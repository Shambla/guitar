"""
YouTube API Manager
Efficiently manage YouTube video descriptions, tags, thumbnails, playlists, and chapters.

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Setup:
    1. Go to Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select existing one
    3. Enable YouTube Data API v3
    4. Create OAuth 2.0 credentials (Desktop app)
    5. Download credentials JSON file
    6. Set CLIENT_SECRETS_FILE path below
"""

import os
import json
from typing import List, Dict, Optional, Tuple
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
CLIENT_SECRETS_FILE = "client_secrets.json"  # Update this path

# OAuth 2.0 scopes required for YouTube API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.upload'
]

# Token file to store credentials
TOKEN_FILE = "youtube_token.json"

# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_authenticated_service():
    """Authenticate and return YouTube API service object."""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
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
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as token:
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
            
            # Get detailed video information
            if video_ids:
                video_request = service.videos().list(
                    part='snippet,status',
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
        # Get current video data
        video = get_video_info(service, video_id)
        if not video:
            print(f"Video {video_id} not found")
            return False
        
        snippet = video['snippet']
        
        # Handle append/prepend
        if append:
            current_desc = snippet.get('description', '')
            new_description = current_desc + '\n\n' + new_description
        elif prepend:
            current_desc = snippet.get('description', '')
            new_description = new_description + '\n\n' + current_desc
        
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
        
        print(f"✓ Updated description for video: {snippet.get('title', video_id)}")
        return True
    
    except HttpError as e:
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
        video = get_video_info(service, video_id)
        if not video:
            return False
        
        snippet = video['snippet']
        
        if not replace:
            existing_tags = snippet.get('tags', [])
            tags = list(set(existing_tags + tags))  # Merge and remove duplicates
        
        snippet['tags'] = tags
        
        request = service.videos().update(
            part='snippet',
            body={
                'id': video_id,
                'snippet': snippet
            }
        )
        request.execute()
        
        print(f"✓ Updated tags for video: {snippet.get('title', video_id)}")
        return True
    
    except HttpError as e:
        print(f"✗ Error updating tags for {video_id}: {e}")
        return False


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
        if not os.path.exists(thumbnail_path):
            print(f"Thumbnail file not found: {thumbnail_path}")
            return False
        
        request = service.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
        )
        request.execute()
        
        print(f"✓ Updated thumbnail for video: {video_id}")
        return True
    
    except HttpError as e:
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

def export_video_list(service, output_file: str = "videos_export.json"):
    """Export all video information to JSON file."""
    print("Exporting video list...")
    videos = get_all_videos(service)
    
    # Simplify video data for export
    export_data = []
    for video in videos:
        export_data.append({
            'id': video['id'],
            'title': video['snippet']['title'],
            'description': video['snippet'].get('description', ''),
            'tags': video['snippet'].get('tags', []),
            'publishedAt': video['snippet'].get('publishedAt', ''),
            'url': f"https://www.youtube.com/watch?v={video['id']}"
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported {len(export_data)} videos to {output_file}")


def search_videos_by_title(service, search_term: str) -> List[Dict]:
    """Search videos by title (case-insensitive)."""
    videos = get_all_videos(service)
    search_lower = search_term.lower()
    
    return [v for v in videos if search_lower in v['snippet']['title'].lower()]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Authenticate
    print("Authenticating with YouTube API...")
    service = get_authenticated_service()
    print("✓ Authentication successful\n")
    
    print("YouTube API Manager ready!")
    print("\nAvailable functions (uncomment to use):")
    print("=" * 60)
    
    # Example 1: Update description for all videos
    # Uncomment the lines below to update all video descriptions
    # new_description = "Check out my latest content! Subscribe for more!"
    # update_all_videos_description(service, new_description, append=True)
    
    # Example 2: Update description for specific videos
    # Uncomment the lines below to update specific videos
    # video_ids = ["VIDEO_ID_1", "VIDEO_ID_2"]
    # batch_update_descriptions(service, video_ids, "New description text")
    
    # Example 3: Add tags to a video
    # Uncomment the lines below to update video tags
    # update_video_tags(service, "VIDEO_ID", ["guitar", "music", "tutorial"], replace=False)
    
    # Example 4: Create playlist and add videos
    # Uncomment the lines below to create a playlist
    # playlist_id = create_playlist(service, "My New Playlist", "Playlist description")
    # add_video_to_playlist(service, playlist_id, "VIDEO_ID")
    
    # Example 5: Export all videos (read-only, safe to run)
    # Uncomment the line below to export video list to JSON
    # export_video_list(service)
    
    print("\nTo use these functions, uncomment the examples above or call them directly.")
    print("Nothing will run automatically - you must uncomment the code you want to execute.")

