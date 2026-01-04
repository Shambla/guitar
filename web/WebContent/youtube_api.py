"""
YouTube API Manager
Efficiently manage YouTube video descriptions, tags, thumbnails, playlists, and chapters.

------------------------------------------------------------------------------
READ THIS FIRST (Secrets / Keys / OAuth)
------------------------------------------------------------------------------
This script intentionally does NOT hardcode any YouTube/Google secrets inside
the Python file. Instead, it reads OAuth credentials from local JSON files:

  - client_secrets.json   (OAuth "client id" + "client secret")
  - youtube_token.json    (your user token + usually a refresh token)

What you need to do (one-time setup):
  1) In Google Cloud Console, enable "YouTube Data API v3".
  2) Create OAuth credentials (type: Desktop app).
  3) Download the OAuth client secrets JSON.
  4) Put it next to this script as "client_secrets.json" (or update the path).
  5) Run the script once; your browser opens; approve access.
  6) The script writes "youtube_token.json" for future runs.

Security notes:
  - DO NOT commit or share: client_secrets.json, youtube_token.json
  - If you ever accidentally share them, rotate/revoke credentials immediately.

Optional (recommended) path override via environment variables:
  - YT_CLIENT_SECRETS_FILE: path to the OAuth client secrets JSON
  - YT_TOKEN_FILE:         path to the saved user token JSON

Example usage (commented out):
    # export YT_CLIENT_SECRETS_FILE="/absolute/path/to/client_secrets.json"
    # export YT_TOKEN_FILE="/absolute/path/to/youtube_token.json"
------------------------------------------------------------------------------

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Setup:
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable YouTube Data API v3
    4. Create OAuth 2.0 credentials (Desktop app)
    5. Download credentials JSON file
    6. Set CLIENT_SECRETS_FILE path below

    cd /Users/olivia2/Documents/GitHub/guitar/web/WebContent
    source venv_youtube/bin/activate
    python3 youtube_api.py

    1. TODO Comments that shill our websites. Ended at 130 latest videos --limit 130
    2. Tags that are at the bottom of descriptions IMPORTANT
    3. 162 long form videos, 32 shorts, 4 live streams. 12/31/25

🎸 Beginner Friendly Music PDFs 📄 (Detailed TABS • Songs • Exercises • Scales • Chords • Music Theory)

👉 https://www.sheetmusicdirect.com/en-US/Search.aspx?query=Brian%2BStreckfus

🎶 Free Online Trial Music Instruction
👉 https://belairmusicstudios.com/faculty/brian-streckfus/

🌐 Complete Tour of My Work (Music, Teaching, Tech, Shows & Bookings, Trading)
👉 www.brianstreckfus.com

🔗 All Social Media Links
👉 https://allmylinks.com/brianstreckfus
"""

import os
import json
import hashlib
from datetime import datetime
import importlib.metadata as importlib_metadata
from typing import List, Dict, Optional, Tuple

# -----------------------------------------------------------------------------
# Compatibility patch (keeps venv_youtube on Python 3.9 quieter/working)
# google.api_core may try to call importlib.metadata.packages_distributions()
# which is not present in Python 3.9's importlib.metadata; it prints a warning.
# We provide a safe stub so imports stay clean and behavior remains correct.
# -----------------------------------------------------------------------------
if not hasattr(importlib_metadata, "packages_distributions"):
    def _packages_distributions_stub():
        return {}
    importlib_metadata.packages_distributions = _packages_distributions_stub  # type: ignore[attr-defined]

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# =============================================================================
# CONFIGURATION
# =============================================================================

# Path to your OAuth 2.0 client secrets JSON file
CLIENT_SECRETS_FILE = os.getenv("YT_CLIENT_SECRETS_FILE", "client_secrets.json")
# What is this file?
# - It's the JSON you download from Google Cloud Console when you create OAuth
#   credentials (Desktop app). It contains your client_id and client_secret.
# - DO NOT share it. DO NOT commit it.
#
# If you want to hardcode an absolute path instead (not recommended), you could:
# CLIENT_SECRETS_FILE = "/absolute/path/to/client_secrets.json"

# OAuth 2.0 scopes required for YouTube API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.upload'
]

# Token file to store credentials
TOKEN_FILE = os.getenv("YT_TOKEN_FILE", "youtube_token.json")
# What is this file?
# - It's created by THIS script after you complete the browser OAuth flow.
# - It usually includes an access token and refresh token for your account.
# - Treat it like a password: DO NOT share it. DO NOT commit it.
#
# If you want to hardcode an absolute path instead (not recommended), you could:
# TOKEN_FILE = "/absolute/path/to/youtube_token.json"

# =============================================================================
# CHANGE CATALOG / AUDIT LOGGING
# =============================================================================
# Why:
# - Avoid repeating the same update (saves strict quota)
# - Create a human-reviewable audit trail to double-check mistakes
#
# Format: JSON Lines (one JSON object per line) so it’s append-only and resilient.
CHANGE_LOG_FILE = "youtube_change_log.jsonl"
ENABLE_CHANGE_LOG = True

# =============================================================================
# COMMENT POSTING (TOP-LEVEL)
# =============================================================================
# NOTE (important limitation):
# The YouTube Data API v3 does NOT provide an endpoint to "pin" a comment.
# We can POST a top-level comment across your videos, but pinning must be done
# manually in YouTube Studio (or via unsupported automation).
ENABLE_BULK_COMMENT_POSTING = False
DEFAULT_BULK_COMMENT_TEXT = "Thanks for watching! If you'd like tabs/sheet music or backing tracks, check the description."

def _json_dumps_safe(obj) -> str:
    """JSON dump helper that won't crash on non-serializable objects."""
    def _default(o):
        try:
            return str(o)
        except Exception:
            return "<unserializable>"
    return json.dumps(obj, ensure_ascii=False, default=_default)

