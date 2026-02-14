"""
Instagram API Manager
Manage Instagram profile, media, and insights via the Instagram Graph API (Meta).

------------------------------------------------------------------------------
READ THIS FIRST (Secrets / Tokens)
------------------------------------------------------------------------------
This script does NOT hardcode any Instagram/Meta secrets. It reads credentials
from environment variables or local files:
  - Instagram media folder = GitHub/guitar/web/WebContent/img/uploading_folder/
  - Long-lived User Access Token (for Instagram Graph API)
  - Optional: Facebook App ID and App Secret (for token exchange/refresh)

What you need to do (one-time setup):
  1) Go to Meta for Developers: https://developers.facebook.com/
  2) Create an app and add "Instagram Graph API" product.
  3) Connect your Instagram Business or Creator account to a Facebook Page.
  4) Get a long-lived User Access Token with permissions:
       instagram_basic, instagram_manage_insights (and others as needed).
  5) Store the token in IG_TOKEN_FILE (default: instagram_token.json) or set
     IG_ACCESS_TOKEN in the environment.

Security notes:
  - DO NOT commit or share: instagram_token.json, client secrets, or tokens.
  - Rotate tokens if they are ever exposed.

Optional path / token override via environment variables:
  - IG_TOKEN_FILE: path to JSON file with "access_token" key
  - IG_ACCESS_TOKEN: raw access token (overrides file if set)
  - IG_APP_ID: Facebook App ID (for token debug or refresh)
  - IG_APP_SECRET: Facebook App Secret (for token exchange; keep secret)

Requirements:
    pip install requests

Example usage:
    cd /path/to/WebContent
    python3 instagram_api.py --profile
    python3 instagram_api.py --media --limit 12
------------------------------------------------------------------------------
"""

import os
import json
import argparse
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# =============================================================================
# CONFIGURATION
# =============================================================================

# Folder where you store media files to upload (path relative to this script).
MEDIA_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "uploading_folder")

# JSON file with at least: {"access_token": "..."}
# Optional: "user_id" (Instagram Business Account ID) to avoid a profile lookup.
TOKEN_FILE = os.getenv("IG_TOKEN_FILE", "instagram_token.json")
# Raw token overrides file if set
ACCESS_TOKEN_ENV = os.getenv("IG_ACCESS_TOKEN", "").strip()
APP_ID = os.getenv("IG_APP_ID", "").strip()
APP_SECRET = os.getenv("IG_APP_SECRET", "").strip()

# Read-only: Instagram Graph API base (profile, media list, insights)
GRAPH_API_BASE = "https://graph.instagram.com"
# Posting: use Facebook Graph API only (graph.instagram.com is read-only for publish)
GRAPH_FACEBOOK_BASE = "https://graph.facebook.com"
GRAPH_API_VERSION = "v21.0"

# =============================================================================
# CHANGE LOG (optional audit trail, same idea as youtube_api)
# =============================================================================
CHANGE_LOG_FILE = "instagram_change_log.jsonl"
ENABLE_CHANGE_LOG = True


def _json_dumps_safe(obj: Any) -> str:
    """JSON dump helper that won't crash on non-serializable objects."""
    def _default(o: Any) -> str:
        try:
            return str(o)
        except Exception:
            return "<unserializable>"
    return json.dumps(obj, ensure_ascii=False, default=_default)


def _append_change_log(event: Dict[str, Any]) -> None:
    if not ENABLE_CHANGE_LOG:
        return
    try:
        from datetime import datetime
        event = dict(event)
        event.setdefault("ts", datetime.now().isoformat(timespec="seconds"))
        with open(CHANGE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(_json_dumps_safe(event) + "\n")
    except Exception:
        pass


# =============================================================================
# TOKEN LOADING
# =============================================================================

def load_access_token() -> Optional[str]:
    """Load access token from IG_ACCESS_TOKEN env or from TOKEN_FILE."""
    if ACCESS_TOKEN_ENV:
        return ACCESS_TOKEN_ENV
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("access_token") or data.get("access_token_long_lived") or "").strip() or None
    except Exception:
        return None


