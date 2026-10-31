#!/usr/bin/env python3
"""
Prepare Suno Backing Tracks for Stripe / mp3-downloads catalog.

- Slugify to kebab-case (matches existing fulldownloads + *-30s.mp3 previews).
- Copy or convert masters into audio/fulldownloads/{slug}.mp3
- Generate 30-second preview clips (same as DIRECT_AUDIO_SALES.md).
- Optionally rename sources under Suno Backing Tracks/ to the slug filename.
- Writes suno-stripe-prep-manifest.json for bulk Stripe / JSON work.

Does not edit mp3-downloads-data.json or create Payment Links.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SUNO_ROOT = SCRIPT_DIR / "fulldownloads" / "Suno Backing Tracks"
FULL_DIR = SCRIPT_DIR / "fulldownloads"
PREVIEW_DIR = SCRIPT_DIR / "previews"
MANIFEST_PATH = SCRIPT_DIR / "suno-stripe-prep-manifest.json"
CATALOG_PATH = SCRIPT_DIR.parent / "mp3-downloads-data.json"

MIN_DURATION_SEC = 120.0
PREVIEW_SECONDS = 30
AUDIO_EXT = {".mp3", ".wav", ".m4a"}

SKIP_DIR_NAMES = {
    ".logicx",
    "Stems",
    "MASTERS",
    "Obsolete",
    "Project File Backups",
    "Undo Data.nosync",
    "Alternatives",
    "Media",
    "Resources",
    "Audio Files",
}

COLLECTION_BY_FOLDER = {
    ".": "suno",
    "Rap May 2026": "rap",
    "Reggae": "reggae",
    "Bossa": "bossa",
    "Calpyso": "calypso",
    "Indian Traditional": "indian-traditional",
    "Irish": "irish",
    "Metal": "metal",
    "C# harmonic Synth": "synth",
    "Ambient": "ambient",
    "Funk Disco": "funk-disco",
    "EDM Metal": "edm-metal",
    "Egyptian": "egypt",
    "F Lydian Backing Track": "lydian",
    "Shoegaze Reggae June 2026 Backing tracks": "shoegaze-reggae",
    "60s Rock - Painted Sky": "60s-rock",
    "Country": "country",
    "Asian": "asian",
    "Lo-Fi": "lo-fi",
    "Chill Indian": "chill-indian",
}


@dataclass
class TrackRow:
    id: str
    title: str
    collection: str
    source_path: str
    full_audio: str
    preview_audio: str
    duration_sec: float
    action: str
    skip_reason: str = ""


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def ffprobe_duration(path: Path) -> float | None:
    proc = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def note_sharp_flat(text: str) -> str:
    """Turn C#, F# into c-sharp; leave Eb/Ab as eb/ab (site convention)."""
    out = text
    for note in "abcdefgABCDEFG":
        out = out.replace(f"{note}#", f"{note.lower()}-sharp")
    return out


def slugify(name: str) -> str:
    stem = Path(name).stem
    s = note_sharp_flat(stem)
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"[\|_/]+", " ", s)
    s = re.sub(r"[^\w\s-]+", " ", s, flags=re.UNICODE)
    s = s.lower()
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def should_skip_file(path: Path, rel: Path) -> str | None:
    sp = str(rel)
    if any(part in SKIP_DIR_NAMES for part in rel.parts):
        return "inside project/stems folder"
    if " Stems" in sp or sp.endswith(" Stems"):
        return "stem export folder"
    parent = path.parent.name
    if re.match(r"^\d+\s", path.name) and "Stem" in parent:
        return "numbered stem file"
    low = path.name.lower()
    if "english lyrics" in low or "english vocals" in low:
        return "vocal/lyrics variant (backing-track catalog is instrumental)"
    if "_converted" in low or "master 5.0" in low:
        return "duplicate DAW export / master variant"
    if path.name.startswith("Gritty Rap") or path.name.startswith("Off Kilter"):
        return "already published under rap collection"
    return None


def catalog_basenames() -> set[str]:
    if not CATALOG_PATH.is_file():
        return set()
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    out: set[str] = set()
    for row in data:
        ds = row.get("direct_sale") or {}
        full = ds.get("full_audio") or ""
        if full:
            out.add(Path(full).name)
        tid = row.get("id")
        if tid:
            out.add(f"{tid}.mp3")
    return out