def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def _fingerprint(payload: dict) -> str:
    """
    Stable fingerprint for "this exact change".
    If you run the script again and attempt the identical change, we can skip it.
    """
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _append_change_log(event: dict) -> None:
    if not ENABLE_CHANGE_LOG:
        return
    try:
        event = dict(event)
        event.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
        with open(CHANGE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(_json_dumps_safe(event) + "\n")
    except Exception:
        # Never interrupt the main workflow because logging failed.
        pass

def _load_applied_fingerprints() -> set[tuple[str, str, str]]:
    """
    Returns a set of (video_id, action, fingerprint) for successful changes.
    Used to make updates idempotent across runs without extra API calls.
    """
    applied: set[tuple[str, str, str]] = set()
    if not ENABLE_CHANGE_LOG:
        return applied
    if not os.path.exists(CHANGE_LOG_FILE):
        return applied
    try:
        with open(CHANGE_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                if evt.get("ok") is True:
                    vid = evt.get("video_id")
                    action = evt.get("action")
                    fp = evt.get("fingerprint")
                    if isinstance(vid, str) and isinstance(action, str) and isinstance(fp, str):
                        applied.add((vid, action, fp))
    except Exception:
        pass
    return applied

def _load_successful_video_ids(action_filter: str) -> set[str]:
    """
    Returns video IDs that have succeeded at least once for the given action
    according to the local change log. This lets us re-run safely without
    burning quota on already-successful videos.
    """
    ok_ids: set[str] = set()
    if not ENABLE_CHANGE_LOG:
        return ok_ids
    if not os.path.exists(CHANGE_LOG_FILE):
        return ok_ids
    try:
        with open(CHANGE_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                if evt.get("ok") is True and evt.get("action") == action_filter:
                    vid = evt.get("video_id")
                    if isinstance(vid, str) and vid:
                        ok_ids.add(vid)
    except Exception:
        pass
    return ok_ids


def _published_at_sort_key(v: dict) -> str:
    # YouTube publishedAt is ISO8601; lexicographic sort works.
    return str(v.get("publishedAt") or "")


def post_top_level_comment(service, video_id: str, text: str) -> bool:
    """
    Post a TOP-LEVEL comment on a video.
    Catalogs results to youtube_change_log.jsonl.

    IMPORTANT: Pinning is not supported by the YouTube Data API.
    """
    action = "post_comment"
    applied = _load_applied_fingerprints()

    payload_fp = _fingerprint({
        "video_id": video_id,
        "action": action,
        "text_sha256": _sha256_text(text),
    })

    if (video_id, action, payload_fp) in applied:
        _append_change_log({
            "ok": True,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "skipped": True,
            "reason": "Already applied in previous run (fingerprint match)",
        })
        print(f"↩︎ Skipping comment (already posted per log): {video_id}")
        return True

    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text
                    }
                }
            }
        }
        request = service.commentThreads().insert(part="snippet", body=body)
        resp = request.execute()

        comment_id = None
        try:
            comment_id = resp["snippet"]["topLevelComment"]["id"]
        except Exception:
            comment_id = None

        _append_change_log({
            "ok": True,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "comment_id": comment_id,
            "text_sha256": _sha256_text(text),
            "text_len": len(text or ""),
            "quota_cost_estimate": 50,
        })
        print(f"✓ Posted top-level comment: video_id={video_id} comment_id={comment_id}")
        return True

    except HttpError as e:
        _append_change_log({
            "ok": False,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "error": str(e),
        })
        print(f"✗ Error posting comment for {video_id}: {e}")
        return False


def run_bulk_comment_plan_from_backup(backup_file: str,
                                      comment_text: str,
                                      oldest_first: bool = True,
                                      limit: Optional[int] = None) -> str:
    """
    Create a local plan file listing which videos would receive a comment.
    This makes NO API calls and does NOT require authentication.
    """
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    with open(backup_file, "r", encoding="utf-8") as f:
        backup = json.load(f)

    videos = list(backup.get("videos", []))
    videos.sort(key=_published_at_sort_key, reverse=not oldest_first)
    if isinstance(limit, int) and limit > 0:
        videos = videos[:limit]

    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "backup_file": backup_file,
        "oldest_first": bool(oldest_first),
        "limit": int(limit) if isinstance(limit, int) and limit > 0 else None,
        "comment_text": comment_text,
        "comment_text_sha256": _sha256_text(comment_text),
        "total_videos": len(videos),
        "videos": [],
    }

    for v in videos:
        plan["videos"].append({
            "id": v.get("id"),
            "title": v.get("title", ""),
            "publishedAt": v.get("publishedAt"),
        })

    plan_file = f"youtube_comment_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"✓ Wrote comment plan: {plan_file}")
    print("  Review this before running live updates (it makes no API calls).")
    return plan_file


def apply_bulk_comment_plan(service,
                            plan_file: str,
                            dry_run: bool = True,
                            batch_size: int = 20,
                            delay_seconds: float = 2.0,
                            skip_already_successful: bool = True) -> Dict[str, bool]:
    """
    Apply a previously generated comment plan file.
    Posts TOP-LEVEL comments (pinning not supported by API).
    """
    if not os.path.exists(plan_file):
        raise FileNotFoundError(f"Plan file not found: {plan_file}")
    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    comment_text = plan.get("comment_text") or ""
    videos = plan.get("videos", [])
    results: Dict[str, bool] = {}
    total = len(videos)

    print(f"\nApplying comment plan: {plan_file}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
    print(f"Total videos in plan: {total}")
    print(f"Batch size: {batch_size} | Delay: {delay_seconds}s\n")
    if skip_already_successful:
        print("Skip already-successful videos: ON (uses youtube_change_log.jsonl)\n")

    if not dry_run:
        if service is None:
            raise ValueError("service is required when dry_run=False")
        print("Checking API quota status...")
        quota_status = check_quota_status(service)
        print(f"  {quota_status['message']}")
        if not quota_status['has_quota']:
            print("\n⚠️  Cannot proceed - quota exhausted. Please wait for daily reset.")
            return {}
        print()

    ok_ids = _load_successful_video_ids("post_comment") if skip_already_successful else set()

    import time
    for i, v in enumerate(videos, 1):
        video_id = str(v.get("id") or "")
        title = v.get("title", "")
        print(f"[{i}/{total}] {title[:50]}...")

        if not video_id:
            results[video_id] = False
            print("   ✗ Missing video_id in plan\n")
            continue

        if skip_already_successful and video_id in ok_ids:
            results[video_id] = True
            print("   ↩︎ Skipping (comment already posted successfully in a previous run)\n")
            continue

        if dry_run:
            results[video_id] = True
            print("   [DRY RUN - would post top-level comment]\n")
        else:
            ok = post_top_level_comment(service, video_id, comment_text)
            results[video_id] = bool(ok)
            print()

        if not dry_run and i % batch_size == 0 and i < total:
            print(f"⏸️  Pausing {delay_seconds}s before next batch...\n")
            time.sleep(delay_seconds)

    return results

def summarize_change_log(action_filter: str = "update_tags",
                         output_file: Optional[str] = None,
                         log_file: str = CHANGE_LOG_FILE) -> str:
    """
    Create a human-readable summary of what the script changed, based on the JSONL catalog.
    This makes NO API calls.
    """
    if output_file is None:
        output_file = f"youtube_change_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    total = 0
    ok = 0
    skipped = 0
    failed = 0
    rows = []

    if not os.path.exists(log_file):
        content = f"# YouTube Change Summary\n\nNo log file found: `{log_file}`\n"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        return output_file

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            action = evt.get("action")
            if action_filter and action != action_filter:
                continue
            total += 1
            is_ok = evt.get("ok") is True
            is_skipped = evt.get("skipped") is True
            if is_ok:
                ok += 1
            else:
                failed += 1
            if is_skipped:
                skipped += 1
            rows.append({
                "ts": evt.get("ts", ""),
                "video_id": evt.get("video_id", ""),
                "title": evt.get("title", ""),
                "ok": is_ok,
                "skipped": is_skipped,
                "before_tags_count": evt.get("before_tags_count"),
                "after_tags_count": evt.get("after_tags_count"),
                "error": evt.get("error", ""),
            })

    lines = []
    lines.append("# YouTube Change Summary")
    lines.append("")
    lines.append(f"- Log file: `{log_file}`")
    lines.append(f"- Action filter: `{action_filter}`")
    lines.append(f"- Events: {total} (ok={ok}, failed={failed}, skipped={skipped})")
    lines.append("")
    lines.append("| ts | video_id | ok | skipped | before_tags | after_tags | title | error |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|")
    for r in rows[-300:]:
        lines.append(
            f"| {r['ts']} | {r['video_id']} | {str(r['ok']).lower()} | {str(r['skipped']).lower()} | "
            f"{r.get('before_tags_count','')} | {r.get('after_tags_count','')} | "
            f"{str(r.get('title','')).replace('|',' ')} | {str(r.get('error','')).replace('|',' ')} |"
        )
    lines.append("")
    lines.append("_Note: This report is generated locally from the change log; it uses no YouTube API quota._")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✓ Wrote change summary: {output_file}")
    return output_file

# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_authenticated_service():
    """Authenticate and return YouTube API service object."""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        # Secrets are injected here via the local token JSON (NOT hardcoded).
        #
        # Example (commented out): if you stored your token elsewhere:
        # token_path = "/absolute/path/to/youtube_token.json"
        # creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"Client secrets file not found: {CLIENT_SECRETS_FILE}\n"
                    "Please download OAuth 2.0 credentials from Google Cloud Console."
                )
            # Secrets are injected here via the OAuth client secrets JSON
            # (NOT hardcoded). This file is the one you download from Google.
            #
            # Example (commented out): if you stored your client secrets elsewhere:
            # client_secrets_path = "/absolute/path/to/client_secrets.json"
            # flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as token:
            # This writes youtube_token.json locally (contains tokens). Don't share it.
            token.write(creds.to_json())
    
    return build('youtube', 'v3', credentials=creds)