def get_saved_user_id() -> Optional[str]:
    """If token file contains 'user_id' (IG Business Account ID), return it."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("user_id") or data.get("instagram_business_account", {}).get("id") or "").strip() or None
    except Exception:
        return None


# =============================================================================
# API CLIENT
# =============================================================================

def get_authenticated_client() -> "InstagramAPI":
    """Build authenticated Instagram API client. Raises if no token or requests missing."""
    if requests is None:
        raise RuntimeError("Install requests: pip install requests")
    token = load_access_token()
    if not token:
        raise RuntimeError(
            "No Instagram access token. Set IG_ACCESS_TOKEN or create "
            f"{TOKEN_FILE} with an 'access_token' key. See script docstring for setup."
        )
    return InstagramAPI(access_token=token)


class InstagramAPI:
    """Client for Instagram: read via graph.instagram.com, publish via graph.facebook.com."""

    def __init__(self, access_token: str, version: str = GRAPH_API_VERSION):
        self.access_token = access_token
        self.version = version
        self.base_url = f"{GRAPH_API_BASE}/{version}"
        self.publish_base_url = f"{GRAPH_FACEBOOK_BASE}/{version}"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        params = dict(params or {})
        params["access_token"] = self.access_token
        if method.upper() == "GET":
            resp = requests.get(url, params=params, timeout=30)
        else:
            resp = requests.post(url, params=params, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _request_publish(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST to graph.facebook.com (required for publishing on your behalf)."""
        url = f"{self.publish_base_url}/{path.lstrip('/')}"
        params = dict(params or {})
        params["access_token"] = self.access_token
        resp = requests.post(url, params=params, json=data, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def get_me(self, fields: str = "id,username,account_type,media_count") -> Dict[str, Any]:
        """Fetch the Instagram user (me) associated with the token."""
        return self._request("GET", "me", params={"fields": fields})

    def get_user_media(
        self,
        user_id: Optional[str] = None,
        limit: int = 25,
        before: Optional[str] = None,
        after: Optional[str] = None,
        fields: str = "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp",
    ) -> Dict[str, Any]:
        """Fetch media list for the given user (default: me). Pagination: before/after cursors."""
        uid = user_id or "me"
        params: Dict[str, str] = {"fields": fields, "limit": str(limit)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request("GET", f"{uid}/media", params=params)

    def get_media_insights(
        self,
        media_id: str,
        metrics: str = "engagement,impressions,reach,saved",
    ) -> Dict[str, Any]:
        """Fetch insights for a single media (photo/video). Requires instagram_manage_insights."""
        return self._request("GET", f"{media_id}/insights", params={"metric": metrics})

    def get_user_insights(
        self,
        user_id: Optional[str] = None,
        period: str = "day",
        metrics: str = "impressions,reach,follower_count",
    ) -> Dict[str, Any]:
        """Fetch account-level insights. period: day, week, days_28."""
        uid = user_id or "me"
        return self._request(
            "GET",
            f"{uid}/insights",
            params={"period": period, "metric": metrics},
        )

    def get_media_children(self, media_id: str, fields: str = "id,media_type,media_url") -> Dict[str, Any]:
        """For carousel albums, get child media."""
        return self._request("GET", f"{media_id}/children", params={"fields": fields})


# =============================================================================
# HIGH-LEVEL HELPERS
# =============================================================================

def fetch_profile(api: Optional[InstagramAPI] = None) -> Dict[str, Any]:
    """Get current Instagram profile (id, username, account_type, media_count)."""
    client = api or get_authenticated_client()
    return client.get_me()


def fetch_media_list(
    limit: int = 25,
    before: Optional[str] = None,
    after: Optional[str] = None,
    api: Optional[InstagramAPI] = None,
) -> Dict[str, Any]:
    """Fetch media list for the authenticated account. Logs to change log."""
    client = api or get_authenticated_client()
    data = client.get_user_media(limit=limit, before=before, after=after)
    _append_change_log({
        "action": "fetch_media",
        "limit": limit,
        "count": len(data.get("data", [])),
        "paging": data.get("paging"),
    })
    return data


def get_ig_user_id(api: Optional[InstagramAPI] = None) -> str:
    """Instagram Business/Creator account ID (for publishing). From token file or get_me()."""
    client = api or get_authenticated_client()
    saved = get_saved_user_id()
    if saved:
        return saved
    me = client.get_me()
    uid = me.get("id")
    if not uid:
        raise RuntimeError("Could not get Instagram user id from get_me()")
    return uid


def post_photo(
    image_url: str,
    caption: Optional[str] = None,
    alt_text: Optional[str] = None,
    api: Optional[InstagramAPI] = None,
) -> Dict[str, Any]:
    """Create image container and publish via graph.facebook.com. Logs to change log."""
    client = api or get_authenticated_client()
    ig_user_id = get_ig_user_id(client)
    result = client.post_photo(ig_user_id, image_url, caption=caption, alt_text=alt_text)
    _append_change_log({"action": "post_photo", "ok": True, "media_id": result["media_id"], "image_url": image_url})
    return result


# =============================================================================
# MAIN / CLI
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Instagram API – profile, media, and posting")
    parser.add_argument("--profile", action="store_true", help="Print Instagram profile (id, username, media_count)")
    parser.add_argument("--media", action="store_true", help="Fetch and print recent media")
    parser.add_argument("--limit", type=int, default=12, help="Max media items (default 12)")
    parser.add_argument("--post", action="store_true", help="Publish a photo (uses graph.facebook.com)")
    parser.add_argument("--image-url", type=str, default="", help="Public URL of image to post (required for --post)")
    parser.add_argument("--caption", type=str, default="", help="Caption for the post")
    parser.add_argument("--alt-text", type=str, default="", help="Accessibility alt text for the image")
    parser.add_argument("--token-file", type=str, default="", help="Override token JSON file path")
    args = parser.parse_args()

    global TOKEN_FILE
    if args.token_file:
        TOKEN_FILE = args.token_file

    if not args.profile and not args.media and not args.post:
        parser.print_help()
        print("\nExample: python3 instagram_api.py --profile")
        print("         python3 instagram_api.py --media --limit 12")
        print("         python3 instagram_api.py --post --image-url \"https://example.com/photo.jpg\" --caption \"My post\"")
        return

    api = get_authenticated_client()

    if args.profile:
        profile = fetch_profile(api)
        print(json.dumps(profile, indent=2))

    if args.media:
        result = fetch_media_list(limit=args.limit, api=api)
        print(json.dumps(result, indent=2))

    if args.post:
        if not args.image_url or not args.image_url.strip():
            raise SystemExit("--post requires --image-url (public URL of the image)")
        result = post_photo(
            args.image_url.strip(),
            caption=args.caption.strip() or None,
            alt_text=args.alt_text.strip() or None,
            api=api,
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
