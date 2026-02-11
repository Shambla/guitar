#!/usr/bin/env python3
"""
Bulk uploader for Instagram conveyor-belt media.

Scans a local directory, computes SHA256 hashes for supported media, uploads only
new/changed files to a remote site folder, and writes a manifest JSON that a
posting bot can consume later.

Supports:
  - rsync over SSH (preferred): --method rsync
  - SFTP via paramiko:         --method sftp

Requirements:
  - Python 3.11+
  - macOS/Linux shell tools for rsync mode: ssh + rsync
  - paramiko only when using --method sftp

Environment variables (SSH key auth, no interactive password prompts):
  - IGQ_SSH_HOST   (required)
  - IGQ_SSH_USER   (required)
  - IGQ_SSH_PORT   (optional, default: 22)
  - IGQ_SSH_KEY    (optional, path to private key)

Behavior:
  - Recursive scan of local media directory.
  - Supported photos: .jpg .jpeg .png .webp
  - Supported videos: .mp4 .mov
  - Skip files larger than --max-mb.
  - Compare against remote manifest (preferred) to avoid re-uploading unchanged files.
  - If remote manifest does not exist, use lightweight remote existence/size checks.
  - Never deletes remote files.
  - Validates that --base-url starts with https://.

Output files (written in --local-dir unless --dry-run):
  - ig_queue_manifest.json
  - ig_bulk_upload_log.jsonl

How to run:
  rsync:
    python3 bulk_upload_to_site.py \
      --method rsync \
      --local-dir "./next_uploads" \
      --base-url "https://example.com/igq/" \
      --remote-dir "/var/www/html/igq"

  sftp:
    python3 bulk_upload_to_site.py \
      --method sftp \
      --local-dir "./next_uploads" \
      --base-url "https://example.com/igq/" \
      --remote-dir "/var/www/html/igq"

  dry run:
    python3 bulk_upload_to_site.py \
      --method rsync \
      --local-dir "./next_uploads" \
      --base-url "https://example.com/igq/" \
      --remote-dir "/var/www/html/igq" \
      --dry-run
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov"}
SUPPORTED_EXTS = PHOTO_EXTS | VIDEO_EXTS
MANIFEST_FILENAME = "ig_queue_manifest.json"
LOG_FILENAME = "ig_bulk_upload_log.jsonl"


@dataclasses.dataclass
class SSHConfig:
    host: str
    user: str
    port: int = 22
    key_path: Optional[str] = None


@dataclasses.dataclass
class MediaItem:
    local_path: Path
    rel_path: str
    remote_rel_path: str
    file_type: str
    sha256: str
    size_bytes: int
    mtime: dt.datetime


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def to_iso(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).isoformat()


def sanitize_segment(name: str) -> str:
    # Keep filenames URL-safe and stable.
    cleaned = name.replace(" ", "_")
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or "file"


def normalize_base_url(base_url: str) -> str:
    base_url = base_url.strip()
    if not base_url.lower().startswith("https://"):
        raise ValueError("--base-url must start with https://")
    return base_url.rstrip("/") + "/"


def load_ssh_config() -> SSHConfig:
    host = (os.getenv("IGQ_SSH_HOST") or "").strip()
    user = (os.getenv("IGQ_SSH_USER") or "").strip()
    port_str = (os.getenv("IGQ_SSH_PORT") or "22").strip()
    key = (os.getenv("IGQ_SSH_KEY") or "").strip() or None

    if not host:
        raise RuntimeError("Missing env var IGQ_SSH_HOST")
    if not user:
        raise RuntimeError("Missing env var IGQ_SSH_USER")
    try:
        port = int(port_str)
    except ValueError as exc:
        raise RuntimeError(f"Invalid IGQ_SSH_PORT: {port_str}") from exc

    return SSHConfig(host=host, user=user, port=port, key_path=key)


def build_ssh_cmd(cfg: SSHConfig) -> List[str]:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(cfg.port),
    ]
    if cfg.key_path:
        cmd += ["-i", cfg.key_path]
    cmd.append(f"{cfg.user}@{cfg.host}")
    return cmd


def build_rsync_cmd(cfg: SSHConfig) -> List[str]:
    ssh_transport = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(cfg.port),
    ]
    if cfg.key_path:
        ssh_transport += ["-i", cfg.key_path]
    return ["rsync", "-avz", "--checksum", "-e", " ".join(shlex.quote(x) for x in ssh_transport)]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def media_type_for(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in PHOTO_EXTS:
        return "photo"
    if ext in VIDEO_EXTS:
        return "video"
    return None


def iter_media_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.name in {MANIFEST_FILENAME, LOG_FILENAME}:
            continue
        if p.suffix.lower() in SUPPORTED_EXTS:
            yield p


def make_remote_rel_path(
    rel_posix: str,
    sha256: str,
    strategy: str,
    used_paths: set[str],
) -> str:
    parts = rel_posix.split("/")
    dir_parts = [sanitize_segment(p) for p in parts[:-1]]
    stem, ext = os.path.splitext(parts[-1])
    ext = ext.lower()

    if strategy == "hash":
        file_name = f"{sha256[:12]}{ext}"
    else:
        file_name = f"{sanitize_segment(stem)}{ext}"

    base_rel = "/".join([*dir_parts, file_name]) if dir_parts else file_name
    candidate = base_rel
    n = 2
    while candidate in used_paths:
        stem2, ext2 = os.path.splitext(base_rel)
        candidate = f"{stem2}_{n}{ext2}"
        n += 1
    used_paths.add(candidate)
    return candidate


def shell_jsonl_log(path: Path, event: Dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    event = dict(event)
    event["ts"] = iso_now()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def ssh_run(cfg: SSHConfig, remote_command: str) -> subprocess.CompletedProcess[str]:
    cmd = [*build_ssh_cmd(cfg), remote_command]
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def rsync_mkdir_p(cfg: SSHConfig, remote_dir: str) -> None:
    safe_remote = shlex.quote(remote_dir)
    proc = ssh_run(cfg, f"mkdir -p {safe_remote}")
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to create remote dir: {proc.stderr.strip()}")


def rsync_fetch_remote_manifest(cfg: SSHConfig, remote_manifest_path: str) -> Optional[Dict[str, Any]]:
    safe_remote = shlex.quote(remote_manifest_path)
    proc = ssh_run(cfg, f"test -f {safe_remote} && cat {safe_remote}")
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def rsync_remote_size(cfg: SSHConfig, remote_file: str) -> Optional[int]:
    safe = shlex.quote(remote_file)
    # POSIX-friendly fallback via wc -c.
    proc = ssh_run(cfg, f"test -f {safe} && wc -c < {safe} || echo MISSING")
    if proc.returncode != 0:
        return None
    out = (proc.stdout or "").strip()
    if not out or out == "MISSING":
        return None
    try:
        return int(out)
    except ValueError:
        return None


def rsync_upload_file(cfg: SSHConfig, local_path: Path, remote_file: str) -> None:
    cmd = build_rsync_cmd(cfg)
    target = f"{cfg.user}@{cfg.host}:{remote_file}"
    cmd += [str(local_path), target]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "rsync upload failed")


def rsync_upload_text(cfg: SSHConfig, content: str, remote_file: str) -> None:
    safe_remote = shlex.quote(remote_file)
    # Use a single-quoted heredoc delimiter to avoid interpolation.
    remote_cmd = f"cat > {safe_remote} <<'EOF'\n{content}\nEOF"
    proc = ssh_run(cfg, remote_cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to upload text file: {proc.stderr.strip()}")


def sftp_connect(cfg: SSHConfig):
    try:
        import paramiko  # type: ignore
    except Exception as exc:
        raise RuntimeError("paramiko is required for --method sftp. Install with: pip install paramiko") from exc

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs: Dict[str, Any] = {
        "hostname": cfg.host,
        "username": cfg.user,
        "port": cfg.port,
        "look_for_keys": True,
        "allow_agent": True,
        "timeout": 30,
    }
    if cfg.key_path:
        connect_kwargs["key_filename"] = cfg.key_path
    client.connect(**connect_kwargs)
    return client, client.open_sftp()


def sftp_mkdir_p(sftp: Any, remote_dir: str) -> None:
    current = ""
    for part in remote_dir.strip("/").split("/"):
        current = current + "/" + part if current else "/" + part
        try:
            sftp.stat(current)
        except Exception:
            sftp.mkdir(current)


def sftp_fetch_remote_manifest(sftp: Any, remote_manifest_path: str) -> Optional[Dict[str, Any]]:
    try:
        with sftp.open(remote_manifest_path, "r") as f:
            data = f.read()
    except Exception:
        return None
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def sftp_remote_size(sftp: Any, remote_file: str) -> Optional[int]:
    try:
        st = sftp.stat(remote_file)
        return int(st.st_size)
    except Exception:
        return None


def sftp_upload_file(sftp: Any, local_path: Path, remote_file: str) -> None:
    sftp.put(str(local_path), remote_file)


def sftp_upload_text(sftp: Any, content: str, remote_file: str) -> None:
    with sftp.open(remote_file, "w") as f:
        f.write(content)


def index_remote_manifest(remote_manifest: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not remote_manifest:
        return out
    items = remote_manifest.get("items", [])
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        if isinstance(filename, str) and filename:
            out[filename] = item
    return out


def build_manifest(base_url: str, items: List[MediaItem]) -> Dict[str, Any]:
    sorted_items = sorted(items, key=lambda i: i.mtime)
    manifest_items = []
    for i in sorted_items:
        encoded_rel = "/".join(quote(seg) for seg in i.remote_rel_path.split("/"))
        manifest_items.append(
            {
                "local_path": str(i.local_path),
                "filename": i.remote_rel_path,
                "url": base_url + encoded_rel,
                "type": i.file_type,
                "sha256": i.sha256,
                "bytes": i.size_bytes,
                "mtime": i.mtime.isoformat(),
            }
        )
    return {
        "generated_at": iso_now(),
        "base_url": base_url,
        "items": manifest_items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk upload local IG media to website and generate manifest.")
    parser.add_argument("--local-dir", required=True, help="Local folder to scan for media files.")
    parser.add_argument("--base-url", required=True, help="Public HTTPS base URL (e.g. https://example.com/igq/).")
    parser.add_argument("--remote-dir", required=True, help="Remote target directory (e.g. /var/www/html/igq).")
    parser.add_argument("--method", choices=["rsync", "sftp"], default="rsync", help="Upload method.")
    parser.add_argument("--rename", choices=["keep", "hash"], default="keep", help="Filename strategy on remote.")
    parser.add_argument("--max-mb", type=float, default=200.0, help="Max file size in MB (default: 200).")
    parser.add_argument("--dry-run", action="store_true", help="Show what would upload; do not modify local/remote files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    local_dir = Path(args.local_dir).expanduser().resolve()
    if not local_dir.exists() or not local_dir.is_dir():
        print(f"ERROR: --local-dir does not exist or is not a directory: {local_dir}", file=sys.stderr)
        return 2

    try:
        base_url = normalize_base_url(args.base_url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    cfg = load_ssh_config()
    remote_dir = args.remote_dir.rstrip("/")
    remote_manifest_path = posixpath.join(remote_dir, MANIFEST_FILENAME)
    max_bytes = int(args.max_mb * 1024 * 1024)

    manifest_local_path = local_dir / MANIFEST_FILENAME
    log_local_path = local_dir / LOG_FILENAME

    scanned = 0
    uploaded = 0
    would_upload = 0
    skipped = 0
    errors = 0

    # Collect local media and compute hashes.
    media_items: List[MediaItem] = []
    used_remote_paths: set[str] = set()
    for p in iter_media_files(local_dir):
        scanned += 1
        try:
            size = p.stat().st_size
            if size > max_bytes:
                skipped += 1
                shell_jsonl_log(
                    log_local_path,
                    {"event": "skip_size_limit", "path": str(p), "bytes": size, "max_bytes": max_bytes},
                    args.dry_run,
                )
                continue

            file_type = media_type_for(p)
            if not file_type:
                continue

            rel_posix = p.relative_to(local_dir).as_posix()
            digest = sha256_file(p)
            remote_rel = make_remote_rel_path(rel_posix, digest, args.rename, used_remote_paths)
            item = MediaItem(
                local_path=p,
                rel_path=rel_posix,
                remote_rel_path=remote_rel,
                file_type=file_type,
                sha256=digest,
                size_bytes=size,
                mtime=dt.datetime.fromtimestamp(p.stat().st_mtime, tz=dt.timezone.utc),
            )
            media_items.append(item)
        except Exception as exc:
            errors += 1
            shell_jsonl_log(log_local_path, {"event": "scan_error", "path": str(p), "error": str(exc)}, args.dry_run)

    # Open transport and fetch remote manifest.
    remote_manifest: Optional[Dict[str, Any]] = None
    remote_map: Dict[str, Dict[str, Any]] = {}
    sftp_client = None
    ssh_client = None
    sftp = None
    try:
        if args.method == "rsync":
            remote_manifest = rsync_fetch_remote_manifest(cfg, remote_manifest_path)
            remote_map = index_remote_manifest(remote_manifest)
            if not args.dry_run:
                rsync_mkdir_p(cfg, remote_dir)
        else:
            ssh_client, sftp = sftp_connect(cfg)
            remote_manifest = sftp_fetch_remote_manifest(sftp, remote_manifest_path)
            remote_map = index_remote_manifest(remote_manifest)
            if not args.dry_run:
                sftp_mkdir_p(sftp, remote_dir)

        # Upload media if changed.
        for item in media_items:
            remote_file = posixpath.join(remote_dir, item.remote_rel_path)
            remote_info = remote_map.get(item.remote_rel_path)

            should_upload = True
            reason = "new"
            if remote_info and isinstance(remote_info.get("sha256"), str):
                if remote_info["sha256"] == item.sha256:
                    should_upload = False
                    reason = "unchanged_manifest_hash"
                else:
                    reason = "changed_manifest_hash"
            else:
                # No remote hash. Lightweight existence/size check.
                if args.method == "rsync":
                    remote_size = rsync_remote_size(cfg, remote_file)
                else:
                    remote_size = sftp_remote_size(sftp, remote_file)  # type: ignore[arg-type]

                if remote_size is not None and remote_size == item.size_bytes:
                    should_upload = False
                    reason = "unchanged_size_no_manifest"
                elif remote_size is None:
                    reason = "new_no_manifest"
                else:
                    reason = "changed_size_no_manifest"

            if not should_upload:
                skipped += 1
                print(f"SKIP  {item.rel_path} ({reason})")
                shell_jsonl_log(
                    log_local_path,
                    {"event": "skip", "path": item.rel_path, "remote": item.remote_rel_path, "reason": reason},
                    args.dry_run,
                )
                continue

            print(f"UPLOAD {item.rel_path} -> {item.remote_rel_path} ({reason})")
            would_upload += 1
            shell_jsonl_log(
                log_local_path,
                {"event": "upload_candidate", "path": item.rel_path, "remote": item.remote_rel_path, "reason": reason},
                args.dry_run,
            )

            if args.dry_run:
                continue

            try:
                remote_parent = posixpath.dirname(remote_file)
                if args.method == "rsync":
                    rsync_mkdir_p(cfg, remote_parent)
                    rsync_upload_file(cfg, item.local_path, remote_file)
                else:
                    sftp_mkdir_p(sftp, remote_parent)  # type: ignore[arg-type]
                    sftp_upload_file(sftp, item.local_path, remote_file)  # type: ignore[arg-type]
                uploaded += 1
                shell_jsonl_log(
                    log_local_path,
                    {"event": "uploaded", "path": item.rel_path, "remote": item.remote_rel_path, "sha256": item.sha256},
                    args.dry_run,
                )
            except Exception as exc:
                errors += 1
                shell_jsonl_log(
                    log_local_path,
                    {"event": "upload_error", "path": item.rel_path, "remote": item.remote_rel_path, "error": str(exc)},
                    args.dry_run,
                )

        manifest = build_manifest(base_url, media_items)

        if not args.dry_run:
            manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
            manifest_local_path.write_text(manifest_text, encoding="utf-8")

            if args.method == "rsync":
                rsync_upload_text(cfg, manifest_text, remote_manifest_path)
            else:
                sftp_upload_text(sftp, manifest_text, remote_manifest_path)  # type: ignore[arg-type]

            shell_jsonl_log(
                log_local_path,
                {
                    "event": "manifest_written",
                    "local_manifest": str(manifest_local_path),
                    "remote_manifest": remote_manifest_path,
                    "items": len(media_items),
                },
                args.dry_run,
            )

    finally:
        try:
            if sftp:
                sftp.close()
            if ssh_client:
                ssh_client.close()
        except Exception:
            pass

    print("\n=== Bulk Upload Summary ===")
    print(f"Scanned : {scanned}")
    print(f"Uploaded: {uploaded}" if not args.dry_run else f"Would upload: {would_upload}")
    print(f"Skipped : {skipped}")
    print(f"Errors  : {errors}")
    print(f"Dry run : {args.dry_run}")
    print(f"Method  : {args.method}")
    print(f"Manifest: {manifest_local_path} {'(not written in dry-run)' if args.dry_run else ''}")
    print(f"Log     : {log_local_path} {'(not written in dry-run)' if args.dry_run else ''}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
