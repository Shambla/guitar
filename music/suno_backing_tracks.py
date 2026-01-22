#!/usr/bin/env python3
"""
Suno Backing Tracks (WIP)
========================

Goal
----
Prototype a simple, programmatic pipeline to generate backing tracks via Suno (or a Suno-compatible
provider like KIE / PiAPI), then poll for completion and download the resulting audio.

Important
---------
- This file does NOT ship any API keys and does NOT read/write any .env files.
- Configure your key via environment variables (see Configuration below).
- Endpoints differ across providers. This client is intentionally configurable and conservative.

Configuration (environment variables)
------------------------------------
- SUNO_API_KEY:
    Bearer token for your provider (required).

- SUNO_PROVIDER:
    One of: "suno", "kie", "piapi"
    Default: "kie" (because a concrete endpoint pattern was provided in your notes).

- SUNO_API_BASE_URL:
    Provider base URL. Defaults:
      - kie:   https://api.kie.ai
      - piapi: https://api.piapi.ai
      - suno:  https://api.sunoapi.org   (placeholder; replace with the official base URL you receive)

How it works (high level)
-------------------------
1) POST a "generate" request with a text prompt + optional params (instrumental/title/style/model).
2) Receive a task/job id.
3) Poll status until streaming/download URLs are available.
4) Download audio.

CLI examples
------------
Export your key first (in your shell):
  export SUNO_API_KEY="YOUR_KEY_HERE"

Generate an instrumental track:
  python3 suno_backing_tracks.py \\
    --instrumental \\
    --title "Soothing Lydian Backing Track" \\
    --style "soothing guitar backing track, lydian mode, slow, warm, spacious, clean tone" \\
    --prompt "A calming, slow, spacious lydian backing track for guitar practice. No vocals." \\
    --outdir "./outputs"

Notes on API shapes
-------------------
Your notes mention KIE uses:
  POST https://api.kie.ai/api/v1/generate
and then you check task status via a task id / callback.

Suno’s official API may differ. Once you confirm the exact official endpoints/fields, we can tighten the
provider adapter(s).
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SunoAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerateRequest:
    prompt: str
    instrumental: bool = True
    title: Optional[str] = None
    style: Optional[str] = None
    model: Optional[str] = None  # e.g. "V4", "V4_5", "V5" (provider-specific)

    # Optional tuning knobs (provider-specific; safe to omit)
    styleWeight: Optional[float] = None
    weirdnessConstraint: Optional[float] = None

    # If True, indicates you want "custom mode" behavior where style/title matter more.
    custom: bool = True


@dataclass(frozen=True)
class TrackResult:
    # Many providers return two variations; we store whatever we can find.
    audio_id: Optional[str]
    title: Optional[str]
    streaming_url: Optional[str]
    download_url: Optional[str]


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return v.strip()


def _default_base_url(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "kie":
        return "https://api.kie.ai"
    if provider == "piapi":
        return "https://api.piapi.ai"
    # Placeholder: replace with the official Suno base URL you receive.
    return "https://api.sunoapi.org"


def _json_request(
    url: str,
    method: str,
    headers: Dict[str, str],
    body: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = urllib.request.Request(url=url, method=method.upper(), headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
            if not raw:
                return {}
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                # Some providers may return plain text on error.
                raise SunoAPIError(f"Non-JSON response from {url}: {raw[:400]!r}")
    except urllib.error.HTTPError as e:
        payload = ""
        try:
            payload = e.read().decode("utf-8", errors="replace")
        except Exception:
            payload = "<unable to read body>"
        raise SunoAPIError(f"HTTP {e.code} calling {url}: {payload}") from e
    except urllib.error.URLError as e:
        raise SunoAPIError(f"Network error calling {url}: {e}") from e


class SunoClient:
    """
    Provider-agnostic-ish client for Suno-compatible APIs.

    You MUST confirm your provider's docs and adjust endpoints/fields as needed.
    This is a first-pass scaffold to get you unblocked.
    """

    def __init__(
        self,
        api_key: str,
        provider: str = "kie",
        base_url: Optional[str] = None,
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key
        self.provider = (provider or "kie").strip().lower()
        self.base_url = (base_url or _default_base_url(self.provider)).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "brianstreckfus-suno-client/0.1",
        }

    # -------- Provider endpoint helpers --------
    def _generate_url(self) -> str:
        # Based on your notes for KIE.
        if self.provider == "kie":
            return f"{self.base_url}/api/v1/generate"
        # Guessy placeholders; adjust once you confirm docs.
        if self.provider == "piapi":
            return f"{self.base_url}/api/v1/suno/generate"
        return f"{self.base_url}/api/v1/generate"

    def _status_url(self, task_id: str) -> str:
        if self.provider == "kie":
            return f"{self.base_url}/api/v1/task/{task_id}"
        if self.provider == "piapi":
            return f"{self.base_url}/api/v1/task/{task_id}"
        return f"{self.base_url}/api/v1/task/{task_id}"

    # -------- Core flow --------
    def generate(self, req: GenerateRequest) -> str:
        """
        Submit a generation request. Returns provider task/job id.
        """
        payload: Dict[str, Any] = {
            "prompt": req.prompt[:500],  # respect the “prompt up to 500 chars” note
            "instrumental": bool(req.instrumental),
        }

        if req.custom:
            # Not all providers will use these fields; safe to include.
            if req.title:
                payload["title"] = req.title
            if req.style:
                payload["style"] = req.style
        else:
            # “non-custom mode”: prompt-only, provider decides style/lyrics
            payload["custom"] = False

        if req.model:
            payload["model"] = req.model
        if req.styleWeight is not None:
            payload["styleWeight"] = float(req.styleWeight)
        if req.weirdnessConstraint is not None:
            payload["weirdnessConstraint"] = float(req.weirdnessConstraint)

        url = self._generate_url()
        data = _json_request(
            url=url,
            method="POST",
            headers=self._headers(),
            body=payload,
            timeout_seconds=self.timeout_seconds,
        )

        # Common patterns:
        # - {"taskId": "..."}
        # - {"id": "..."}
        # - {"data": {"task_id": "..."}}  etc.
        task_id = (
            data.get("taskId")
            or data.get("task_id")
            or data.get("id")
            or (data.get("data") or {}).get("taskId")
            or (data.get("data") or {}).get("task_id")
            or (data.get("data") or {}).get("id")
        )
        if not task_id:
            raise SunoAPIError(f"Could not find task id in response: {data}")
        return str(task_id)

    def get_status(self, task_id: str) -> Dict[str, Any]:
        url = self._status_url(task_id)
        return _json_request(
            url=url,
            method="GET",
            headers=self._headers(),
            body=None,
            timeout_seconds=self.timeout_seconds,
        )

    def wait_for_results(
        self,
        task_id: str,
        timeout_seconds: int = 240,
        poll_every_seconds: float = 2.0,
    ) -> List[TrackResult]:
        """
        Poll until results are available, then return best-effort track URLs.
        """
        start = time.time()
        last_status: Optional[Dict[str, Any]] = None

        while time.time() - start < timeout_seconds:
            status = self.get_status(task_id)
            last_status = status

            # Provider may include status fields like: "status": "completed"
            state = (
                status.get("status")
                or status.get("state")
                or (status.get("data") or {}).get("status")
                or (status.get("data") or {}).get("state")
            )
            state_lc = str(state or "").lower()
            if state_lc in {"completed", "complete", "success", "succeeded", "done"}:
                return self._extract_tracks(status)
            if state_lc in {"failed", "error", "cancelled", "canceled"}:
                raise SunoAPIError(f"Task failed ({task_id}): {status}")

            # Some providers may return results even without a terminal state.
            tracks = self._extract_tracks(status)
            if any(t.streaming_url or t.download_url for t in tracks):
                return tracks

            time.sleep(poll_every_seconds)

        raise SunoAPIError(
            f"Timed out waiting for results ({timeout_seconds}s). Last status: {last_status}"
        )

    def download(self, url: str, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            url=url,
            method="GET",
            headers={"User-Agent": "brianstreckfus-suno-client/0.1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                with out_path.open("wb") as f:
                    while True:
                        chunk = resp.read(1024 * 256)
                        if not chunk:
                            break
                        f.write(chunk)
        except Exception as e:
            raise SunoAPIError(f"Failed to download {url} -> {out_path}: {e}") from e

    # -------- Parsing helpers --------
    def _extract_tracks(self, status: Dict[str, Any]) -> List[TrackResult]:
        """
        Best-effort extraction across various provider response shapes.
        """
        candidates: List[Dict[str, Any]] = []

        # Common placements
        if isinstance(status.get("songs"), list):
            candidates.extend(status["songs"])
        data = status.get("data")
        if isinstance(data, dict) and isinstance(data.get("songs"), list):
            candidates.extend(data["songs"])
        if isinstance(status.get("results"), list):
            candidates.extend(status["results"])
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            candidates.extend(data["results"])

        # Sometimes a single dict
        if isinstance(status.get("song"), dict):
            candidates.append(status["song"])
        if isinstance(data, dict) and isinstance(data.get("song"), dict):
            candidates.append(data["song"])

        tracks: List[TrackResult] = []
        for c in candidates:
            if not isinstance(c, dict):
                continue
            audio_id = c.get("audioId") or c.get("audio_id") or c.get("id")
            title = c.get("title")
            streaming_url = (
                c.get("streamingUrl")
                or c.get("streaming_url")
                or c.get("streamUrl")
                or c.get("stream_url")
            )
            download_url = (
                c.get("downloadUrl")
                or c.get("download_url")
                or c.get("audioUrl")
                or c.get("audio_url")
                or c.get("url")
            )
            tracks.append(
                TrackResult(
                    audio_id=str(audio_id) if audio_id else None,
                    title=str(title) if title else None,
                    streaming_url=str(streaming_url) if streaming_url else None,
                    download_url=str(download_url) if download_url else None,
                )
            )

        # If nothing parsed, return empty list instead of crashing.
        return tracks


def _pick_best_download(tracks: List[TrackResult]) -> Optional[TrackResult]:
    for t in tracks:
        if t.download_url:
            return t
    for t in tracks:
        if t.streaming_url:
            return t
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate backing tracks via Suno-compatible APIs (WIP).")
    parser.add_argument("--prompt", required=True, help="Natural language prompt describing the music.")
    parser.add_argument("--instrumental", action="store_true", help="Generate instrumental (no vocals).")
    parser.add_argument("--title", default=None, help="Optional title (custom mode).")
    parser.add_argument("--style", default=None, help="Optional style/genre/mood (custom mode).")
    parser.add_argument("--model", default=None, help="Optional model version (e.g., V4, V4_5, V5).")
    parser.add_argument("--outdir", default="outputs", help="Directory to save downloads.")
    parser.add_argument("--timeout", type=int, default=240, help="Max seconds to wait for results.")
    args = parser.parse_args()

    api_key = _env("SUNO_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing SUNO_API_KEY. Set it in your shell, e.g.:\n"
            "  export SUNO_API_KEY=\"YOUR_KEY_HERE\""
        )

    provider = (_env("SUNO_PROVIDER", "kie") or "kie").lower()
    base_url = _env("SUNO_API_BASE_URL", _default_base_url(provider))

    client = SunoClient(
        api_key=api_key,
        provider=provider,
        base_url=base_url,
        timeout_seconds=30,
    )

    req = GenerateRequest(
        prompt=args.prompt,
        instrumental=bool(args.instrumental),
        title=args.title,
        style=args.style,
        model=args.model,
        custom=True,
    )

    print(f"Provider: {client.provider}")
    print(f"Base URL: {client.base_url}")
    print("Submitting generation request...")
    task_id = client.generate(req)
    print(f"Task ID: {task_id}")
    print("Waiting for results...")
    tracks = client.wait_for_results(task_id=task_id, timeout_seconds=args.timeout, poll_every_seconds=2.0)

    if not tracks:
        print("No tracks returned yet. Raw status may require provider-specific parsing.")
        return

    for i, t in enumerate(tracks, start=1):
        print(f"\nResult {i}:")
        print(f"  audio_id:      {t.audio_id}")
        print(f"  title:         {t.title}")
        print(f"  streaming_url: {t.streaming_url}")
        print(f"  download_url:  {t.download_url}")

    best = _pick_best_download(tracks)
    if not best:
        print("\nNo downloadable/streamable URL found to download.")
        return

    outdir = Path(args.outdir)
    outname = (best.title or f"suno_{task_id}").strip().replace("/", "_")
    # Many providers return MP3; we keep .mp3 by default.
    out_path = outdir / f"{outname}.mp3"

    print(f"\nDownloading -> {out_path}")
    client.download(best.download_url or best.streaming_url, out_path)
    print("Done.")


if __name__ == "__main__":
    main()