def discover_files() -> list[tuple[Path, Path]]:
    found: list[tuple[Path, Path]] = []
    if not SUNO_ROOT.is_dir():
        return found
    for path in sorted(SUNO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in AUDIO_EXT:
            continue
        rel = path.relative_to(SUNO_ROOT)
        if should_skip_file(path, rel):
            continue
        found.append((path, rel))
    return found


def collection_for(rel: Path) -> str:
    if rel.parent == Path("."):
        return COLLECTION_BY_FOLDER["."]
    key = rel.parts[0] if rel.parts else "."
    return COLLECTION_BY_FOLDER.get(key, slugify(key))


def human_title(stem: str) -> str:
    t = stem.replace("_", " ").replace("|", " / ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def ensure_unique_slug(base: str, used: set[str]) -> str:
    slug = base
    n = 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def copy_or_convert(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".mp3":
        if dest.resolve() != src.resolve():
            shutil.copy2(src, dest)
        return
    proc = run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(dest),
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg convert failed: {proc.stderr[-500:]}")


def make_preview(full: Path, preview: Path) -> None:
    preview.parent.mkdir(parents=True, exist_ok=True)
    if preview.is_file() and preview.stat().st_mtime >= full.stat().st_mtime:
        return
    proc = run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(full),
            "-t",
            str(PREVIEW_SECONDS),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(preview),
        ]
    )
    if proc.returncode != 0:
        # MP3 may lack edit list for stream copy; re-encode trim always works.
        proc = run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(full),
                "-t",
                str(PREVIEW_SECONDS),
                "-c",
                "copy",
                str(preview),
            ]
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg preview failed: {proc.stderr[-500:]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print plan only")
    parser.add_argument(
        "--rename-sources",
        action="store_true",
        default=True,
        help="Rename files under Suno Backing Tracks/ to {slug}.mp3 (default: on)",
    )
    parser.add_argument(
        "--no-rename-sources",
        action="store_false",
        dest="rename_sources",
        help="Leave original Suno filenames in place",
    )
    parser.add_argument(
        "--skip-existing-full",
        action="store_true",
        default=True,
        help="Skip copy when fulldownloads/{slug}.mp3 already exists",
    )
    args = parser.parse_args()

    if not SUNO_ROOT.is_dir():
        print(f"Missing Suno folder: {SUNO_ROOT}", file=sys.stderr)
        return 1

    existing_catalog = catalog_basenames()
    used_slugs: set[str] = set()
    rows: list[TrackRow] = []
    stats = {"processed": 0, "skipped": 0, "previews": 0, "copies": 0}

    for src, rel in discover_files():
        skip = should_skip_file(src, rel)
        if skip:
            stats["skipped"] += 1
            continue

        base_slug = slugify(src.name)
        if not base_slug:
            stats["skipped"] += 1
            continue

        slug = ensure_unique_slug(base_slug, used_slugs)
        full_name = f"{slug}.mp3"
        full_dest = FULL_DIR / full_name
        preview_dest = PREVIEW_DIR / f"{slug}-{PREVIEW_SECONDS}s.mp3"

        if full_name in existing_catalog and full_dest.is_file():
            stats["skipped"] += 1
            rows.append(
                TrackRow(
                    id=slug,
                    title=human_title(src.stem),
                    collection=collection_for(rel),
                    source_path=str(rel),
                    full_audio=f"audio/fulldownloads/{full_name}",
                    preview_audio=f"audio/previews/{preview_dest.name}",
                    duration_sec=ffprobe_duration(src) or 0,
                    action="skipped",
                    skip_reason="already in mp3-downloads catalog",
                )
            )
            continue

        dur = ffprobe_duration(src)
        if dur is None:
            stats["skipped"] += 1
            rows.append(
                TrackRow(
                    id=slug,
                    title=human_title(src.stem),
                    collection=collection_for(rel),
                    source_path=str(rel),
                    full_audio=f"audio/fulldownloads/{full_name}",
                    preview_audio=f"audio/previews/{preview_dest.name}",
                    duration_sec=0,
                    action="skipped",
                    skip_reason="could not read duration",
                )
            )
            continue
        if dur < MIN_DURATION_SEC:
            stats["skipped"] += 1
            rows.append(
                TrackRow(
                    id=slug,
                    title=human_title(src.stem),
                    collection=collection_for(rel),
                    source_path=str(rel),
                    full_audio=f"audio/fulldownloads/{full_name}",
                    preview_audio=f"audio/previews/{preview_dest.name}",
                    duration_sec=dur,
                    action="skipped",
                    skip_reason=f"under {MIN_DURATION_SEC:.0f}s minimum",
                )
            )
            continue

        action = "planned"
        if not args.dry_run:
            if not (args.skip_existing_full and full_dest.is_file()):
                copy_or_convert(src, full_dest)
                stats["copies"] += 1
            make_preview(full_dest, preview_dest)
            stats["previews"] += 1
            if args.rename_sources and src.suffix.lower() == ".mp3":
                renamed = src.with_name(f"{slug}.mp3")
                if renamed != src and not renamed.exists():
                    src.rename(renamed)
            action = "processed"
            stats["processed"] += 1

        rows.append(
            TrackRow(
                id=slug,
                title=human_title(src.stem),
                collection=collection_for(rel),
                source_path=str(rel),
                full_audio=f"audio/fulldownloads/{full_name}",
                preview_audio=f"audio/previews/{preview_dest.name}",
                duration_sec=round(dur, 2),
                action=action,
            )
        )

    manifest = {
        "suno_root": str(SUNO_ROOT.relative_to(SCRIPT_DIR.parent)),
        "preview_seconds": PREVIEW_SECONDS,
        "min_duration_seconds": MIN_DURATION_SEC,
        "stats": stats,
        "tracks": [asdict(r) for r in rows],
    }
    if not args.dry_run:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(stats, indent=2))
    print(f"Manifest rows: {len(rows)} ({MANIFEST_PATH.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
