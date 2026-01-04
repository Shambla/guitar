"""
Update SEO tags on your LATEST YouTube upload only.

Usage:
  cd /Users/olivia2/Documents/GitHub/guitar/web/WebContent
  source venv_youtube/bin/activate
  python3 update_latest_video_tags.py

Optional:
  python3 update_latest_video_tags.py --dry-run
"""

import argparse

import youtube_api


def get_latest_uploaded_video_id(service) -> str:
    """
    Returns the newest upload's videoId for the authenticated channel.
    Uses the channel's uploads playlist (newest-first ordering).
    """
    channel_resp = service.channels().list(part="contentDetails", mine=True).execute()
    if not channel_resp.get("items"):
        raise RuntimeError("No channel found for authenticated user.")

    uploads_playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    pl_resp = service.playlistItems().list(
        part="contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=1,
    ).execute()

    items = pl_resp.get("items") or []
    if not items:
        raise RuntimeError("No uploads found in uploads playlist.")

    return items[0]["contentDetails"]["videoId"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Compute/print tags, but do not update YouTube.")
    args = parser.parse_args()

    print("Authenticating with YouTube API...")
    svc = youtube_api.get_authenticated_service()
    print("✓ Authentication successful")

    latest_id = get_latest_uploaded_video_id(svc)
    print(f"\nLatest upload video ID: {latest_id}")
    print(f"URL: https://www.youtube.com/watch?v={latest_id}")

    video = youtube_api.get_video_info(svc, latest_id)
    if not video:
        raise RuntimeError(f"Could not fetch video info for {latest_id}")

    snippet = video.get("snippet", {}) or {}
    title = snippet.get("title", "")
    desc = snippet.get("description", "") or ""
    current_tags = snippet.get("tags", []) or []

    print(f"\nTitle: {title}")
    print(f"Current tag count: {len(current_tags)}")

    new_tags = youtube_api.generate_seo_tags(title, desc, current_tags)
    print(f"Proposed tag count: {len(new_tags)}")
    print("Proposed tags:")
    for t in new_tags:
        print(f"- {t}")

    if args.dry_run:
        print("\nDRY RUN: no changes applied.")
        return 0

    print("\nUpdating tags for latest video...")
    ok = youtube_api.update_video_tags(svc, latest_id, new_tags, replace=True)
    print(f"\nDone. success={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