# =============================================================================
# CHANNEL & VIDEO INFORMATION
# =============================================================================

def get_channel_id(service) -> str:
    """Get the authenticated user's channel ID."""
    try:
        request = service.channels().list(part='id', mine=True)
        response = request.execute()
        if response['items']:
            return response['items'][0]['id']
        raise Exception("No channel found for authenticated user")
    except HttpError as e:
        raise Exception(f"Error getting channel ID: {e}")


def get_all_videos(service, channel_id: Optional[str] = None) -> List[Dict]:
    """
    Get all videos from channel.
    
    Returns:
        List of video dictionaries with id, title, description, etc.
    """
    if not channel_id:
        channel_id = get_channel_id(service)
    
    videos = []
    next_page_token = None
    
    try:
        while True:
            # Get uploads playlist ID
            request = service.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                break
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            request = service.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            video_ids = [item['contentDetails']['videoId'] for item in response['items']]
            
            # Get detailed video information (include contentDetails and statistics for comprehensive backup)
            if video_ids:
                video_request = service.videos().list(
                    part='snippet,status,contentDetails,statistics',
                    id=','.join(video_ids)
                )
                video_response = video_request.execute()
                videos.extend(video_response['items'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return videos
    
    except HttpError as e:
        raise Exception(f"Error getting videos: {e}")


def get_video_info(service, video_id: str) -> Dict:
    """Get detailed information for a single video."""
    try:
        request = service.videos().list(
            part='snippet,status,contentDetails',
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]
        return None
    except HttpError as e:
        raise Exception(f"Error getting video info: {e}")


# =============================================================================
# PRIMARY: DESCRIPTION MANAGEMENT
# =============================================================================

def update_video_description(service, video_id: str, new_description: str, 
                            append: bool = False, prepend: bool = False) -> bool:
    """
    Update video description.
    
    Args:
        service: YouTube API service object
        video_id: YouTube video ID
        new_description: New description text
        append: If True, append to existing description
        prepend: If True, prepend to existing description
    
    Returns:
        True if successful, False otherwise
    """
    try:
        applied = _load_applied_fingerprints()
        action = "update_description"

        # Get current video data
        video = get_video_info(service, video_id)
        if not video:
            _append_change_log({
                "ok": False,
                "action": action,
                "video_id": video_id,
                "error": "Video not found",
            })
            print(f"Video {video_id} not found")
            return False
        
        snippet = video['snippet']
        before_desc = snippet.get('description', '') or ""
        
        # Handle append/prepend
        if append:
            current_desc = snippet.get('description', '')
            new_description = current_desc + '\n\n' + new_description
        elif prepend:
            current_desc = snippet.get('description', '')
            new_description = new_description + '\n\n' + current_desc

        # Idempotency (avoid re-applying exact same change)
        payload_fp = _fingerprint({
            "video_id": video_id,
            "action": action,
            "append": bool(append),
            "prepend": bool(prepend),
            "after_desc_sha256": _sha256_text(new_description),
        })
        if (video_id, action, payload_fp) in applied:
            _append_change_log({
                "ok": True,
                "action": action,
                "video_id": video_id,
                "fingerprint": payload_fp,
                "skipped": True,
                "reason": "Already applied in previous run (fingerprint match)",
                "before_desc_sha256": _sha256_text(before_desc),
                "after_desc_sha256": _sha256_text(new_description),
                "before_desc_len": len(before_desc),
                "after_desc_len": len(new_description),
            })
            print(f"↩︎ Skipping description update (already applied): {snippet.get('title', video_id)}")
            return True
        
        # Update description
        snippet['description'] = new_description
        
        # Update video
        request = service.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        )
        request.execute()
        
        _append_change_log({
            "ok": True,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "append": bool(append),
            "prepend": bool(prepend),
            "title": snippet.get("title", ""),
            "before_desc_sha256": _sha256_text(before_desc),
            "after_desc_sha256": _sha256_text(new_description),
            "before_desc_len": len(before_desc),
            "after_desc_len": len(new_description),
            "quota_cost_estimate": 50,
        })
        print(f"✓ Updated description for video: {snippet.get('title', video_id)}")
        return True
    
    except HttpError as e:
        _append_change_log({
            "ok": False,
            "action": "update_description",
            "video_id": video_id,
            "error": str(e),
        })
        print(f"✗ Error updating description for {video_id}: {e}")
        return False


def batch_update_descriptions(service, video_ids: List[str], 
                             new_description: str, append: bool = False, 
                             prepend: bool = False) -> Dict[str, bool]:
    """
    Batch update descriptions for multiple videos.
    
    Returns:
        Dictionary mapping video_id to success status
    """
    results = {}
    total = len(video_ids)
    
    print(f"\nUpdating descriptions for {total} videos...")
    
    for i, video_id in enumerate(video_ids, 1):
        print(f"[{i}/{total}] Processing video {video_id}...")
        results[video_id] = update_video_description(
            service, video_id, new_description, append, prepend
        )
    
    successful = sum(1 for v in results.values() if v)
    print(f"\n✓ Successfully updated {successful}/{total} videos")
    
    return results


def update_all_videos_description(service, new_description: str, 
                                 append: bool = False, prepend: bool = False,
                                 filter_func: Optional[callable] = None) -> Dict[str, bool]:
    """
    Update description for all videos in channel.
    
    Args:
        service: YouTube API service object
        new_description: New description text
        append: If True, append to existing description
        prepend: If True, prepend to existing description
        filter_func: Optional function to filter videos (takes video dict, returns bool)
    
    Returns:
        Dictionary mapping video_id to success status
    """
    print("Fetching all videos from channel...")
    videos = get_all_videos(service)
    
    if filter_func:
        videos = [v for v in videos if filter_func(v)]
    
    video_ids = [v['id'] for v in videos]
    
    print(f"Found {len(video_ids)} videos to update")
    
    return batch_update_descriptions(service, video_ids, new_description, append, prepend)


# =============================================================================
# SECONDARY: TAGS MANAGEMENT
# =============================================================================

def update_video_tags(service, video_id: str, tags: List[str], 
                     replace: bool = True) -> bool:
    """
    Update video tags.
    
    Args:
        service: YouTube API service object
        video_id: YouTube video ID
        tags: List of tag strings
        replace: If True, replace existing tags; if False, merge with existing
    
    Returns:
        True if successful, False otherwise
    """
    try:
        applied = _load_applied_fingerprints()
        action = "update_tags"

        video = get_video_info(service, video_id)
        if not video:
            _append_change_log({
                "ok": False,
                "action": action,
                "video_id": video_id,
                "error": "Video not found",
            })
            return False
        
        snippet = video['snippet']
        before_tags = snippet.get('tags', []) or []
        
        if not replace:
            existing_tags = snippet.get('tags', [])
            tags = list(set(existing_tags + tags))  # Merge and remove duplicates
        
        snippet['tags'] = tags
        
        payload_fp = _fingerprint({
            "video_id": video_id,
            "action": action,
            "replace": bool(replace),
            "tags_sorted": sorted([str(t).strip().lower() for t in (tags or [])]),
        })
        if (video_id, action, payload_fp) in applied:
            _append_change_log({
                "ok": True,
                "action": action,
                "video_id": video_id,
                "fingerprint": payload_fp,
                "skipped": True,
                "reason": "Already applied in previous run (fingerprint match)",
                "title": snippet.get("title", ""),
                "before_tags_count": len(before_tags),
                "after_tags_count": len(tags or []),
                "replace": bool(replace),
            })
            print(f"↩︎ Skipping tag update (already applied): {snippet.get('title', video_id)}")
            return True
        
        def _attempt_update(tag_list: List[str]) -> None:
            snippet['tags'] = tag_list
        request = service.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        )
        request.execute()
        
        try:
            _attempt_update(tags)
        except HttpError as e:
            # One-time fallback for invalidTags: shrink to a safer subset (saves you manual babysitting)
            if 'invalidTags' in str(e) or 'invalid video keywords' in str(e):
                safe_tags = generate_seo_tags(snippet.get('title', ''), snippet.get('description', ''), current_tags=before_tags)
                _append_change_log({
                    "ok": False,
                    "action": action,
                    "video_id": video_id,
                    "fingerprint": payload_fp,
                    "retry": True,
                    "reason": "invalidTags from YouTube; retrying with safer smaller tag set",
                    "first_attempt_tags_count": len(tags or []),
                    "retry_tags_count": len(safe_tags or []),
                    "error": str(e),
                })
                _attempt_update(safe_tags)
                tags = safe_tags  # for logging counts below
            else:
                raise
        
        _append_change_log({
            "ok": True,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "title": snippet.get("title", ""),
            "before_tags_count": len(before_tags),
            "after_tags_count": len(tags or []),
            "replace": bool(replace),
            "quota_cost_estimate": 50,
        })
        print(f"✓ Updated tags for video: {snippet.get('title', video_id)}")
        return True
    
    except HttpError as e:
        _append_change_log({
            "ok": False,
            "action": "update_tags",
            "video_id": video_id,
            "error": str(e),
        })
        print(f"✗ Error updating tags for {video_id}: {e}")
        return False


# =============================================================================
# SEO TAG GENERATION
# =============================================================================

def generate_seo_tags(title: str, description: str, current_tags: List[str] = None) -> List[str]:
    """
    Generate SEO-optimized tags based on video title and description.
    
    Analyzes title and description to extract relevant keywords, genres, techniques,
    and creates optimized tags that improve YouTube search visibility.
    
    Args:
        title: Video title
        description: Video description
        current_tags: Existing tags (optional, for reference)
    
    Returns:
        List of optimized tags (max 500 characters total for YouTube)
    """
    import re
    from collections import Counter
    
    # Base tags that should always be included (your brand)
    base_tags = [
        "brian streckfus",
        "brian streckfus guitar",
        "guitar",
        "music"
    ]
    
    # Extract keywords from title (remove special chars, split)
    title_words = re.findall(r'\b\w+\b', title.lower())
    
    # Extract keywords from description
    # Remove URLs, emojis, and special formatting
    desc_clean = re.sub(r'http\S+|www\.\S+', '', description.lower())
    desc_clean = re.sub(r'[^\w\s]', ' ', desc_clean)
    desc_words = re.findall(r'\b\w+\b', desc_clean)
    
    # Common music/guitar keywords to look for
    music_keywords = {
        'guitar': ['guitar', 'guitarist', 'guitar performance', 'guitar lesson', 
                   'guitar tutorial', 'guitar practice', 'acoustic guitar', 
                   'classical guitar', 'electric guitar', 'fingerstyle guitar',
                   'guitar solo', 'guitar cover', 'guitar tabs', 'guitar scales'],
        'music_theory': ['music theory', 'chord progressions', 'scales', 'modes',
                        'harmonic minor', 'melodic minor', 'nashville numbers',
                        'roman numeral analysis', 'modal interchange'],
        'genres': ['classical', 'metal', 'rock', 'jazz', 'blues', 'folk', 
                  'country', 'flamenco', 'fingerstyle', 'neoclassical', 'edm',
                  'industrial', 'synth', 'electronic'],
        'techniques': ['fingerpicking', 'strumming', 'soloing', 'improvisation',
                      'arrangement', 'composition', 'backing track', 'practice'],
        'instruments': ['guitar', 'acoustic', 'classical', 'nylon string',
                       'steel string', 'electric'],
        'content_type': ['lesson', 'tutorial', 'performance', 'cover', 'original',
                        'backing track', 'sheet music', 'tabs', 'midi', 'etude',
                        'study', 'piece', 'song', 'track']
    }

    # Finance/trading keywords (for videos like "talking stocks/crypto")
    finance_terms = {
        "stocks": ["stocks", "stock", "stock market", "market"],
        "crypto": ["crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth", "altcoin", "altcoins"],
        "trading": ["trading", "trader", "day trading", "swing trading"],
        "investing": ["investing", "investment", "investor"],
    }
    
    # Build tag list
    tags = set(base_tags)

    # Detect finance intent from title/description and seed a few finance tags.
    # (We keep these limited so they don't crowd out the music keywords.)
    title_l = title.lower()
    combined = (title_l + " " + desc_clean).lower()
    finance_hits = set()
    for group, terms in finance_terms.items():
        for t in terms:
            if t in combined:
                finance_hits.add(group)
                break

    finance_pinned = []
    if finance_hits:
        # Add a small set of finance tags and also PIN a couple so they don't get squeezed out
        if "crypto" in finance_hits:
            tags.update(["crypto", "cryptocurrency", "crypto music"])
            finance_pinned.extend(["crypto", "cryptocurrency"])
        if "stocks" in finance_hits:
            tags.update(["stocks", "stock market", "stock market talk"])
            finance_pinned.extend(["stocks", "stock market"])
        if "trading" in finance_hits or "investing" in finance_hits:
            tags.update(["trading", "investing"])
            finance_pinned.extend(["trading", "investing"])
    
    # Add title-based tags
    for word in title_words:
        if len(word) > 3:  # Skip short words
            tags.add(word)
            # Add combinations for common music terms
            if word in ['etude', 'study', 'piece', 'song', 'track', 'backing']:
                tags.add(f"{word} guitar")
            if word in ['minor', 'major', 'scale', 'mode']:
                tags.add(f"{word} guitar")
                tags.add(f"guitar {word}")
            # Avoid junk like "guitar guitar"
            if word == "guitar":
                # keep just "guitar" (already in base tags)
                pass
    
    # Extract specific patterns from description
    # Look for genre mentions
    for genre in music_keywords['genres']:
        if genre in desc_clean:
            tags.add(genre)
            tags.add(f"{genre} guitar")
            if genre in ['classical', 'metal', 'rock', 'jazz']:
                tags.add(f"{genre} music")
    
    # Look for technique mentions
    for technique in music_keywords['techniques']:
        if technique in desc_clean:
            tags.add(technique)
            if 'guitar' not in technique:
                tags.add(f"guitar {technique}")
    
    # Look for composer/artist names (capitalized words in title)
    title_caps = re.findall(r'\b[A-Z][a-z]+\b', title)
    for name in title_caps:
        name_lower = name.lower()
        # Skip common words
        if name_lower not in ['the', 'and', 'for', 'with', 'from', 'this', 'that', 
                             'test', 'op', 'no', 'in', 'on', 'at', 'to', 'of']:
            tags.add(name_lower)
            tags.add(f"{name_lower} guitar")
    
    # Extract scale/key information (e.g., "C# harmonic minor")
    scale_patterns = [
        r'([A-G]#?)\s+(harmonic|melodic|natural)\s+minor',
        r'([A-G]#?)\s+major',
        r'([A-G]#?)\s+minor',
        r'([A-G]#?)\s+scale',
    ]
    for pattern in scale_patterns:
        matches = re.findall(pattern, desc_clean, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                key = match[0].lower().strip()
                scale_type = match[1].lower().strip() if len(match) > 1 else ''
            else:
                key = match.lower().strip()
                scale_type = ''
            
            # Create properly formatted tags (no double spaces)
            if scale_type:
                scale_tag = f"{key} {scale_type}".strip()
                tags.add(scale_tag)
                tags.add(f"{scale_tag} guitar".strip())
            else:
                # Just the key
                tags.add(key)
                tags.add(f"{key} guitar".strip())
    
    # Add relevant long-tail keywords based on content
    if 'backing track' in desc_clean:
        tags.update(['backing track', 'guitar backing track', 'jam track', 
                    'guitar jam track', 'backing track guitar'])
    if 'lesson' in desc_clean or 'tutorial' in desc_clean:
        tags.update(['guitar lesson', 'music lesson', 'how to play guitar', 
                    'guitar tutorial', 'learn guitar'])
    if 'sheet music' in desc_clean or 'tabs' in desc_clean or 'tablature' in desc_clean:
        tags.update(['sheet music', 'guitar tabs', 'tablature', 'guitar sheet music'])
    if 'classical' in desc_clean:
        tags.update(['classical guitar', 'classical music', 'classical guitar performance'])
    if 'etude' in desc_clean or 'etude' in title.lower():
        tags.update(['etude', 'guitar etude', 'classical guitar etude'])
    if 'midi' in desc_clean:
        tags.update(['midi guitar', 'midi visualizer', 'scrolling sheet music'])
    
    # Add music theory tags if relevant
    theory_terms = ['scale', 'chord', 'progression', 'mode', 'key', 'minor', 'major', 
                   'harmonic', 'melodic', 'nashville', 'roman numeral']
    if any(term in desc_clean for term in theory_terms):
        tags.update(['music theory', 'guitar theory', 'music education'])
    
    # Add performance-related tags
    if 'performance' in desc_clean or 'perform' in desc_clean:
        tags.update(['guitar performance', 'live performance', 'guitar recital'])
    if 'cover' in desc_clean:
        tags.update(['guitar cover', 'cover song', 'guitar arrangement'])
    if 'original' in desc_clean:
        tags.update(['original music', 'original composition', 'original guitar'])
    
    # Clean up tags
    final_tags = []
    for tag in tags:
        # Clean up first
        tag = tag.strip().lower()
        
        # Remove very short tags (except single important words)
        if len(tag) < 2:
            continue
        
        # Remove tags that are too long (YouTube limit per tag is ~30 chars, but be safe)
        if len(tag) > 30:
            continue
        
        # Remove tags with multiple consecutive spaces (YouTube doesn't like these)
        if '  ' in tag:
            tag = ' '.join(tag.split())  # Normalize spaces
        
        # Remove tags that are just single letters or numbers (unless they're meaningful)
        if len(tag) == 1 and tag not in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            continue
        
        # Remove tags that start/end with spaces or contain only spaces
        tag = tag.strip()
        if not tag:
            continue
        
        # Remove tags that are just punctuation or special chars
        if not any(c.isalnum() for c in tag):
            continue
        
        # Remove tags with invalid characters (YouTube allows letters, numbers, spaces, hyphens, underscores)
        if not all(c.isalnum() or c in [' ', '-', '_'] for c in tag):
            continue
        
        # Skip tags that are just numbers (unless they're meaningful like "op 60")
        if tag.isdigit() and len(tag) < 3:
            continue
        
        final_tags.append(tag)
    
    # Remove duplicates
    final_tags = list(set(final_tags))

    # -------------------------------------------------------------------------
    # YouTube keyword validation is stricter than the documented 500-char rule in practice.
    # We keep the set smaller and more targeted to avoid "invalidTags" errors.
    # -------------------------------------------------------------------------
    def _finalize_for_youtube(tag_list: List[str]) -> List[str]:
        # Drop very generic/low-signal tokens that tend to bloat tag sets
        stop = {"all", "keys", "music education", "music"}
        tag_list = [t for t in tag_list if t not in stop]

        # Prefer brand + guitar-intent tags, then other relevant tags
        base = [t for t in tag_list if t in base_tags]
        others = [t for t in tag_list if t not in base_tags]

        def score(t: str) -> int:
            s = 0
            if "guitar" in t:
                s += 50
            if "backing track" in t or "jam track" in t:
                s += 20
            if "lesson" in t or "tutorial" in t:
                s += 15
            if "classical" in t or "jazz" in t or "metal" in t or "blues" in t:
                s += 10
            # finance intent (keep some finance context when present)
            if any(k in t for k in ["stock", "stocks", "crypto", "bitcoin", "ethereum", "trading", "investing"]):
                s += 12
            # multi-word tends to be higher-intent than single-word
            if " " in t:
                s += 5
            # penalize obvious redundancy
            if t == "guitar guitar":
                s -= 100
            return s

        others.sort(key=lambda t: (-score(t), t))

        # Conservative caps to avoid invalidTags:
        # - max tags: 25 (keeps payload sane; many failures happened at 34–40 tags)
        # - max chars: 380 (below 500; leaves headroom for API serialization quirks)
        MAX_TAGS = 25
        MAX_CHARS = 380

        chosen: List[str] = []
        for t in base:
            if t not in chosen:
                chosen.append(t)

        # Pin a few finance tags if this video is clearly finance-related.
        # Keep this small so we don't dilute the core guitar keywords.
        for t in finance_pinned[:3]:
            if t in tag_list and t not in chosen:
                candidate = chosen + [t]
                char_count = sum(len(x) for x in candidate) + max(len(candidate) - 1, 0)
                if len(candidate) <= MAX_TAGS and char_count <= MAX_CHARS:
                    chosen.append(t)

        for t in others:
            if t in chosen:
                continue
            # enforce per-tag length again defensively
            if len(t) > 30:
                continue
            candidate = chosen + [t]
            char_count = sum(len(x) for x in candidate) + max(len(candidate) - 1, 0)
            if len(candidate) > MAX_TAGS:
                continue
            if char_count > MAX_CHARS:
                continue
            chosen.append(t)
            if len(chosen) >= MAX_TAGS:
                break

        return chosen

    final_tags = _finalize_for_youtube(final_tags)

    # Stable output
    final_tags = sorted(final_tags)
    
    return final_tags


def check_quota_status(service) -> Dict[str, any]:
    """
    Check YouTube API quota usage (approximate).
    Note: YouTube doesn't provide exact quota info, but we can estimate based on errors.
    
    Returns:
        Dictionary with quota status info
    """
    try:
        # Try a lightweight operation to see if we have quota
        request = service.channels().list(part='snippet', mine=True, maxResults=1)
        request.execute()
        return {
            'has_quota': True,
            'message': 'Quota available (estimated)'
        }
    except HttpError as e:
        if 'quotaExceeded' in str(e):
            return {
                'has_quota': False,
                'message': 'Quota exceeded - wait for daily reset (midnight Pacific Time)'
            }
        return {
            'has_quota': True,
            'message': f'Quota check error: {e}'
        }
    except Exception as e:
        return {
            'has_quota': True,
            'message': f'Quota check error: {e}'
        }


def batch_update_tags_seo(service, backup_file: str = "youtube_backup_20251227_032322.json",
                          dry_run: bool = True, batch_size: int = 20, delay_seconds: float = 2.0,
                          oldest_first: bool = True) -> Dict[str, bool]:
    """
    Analyze all videos and update tags with SEO-optimized versions.
    
    Reads from backup file, generates new SEO tags for each video based on
    title and description, and optionally updates them on YouTube.
    
    Processes videos in batches to avoid quota exhaustion.
    Each video update costs ~50 quota units. Default daily limit is 10,000 units.
    
    Args:
        service: YouTube API service object
        backup_file: Path to backup JSON file
        dry_run: If True, only show what would be updated without making changes
        batch_size: Number of videos to process before checking quota (default: 20)
        delay_seconds: Delay between batches in seconds (default: 2.0)
        oldest_first: If True, process oldest videos first (by publishedAt) when available
    
    Returns:
        Dictionary mapping video_id to success status
    """
    import json
    import time
    
    # Check quota status first (only when doing LIVE updates)
    if not dry_run:
        if service is None:
            raise ValueError("service is required when dry_run=False")
        print("Checking API quota status...")
        quota_status = check_quota_status(service)
        print(f"  {quota_status['message']}")
        if not quota_status['has_quota']:
            print("\n⚠️  Cannot proceed - quota exhausted. Please wait for daily reset.")
            return {}
        print()
    
    # Load backup
    if not os.path.exists(backup_file):
        print(f"✗ Backup file not found: {backup_file}")
        return {}
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup = json.load(f)
    
    # Sort videos oldest->newest when possible (YouTube publishedAt is ISO8601)
    # This helps you start with older catalog content first, as requested.
    try:
        videos_list = list(backup.get('videos', []))
        def _published_at(v: dict) -> str:
            # Prefer explicit publishedAt; fallback to empty string (will sort first)
            return str(v.get('publishedAt') or "")
        if oldest_first:
            videos_list.sort(key=_published_at)
        else:
            videos_list.sort(key=_published_at, reverse=True)
        backup['videos'] = videos_list
    except Exception:
        pass
    
    results = {}
    total = len(backup['videos'])
    
    # Calculate quota usage
    # Each video update = 50 units, each video info fetch = 1 unit
    estimated_quota_per_video = 51  # 50 for update + 1 for get info
    estimated_total_quota = total * estimated_quota_per_video
    
    print(f"\n{'='*60}")
    print(f"🔍 SEO TAG ANALYSIS & UPDATE")
    print(f"{'='*60}")
    print(f"Total videos: {total}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
    print(f"Batch size: {batch_size} videos per batch")
    print(f"Delay between batches: {delay_seconds} seconds")
    print(f"Estimated quota needed: ~{estimated_total_quota:,} units")
    print(f"  (Each update = 50 units, each info fetch = 1 unit)")
    print(f"  (Daily limit typically = 10,000 units)")
    if estimated_total_quota > 10000:
        print(f"  ⚠️  WARNING: This will exceed daily quota! Processing in batches...")
    print(f"{'='*60}\n")
    
    successful_count = 0
    failed_count = 0
    quota_exceeded = False
    
    for i, video in enumerate(backup['videos'], 1):
        video_id = video['id']
        title = video['title']
        description = video.get('description', '')
        current_tags = video.get('tags', [])
        
        # Generate new tags
        new_tags = generate_seo_tags(title, description, current_tags)
        
        # Calculate character counts
        current_char_count = sum(len(tag) for tag in current_tags) + len(current_tags) - 1
        new_char_count = sum(len(tag) for tag in new_tags) + len(new_tags) - 1
        
        # Compare
        current_tag_str = ', '.join(current_tags[:5]) + ('...' if len(current_tags) > 5 else '')
        new_tag_str = ', '.join(new_tags[:5]) + ('...' if len(new_tags) > 5 else '')
        
        print(f"[{i}/{total}] {title[:50]}...")
        print(f"   Current: {len(current_tags)} tags ({current_char_count} chars) - {current_tag_str}")
        print(f"   New:     {len(new_tags)} tags ({new_char_count} chars) - {new_tag_str}")
        
        if not dry_run:
            # Check for quota before processing
            if quota_exceeded:
                print(f"   ⏸️  Skipped (quota exhausted)")
                results[video_id] = False
                failed_count += 1
                continue
            
            try:
                success = update_video_tags(service, video_id, new_tags, replace=True)
                results[video_id] = success
                if success:
                    print(f"   ✓ Updated successfully")
                    successful_count += 1
                else:
                    print(f"   ✗ Update failed")
                    failed_count += 1
            except HttpError as e:
                if 'quotaExceeded' in str(e):
                    print(f"   ⚠️  QUOTA EXCEEDED - Stopping batch")
                    quota_exceeded = True
                    results[video_id] = False
                    failed_count += 1
                else:
                    print(f"   ✗ Error: {e}")
                    results[video_id] = False
                    failed_count += 1
            except Exception as e:
                print(f"   ✗ Error: {e}")
                results[video_id] = False
                failed_count += 1
        else:
            results[video_id] = True
            print(f"   [DRY RUN - would update]")
        
        # Batch processing: pause after each batch
        if not dry_run and i % batch_size == 0 and i < total:
            print(f"\n   📊 Progress: {successful_count} updated, {failed_count} failed")
            if not quota_exceeded:
                print(f"   ⏸️  Pausing {delay_seconds}s before next batch...")
                time.sleep(delay_seconds)
                # Check quota status
                quota_status = check_quota_status(service)
                if not quota_status['has_quota']:
                    print(f"   ⚠️  Quota exhausted - stopping")
                    quota_exceeded = True
            print()
        
        if quota_exceeded and not dry_run:
            break
        
        print()
    
    successful = sum(1 for v in results.values() if v)
    processed = len(results)
    
    print(f"{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Processed: {processed}/{total} videos")
    print(f"Successful: {successful}")
    print(f"Failed: {failed_count}")
    
    if quota_exceeded:
        remaining = total - processed
        print(f"\n⚠️  QUOTA EXCEEDED")
        print(f"   Remaining videos: {remaining}")
        print(f"   Estimated quota used: ~{processed * estimated_quota_per_video:,} units")
        print(f"   Wait for daily reset (midnight Pacific Time) to continue")
        print(f"   You can re-run this script to process remaining videos")
    
    if dry_run:
        print(f"\n💡 This was a DRY RUN. Set dry_run=False to apply changes.")
        print(f"   Example: batch_update_tags_seo(service, dry_run=False, batch_size=20)")
    elif not quota_exceeded and processed < total:
        print(f"\n💡 To continue processing remaining videos, run the script again.")
    
    print(f"{'='*60}")
    
    return results


# =============================================================================
# WORKFLOWS (SAFE DEFAULTS)
# =============================================================================

def run_seo_tag_plan_from_backup(backup_file: str, oldest_first: bool = True) -> str:
    """
    Create a local "plan" file showing current vs proposed SEO tags, oldest-first.
    This makes NO API calls and does NOT require authentication.

    Returns:
        str: path to the generated plan file
    """
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    with open(backup_file, "r", encoding="utf-8") as f:
        backup = json.load(f)

    videos = list(backup.get("videos", []))
    def _published_at(v: dict) -> str:
        return str(v.get("publishedAt") or "")
    videos.sort(key=_published_at, reverse=not oldest_first)

    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "backup_file": backup_file,
        "oldest_first": bool(oldest_first),
        "total_videos": len(videos),
        "videos": [],
    }

    for v in videos:
        vid = v.get("id")
        title = v.get("title", "")
        desc = v.get("description", "") or ""
        current_tags = v.get("tags", []) or []
        new_tags = generate_seo_tags(title, desc, current_tags)
        plan["videos"].append({
            "id": vid,
            "title": title,
            "publishedAt": v.get("publishedAt"),
            "current_tags": current_tags,
            "new_tags": new_tags,
            "current_tag_chars": (sum(len(t) for t in current_tags) + max(len(current_tags) - 1, 0)),
            "new_tag_chars": (sum(len(t) for t in new_tags) + max(len(new_tags) - 1, 0)),
        })

    plan_file = f"youtube_tag_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"✓ Wrote tag update plan: {plan_file}")
    print(f"  Review this before running live updates (it makes no API calls).")
    return plan_file


def apply_seo_tag_plan(service, plan_file: str, dry_run: bool = True,
                       batch_size: int = 20, delay_seconds: float = 2.0,
                       skip_already_successful: bool = True) -> Dict[str, bool]:
    """
    Apply tags from a previously generated plan file.
    Uses update_video_tags() which logs + skips already-applied identical updates.
    """
    if not os.path.exists(plan_file):
        raise FileNotFoundError(f"Plan file not found: {plan_file}")
    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    videos = plan.get("videos", [])
    results: Dict[str, bool] = {}
    total = len(videos)

    print(f"\nApplying plan: {plan_file}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
    print(f"Total videos in plan: {total}")
    print(f"Batch size: {batch_size} | Delay: {delay_seconds}s\n")
    if skip_already_successful:
        print(f"Skip already-successful videos: ON (uses youtube_change_log.jsonl)\n")

    if not dry_run:
        if service is None:
            raise ValueError("service is required when dry_run=False")
        print("Checking API quota status...")
        quota_status = check_quota_status(service)
        print(f"  {quota_status['message']}")
        if not quota_status['has_quota']:
            print("\n⚠️  Cannot proceed - quota exhausted. Please wait for daily reset.")
            return {}
        print()

    ok_ids = _load_successful_video_ids("update_tags") if skip_already_successful else set()

    import time
    for i, v in enumerate(videos, 1):
        video_id = v.get("id")
        title = v.get("title", "")
        new_tags = v.get("new_tags", []) or []

        print(f"[{i}/{total}] {title[:50]}...")
        if skip_already_successful and isinstance(video_id, str) and video_id in ok_ids:
            results[str(video_id)] = True
            print("   ↩︎ Skipping (tags already updated successfully in a previous run)\n")
            continue
        if dry_run:
            results[str(video_id)] = True
            print("   [DRY RUN - would update tags]\n")
        else:
            ok = update_video_tags(service, str(video_id), new_tags, replace=True)
            results[str(video_id)] = bool(ok)
            print()

        if not dry_run and i % batch_size == 0 and i < total:
            print(f"⏸️  Pausing {delay_seconds}s before next batch...\n")
            time.sleep(delay_seconds)
    
    return results


# =============================================================================
# SECONDARY: THUMBNAIL MANAGEMENT
# =============================================================================

def update_video_thumbnail(service, video_id: str, thumbnail_path: str) -> bool:
    """
    Update video thumbnail.
    
    Args:
        service: YouTube API service object
        video_id: YouTube video ID
        thumbnail_path: Path to thumbnail image file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        applied = _load_applied_fingerprints()
        action = "update_thumbnail"

        if not os.path.exists(thumbnail_path):
            _append_change_log({
                "ok": False,
                "action": action,
                "video_id": video_id,
                "thumbnail_path": thumbnail_path,
                "error": "Thumbnail file not found",
            })
            print(f"Thumbnail file not found: {thumbnail_path}")
            return False

        # Idempotency: if the same file path + file hash was already applied, skip
        try:
            with open(thumbnail_path, "rb") as f:
                thumb_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception:
            thumb_hash = None
        payload_fp = _fingerprint({
            "video_id": video_id,
            "action": action,
            "thumbnail_path": os.path.abspath(thumbnail_path),
            "thumbnail_sha256": thumb_hash,
        })
        if (video_id, action, payload_fp) in applied:
            _append_change_log({
                "ok": True,
                "action": action,
                "video_id": video_id,
                "fingerprint": payload_fp,
                "skipped": True,
                "reason": "Already applied in previous run (fingerprint match)",
                "thumbnail_path": thumbnail_path,
                "thumbnail_sha256": thumb_hash,
            })
            print(f"↩︎ Skipping thumbnail update (already applied): {video_id}")
            return True
        
        request = service.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
        )
        request.execute()
        
        _append_change_log({
            "ok": True,
            "action": action,
            "video_id": video_id,
            "fingerprint": payload_fp,
            "thumbnail_path": thumbnail_path,
            "thumbnail_sha256": thumb_hash,
            "quota_cost_estimate": 50,
        })
        print(f"✓ Updated thumbnail for video: {video_id}")
        return True
    
    except HttpError as e:
        _append_change_log({
            "ok": False,
            "action": "update_thumbnail",
            "video_id": video_id,
            "thumbnail_path": thumbnail_path,
            "error": str(e),
        })
        print(f"✗ Error updating thumbnail for {video_id}: {e}")
        return False


# =============================================================================
# SECONDARY: PLAYLIST MANAGEMENT
# =============================================================================

def create_playlist(service, title: str, description: str = "", 
                   privacy: str = "private") -> Optional[str]:
    """
    Create a new playlist.
    
    Args:
        service: YouTube API service object
        title: Playlist title
        description: Playlist description
        privacy: 'private', 'public', or 'unlisted'
    
    Returns:
        Playlist ID if successful, None otherwise
    """
    try:
        request = service.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description
                },
                'status': {
                    'privacyStatus': privacy
                }
            }
        )
        response = request.execute()
        
        playlist_id = response['id']
        print(f"✓ Created playlist: {title} (ID: {playlist_id})")
        return playlist_id
    
    except HttpError as e:
        print(f"✗ Error creating playlist: {e}")
        return None


def add_video_to_playlist(service, playlist_id: str, video_id: str, 
                         position: Optional[int] = None) -> bool:
    """
    Add video to playlist.
    
    Args:
        service: YouTube API service object
        playlist_id: Playlist ID
        video_id: Video ID to add
        position: Optional position in playlist (0-indexed)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        
        if position is not None:
            body['snippet']['position'] = position
        
        request = service.playlistItems().insert(
            part='snippet',
            body=body
        )
        request.execute()
        
        print(f"✓ Added video {video_id} to playlist {playlist_id}")
        return True
    
    except HttpError as e:
        print(f"✗ Error adding video to playlist: {e}")
        return False


def get_playlists(service) -> List[Dict]:
    """Get all playlists for the authenticated channel."""
    try:
        playlists = []
        next_page_token = None
        
        while True:
            request = service.playlists().list(
                part='snippet,contentDetails',
                mine=True,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            playlists.extend(response['items'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return playlists
    
    except HttpError as e:
        print(f"✗ Error getting playlists: {e}")
        return []


# =============================================================================
# SECONDARY: CHAPTERS MANAGEMENT
# =============================================================================

def add_chapters_to_description(service, video_id: str, chapters: List[Dict]) -> bool:
    """
    Add chapters to video description.
    
    Args:
        service: YouTube API service object
        video_id: YouTube video ID
        chapters: List of chapter dicts with 'time' (HH:MM:SS) and 'title' keys
    
    Returns:
        True if successful, False otherwise
    """
    try:
        video = get_video_info(service, video_id)
        if not video:
            return False
        
        snippet = video['snippet']
        description = snippet.get('description', '')
        
        # Format chapters
        chapter_text = "\n\n--- Chapters ---\n"
        for chapter in chapters:
            chapter_text += f"{chapter['time']} - {chapter['title']}\n"
        
        # Append chapters to description
        new_description = description + chapter_text
        
        snippet['description'] = new_description
        
        request = service.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        )
        request.execute()
        
        print(f"✓ Added chapters to video: {snippet.get('title', video_id)}")
        return True
    
    except HttpError as e:
        print(f"✗ Error adding chapters: {e}")
        return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def export_video_list(service, output_file: Optional[str] = None):
    """
    Export all video information to JSON file as a backup.
    Includes titles, descriptions, tags, thumbnails, and all metadata.
    This should be run FIRST before making any changes to videos.
    """
    from datetime import datetime
    
    # Generate timestamped filename if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"youtube_backup_{timestamp}.json"
    
    print("=" * 60)
    print("📦 BACKUP: Exporting all YouTube video information...")
    print("=" * 60)
    
    videos = get_all_videos(service)
    
    if not videos:
        print("⚠️  No videos found in channel")
        return
    
    # Comprehensive video data export
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'total_videos': len(videos),
        'videos': []
    }
    
    for i, video in enumerate(videos, 1):
        snippet = video.get('snippet', {})
        status = video.get('status', {})
        content_details = video.get('contentDetails', {})
        
        video_info = {
            'id': video['id'],
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'tags': snippet.get('tags', []),
            'categoryId': snippet.get('categoryId', ''),
            'publishedAt': snippet.get('publishedAt', ''),
            'channelId': snippet.get('channelId', ''),
            'channelTitle': snippet.get('channelTitle', ''),
            'defaultLanguage': snippet.get('defaultLanguage', ''),
            'defaultAudioLanguage': snippet.get('defaultAudioLanguage', ''),
            'url': f"https://www.youtube.com/watch?v={video['id']}",
            
            # Thumbnails
            'thumbnails': snippet.get('thumbnails', {}),
            
            # Status information
            'privacyStatus': status.get('privacyStatus', ''),
            'madeForKids': status.get('selfDeclaredMadeForKids', False),
            'license': status.get('license', ''),
            
            # Content details
            'duration': content_details.get('duration', ''),
            'dimension': content_details.get('dimension', ''),
            'definition': content_details.get('definition', ''),
            'caption': content_details.get('caption', ''),
            'licensedContent': content_details.get('licensedContent', False),
            
            # Statistics (if available)
            'statistics': video.get('statistics', {}),
        }
        
        export_data['videos'].append(video_info)
        
        # Progress indicator
        if i % 10 == 0 or i == len(videos):
            print(f"   Processed {i}/{len(videos)} videos...")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # Size in MB
    print(f"\n✓ Backup complete!")
    print(f"   Exported {len(videos)} videos to: {output_file}")
    print(f"   File size: {file_size:.2f} MB")
    print(f"   📝 This backup contains all video metadata for recovery if needed")
    print("=" * 60)


def search_videos_by_title(service, search_term: str) -> List[Dict]:
    """Search videos by title (case-insensitive)."""
    videos = get_all_videos(service)
    search_lower = search_term.lower()
    
    return [v for v in videos if search_lower in v['snippet']['title'].lower()]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube API Manager")
    parser.add_argument("--backup-file", default="youtube_backup_20251227_032322.json", help="Backup JSON file containing videos[]")

    # Bulk top-level comments (pinning not supported by API)
    parser.add_argument("--bulk-comment", action="store_true", help="Enable bulk TOP-LEVEL comment posting workflow (pinning not supported by API)")
    parser.add_argument("--comment-text", default=None, help="Comment text to post (if omitted, uses DEFAULT_BULK_COMMENT_TEXT)")
    parser.add_argument("--comment-text-file", default=None, help="Path to a UTF-8 text file containing the comment to post")
    parser.add_argument("--oldest-first", action="store_true", help="Post comments oldest->newest (default).")
    parser.add_argument("--newest-first", action="store_true", help="Post comments newest->oldest.")
    parser.add_argument("--limit", type=int, default=10, help="How many videos to include from the sorted list (default: 10). Increase this later; already-posted comments will be skipped via youtube_change_log.jsonl.")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (NO API calls; just generates a plan). Recommended first step.")
    parser.add_argument("--live", action="store_true", help="LIVE update (will authenticate + post comments).")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for live posting pauses (default: 10)")
    parser.add_argument("--delay-seconds", type=float, default=2.0, help="Delay between batches in live mode (default: 2.0)")

    args = parser.parse_args()

    print("YouTube API Manager ready!")
    print("=" * 60)
    print("NOTE: The YouTube Data API v3 does NOT support pinning comments.")
    print("      This script can only post TOP-LEVEL comments.\n")

    # If no explicit workflow flags were provided, just print guidance and exit.
    if not args.bulk_comment:
        print("Bulk comment posting is available but OFF by default.")
        print("Example (dry run plan only; no API calls):")
        print("  python3 youtube_api.py --bulk-comment --dry-run --backup-file youtube_backup_20251227_032322.json")
        print("\nExample (LIVE posting; will authenticate and post comments):")
        print("  python3 youtube_api.py --bulk-comment --live --backup-file youtube_backup_20251227_032322.json --batch-size 10 --delay-seconds 2")
        print("\nTip: Provide your promotional comment with --comment-text-file promo.txt (recommended) or --comment-text \"...\"")
        raise SystemExit(0)

    # Resolve comment text
    comment_text = args.comment_text
    if args.comment_text_file:
        with open(args.comment_text_file, "r", encoding="utf-8") as f:
            comment_text = f.read().strip()
    if not comment_text:
        comment_text = DEFAULT_BULK_COMMENT_TEXT

    if not comment_text.strip():
        raise SystemExit("Comment text is empty. Provide --comment-text or --comment-text-file.")

    # Ordering
    oldest_first = True
    if args.newest_first:
        oldest_first = False
    elif args.oldest_first:
        oldest_first = True

    # Safety: default to dry-run unless --live is explicitly set
    dry_run = True
    if args.live:
        dry_run = False
    if args.dry_run:
        dry_run = True

    # 1) Always generate a plan first (no API calls)
    plan_file = run_bulk_comment_plan_from_backup(
        backup_file=args.backup_file,
        comment_text=comment_text,
        oldest_first=oldest_first,
        limit=int(args.limit) if args.limit and args.limit > 0 else None,
    )

    # 2) Apply plan (only in live mode)
    if dry_run:
        print("\n[DRY RUN] Plan generated; no comments were posted.")
        print(f"Review plan file: {plan_file}")
        raise SystemExit(0)

    # LIVE mode: authenticate + post comments
    svc = get_authenticated_service()
    apply_bulk_comment_plan(
        service=svc,
        plan_file=plan_file,
        dry_run=False,
        batch_size=int(args.batch_size),
        delay_seconds=float(args.delay_seconds),
        skip_already_successful=True,
    )

