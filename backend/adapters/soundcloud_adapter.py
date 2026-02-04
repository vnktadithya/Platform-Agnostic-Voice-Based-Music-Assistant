import os
import requests
import secrets
import hashlib
import base64
from typing import List, Tuple, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.adapters.adapter_base import MusicPlatformAdapter
from backend.models.database_models import UserPlaylist, UserLikedSong
from backend.utils.normalize_text import normalize_query
import logging
import json

logger = logging.getLogger(__name__)

class SoundCloudAdapter(MusicPlatformAdapter):
    """
    SoundCloud music platform adapter.
    Implements OAuth 2.0 PKCE flow and interacts with the official SoundCloud JSON API.
    """

    CAPABILITIES = {
        "playback_control": False,       
        "playlist_management": True,     
        "library_management": True,      
        "search": True,                 
        "recommendations": False,        
        "real_time_control": False,       
        "favorites_management": True,    
        "playlist_creation": True,       
        "voice_control": False,           
    }
    BASE_API_URL = "https://api.soundcloud.com"

    def __init__(self, access_token: str = None, **kwargs):
        if not access_token:
            raise ValueError("SoundCloudAdapter requires access_token")
        self.access_token = access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
    
    @staticmethod
    def _generate_pkce_pair() -> Tuple[str, str]:
        """Generates (code_verifier, code_challenge) for PKCE."""
        verifier = secrets.token_urlsafe(96) 
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(digest).decode('utf-8').replace('=', '')
        return verifier, challenge

    @staticmethod
    def get_auth_url() -> Tuple[str, str]:
        """
        Returns (auth_url, code_verifier).
        The caller MUST store code_verifier (e.g., in a cookie) to complete the flow.
        """
        client_id = os.getenv("SOUNDCLOUD_CLIENT_ID")
        redirect_uri = os.getenv("SOUNDCLOUD_REDIRECT_URI")
        
        verifier, challenge = SoundCloudAdapter._generate_pkce_pair()

        url = (
            "https://secure.soundcloud.com/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            f"&code_challenge={challenge}"
            "&code_challenge_method=S256"
            "&scope=non-expiring"
        )
        return url, verifier

    @staticmethod
    def handle_auth_callback(code: str, code_verifier: str) -> dict:
        token_url = "https://secure.soundcloud.com/oauth/token"

        payload = {
            "grant_type": "authorization_code",
            "client_id": os.getenv("SOUNDCLOUD_CLIENT_ID"),
            "client_secret": os.getenv("SOUNDCLOUD_CLIENT_SECRET"),
            "redirect_uri": os.getenv("SOUNDCLOUD_REDIRECT_URI"),
            "code": code,
            "code_verifier": code_verifier
        }

        token_resp = requests.post(token_url, data=payload)
        token_resp.raise_for_status()
        token_data = token_resp.json()

        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me = requests.get("https://api.soundcloud.com/me", headers=headers).json()

        # Calculate expiration
        expires_in = token_data.get("expires_in", 3600)
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()

        return {
            "platform_user_id": str(me["id"]),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "meta_data": {
                "username": me.get("username"),
                "avatar": me.get("avatar_url"),
                "email": me.get("email") or me.get("email_address"),
                "expires_at": expires_at,
                "scope": token_data.get("scope")
            }
        }

    # ---------------- Library Management ----------------


    def fetch_liked_tracks(self, limit: int = 50) -> List[dict]:
        """
        Fetches liked tracks, utilizing pagination to retrieve the full list.
        The 'limit' argument controls the batch size per request.
        """
        tracks = []
        next_href = f"{self.BASE_API_URL}/me/likes/tracks"
        params = {"limit": limit} 
        
        MAX_PAGES = 50 
        page_count = 0

        while next_href and page_count < MAX_PAGES:
            logger.info(f"Fetching SoundCloud Liked Tracks Page {page_count + 1}...")
            
            try:
                if page_count == 0:
                    resp = requests.get(next_href, headers=self._headers(), params=params)
                else:
                    resp = requests.get(next_href, headers=self._headers())
                
                resp.raise_for_status()
                data = resp.json()
                
                collection = []
                if isinstance(data, list):
                    collection = data
                    next_href = None 
                elif isinstance(data, dict):
                     collection = data.get("collection", [])
                     next_href = data.get("next_href")
                else:
                    logger.warning(f"Unexpected SoundCloud response structure: {type(data)}")
                    break

                if not collection:
                    break

                for item in collection:
                    track = item.get("track", item)
                    user = track.get("user", {})
                    
                    tracks.append({
                        "uri": f"soundcloud:track:{track.get('id')}",
                        "meta_data": {
                            "title": track.get("title", "Unknown Title"),
                            "artist": user.get("username", "Unknown Artist"),
                            "duration_ms": track.get("duration", 0),
                            "artwork": track.get("artwork_url") or user.get("avatar_url"),
                        }
                    })
                
                page_count += 1
                
            except Exception as e:
                logger.error(f"Error fetching SoundCloud likes page {page_count}: {e}")
                break
                
        logger.info(f"Fetched total {len(tracks)} liked tracks from SoundCloud.")
        return tracks

    # ---------------- Playlists Management----------------

    def fetch_user_playlists(self) -> List[dict]:
        resp = requests.get(
            f"{self.BASE_API_URL}/me/playlists",
            headers=self._headers()
        )
        resp.raise_for_status()

        playlists = []
        data = resp.json()
        
        collection = []
        if isinstance(data, list):
            collection = data
        elif isinstance(data, dict) and "collection" in data:
             collection = data["collection"]
        else:
             print(f"DEBUG: Unexpected SoundCloud playlist response: {type(data)} - {data}")
             return []

        for pl in collection:
            playlist = pl.get("playlist", pl)
            
            if not playlist.get("id"):
                continue

            playlists.append({
                "id": str(playlist["id"]),
                "name": playlist.get("title", f"Playlist {playlist['id']}"),
                "description": playlist.get("description", ""),
                "owner": {"display_name": playlist.get("user", {}).get("username", "")},
                "tracks": {"total": playlist.get("track_count", len(playlist.get("tracks", [])))},
                "images": [{"url": playlist.get("artwork_url")}] if playlist.get("artwork_url") else []
            })
        return playlists

    def create_playlist(self, db: Session, platform_account_id: int, user_id: str, name: str, description: str = ""):
        payload = {
            "playlist": {
                "title": name,
                "description": description,
                "sharing": "public"
            }
        }

        resp = requests.post(
            f"{self.BASE_API_URL}/playlists",
            headers=self._headers(),
            json=payload
        )
        resp.raise_for_status()
        playlist_data = resp.json()        

        if playlist_data:
             new_playlist = UserPlaylist(
                platform_account_id=platform_account_id,
                playlist_id=str(playlist_data['id']),
                name=playlist_data['title'],
                meta_data={
                    "normalized_name": normalize_query(playlist_data['title']),
                    "description": playlist_data.get("description", ""),
                    "owner": playlist_data.get("user", {}).get("username", ""),
                    "track_count": playlist_data.get("track_count", 0),
                    "image": playlist_data.get("artwork_url")
                }
            )
             db.add(new_playlist)
             db.commit()
             logger.info(f"Successfully cached new SoundCloud playlist '{name}' in DB.")

        return playlist_data

    # ---------------- Search ----------------

    def search_track_uris(self, db: Session, platform_account_id: int, query: str, limit: int = 1) -> List[str]:
        resp = requests.get(
            f"{self.BASE_API_URL}/tracks",
            headers=self._headers(),
            params={"q": query, "limit": limit}
        )
        resp.raise_for_status()

        return [f"soundcloud:track:{t['id']}" for t in resp.json()]

    def play_by_query(self, db: Session, platform_account_id: int, query: str, limit: int = 5):
        """
        Since SoundCloud doesn't support remote playback, we search and return the track info
        effectively acting as a 'resolve' step.
        """
        # Search for the track
        resp = requests.get(
            f"{self.BASE_API_URL}/tracks",
            headers=self._headers(),
            params={"q": query, "limit": 1}
        )
        resp.raise_for_status()
        results = resp.json()
        
        if not results:
            return "No track found on SoundCloud matching that query."

        track = results[0]
        
        # Return structured data for Frontend Player
        return {
            "message": f"Playing {track['title']} by {track['user']['username']} on SoundCloud.",
            "track_info": {
                "title": track['title'],
                "subtitle": track['user']['username'],
                "type": "song",
                "image": track.get("artwork_url") or track.get("user", {}).get("avatar_url"),
                "permalink_url": track["permalink_url"], # Critical for Widget
                "uri": track["uri"]
            }
        }

    def play_playlist_by_name(self, db: Session, platform_account_id: int, playlist_name: str):
        # 1. Search for playlist
        resp = requests.get(
            f"{self.BASE_API_URL}/me/playlists",
            headers=self._headers()
        )
        resp.raise_for_status()
        playlists = resp.json()
        
        target = None
        for pl in playlists:
            if playlist_name.lower() in pl["title"].lower():
                target = pl
                break
        
        if not target:
            return f"Could not find a playlist named '{playlist_name}' on SoundCloud."
            
        return f"Playing playlist {target['title']} on SoundCloud."

    def delete_user_playlist(self, db: Session, platform_account_id: int, playlist_name: str):
        # 1. Resolve ID
        playlist_id = self.resolve_playlist_id(db, platform_account_id, playlist_name)
        if not playlist_id:
             return f"Could not find playlist '{playlist_name}' to delete."

        # 2. Delete
        resp = requests.delete(
            f"{self.BASE_API_URL}/playlists/{playlist_id}",
            headers=self._headers()
        )
        if resp.status_code == 404:
             return f"Playlist {playlist_name} not found."
        resp.raise_for_status()
        
        # 3. Delete from DB
        
        playlist_entry = db.query(UserPlaylist).filter_by(
            platform_account_id=platform_account_id,
            playlist_id=playlist_id
        ).first()

        if playlist_entry:
            db.delete(playlist_entry)
            db.commit()
            logger.info(f"Deleted playlist '{playlist_name}' from local DB.")

        return f"Deleted SoundCloud playlist: {playlist_name}"

    def resolve_playlist_id(self, db: Session, platform_account_id: int, playlist_name: str) -> Optional[str]:
        """Helper to find playlist ID by name."""
        resp = requests.get(
            f"{self.BASE_API_URL}/me/playlists",
            headers=self._headers()
        )
        if resp.status_code != 200:
            return None
        
        playlists = resp.json()
        for pl in playlists:
            if playlist_name.lower() in pl["title"].lower():
                return str(pl["id"])
        return None

    def add_tracks_to_playlist(self, db: Session, platform_account_id: int, playlist_id: str, track_uris: List[str]):
        """
        Adds tracks to a playlist. 
        Note: SoundCloud API requires sending the FULL list of tracks.
        """
        if not playlist_id:
            return "Playlist ID is missing."
            
        # 1. Fetch current
        resp = requests.get(
            f"{self.BASE_API_URL}/playlists/{playlist_id}",
            headers=self._headers()
        )
        if resp.status_code == 404:
            raise Exception("Playlist not found.")
        resp.raise_for_status()
        
        current_playlist = resp.json()
        current_tracks = current_playlist.get("tracks", [])
        
        # 2. Build track list
        track_list = []
        for t in current_tracks:
            track_list.append({"id": str(t.get("id"))})
        
        # Append new tracks
        added_count = 0
        for uri in track_uris:
            try:
                tid = uri.split(":")[-1]
                track_list.append({"id": str(tid)})
                added_count += 1
            except ValueError:
                continue
                
        # 3. Update Playlist
        playlist_update = {
            "title": current_playlist.get("title"),
            "tracks": track_list
        }
        
        final_payload = {
            "playlist": playlist_update
        }
        
        logger.info(f"DEBUG: Playlist Payload: {json.dumps(final_payload)}")
        
        headers = self._headers()
        headers["Content-Type"] = "application/json"

        resp = requests.put(
            f"{self.BASE_API_URL}/playlists/{playlist_id}",
            headers=headers,
            data=json.dumps(final_payload)
        )
        
        if resp.status_code != 200:
             error_msg = f"Failed to add tracks: {resp.status_code} - {resp.text}"
             logger.error(f"DEBUG: SC API Error: {error_msg}")
             raise Exception(error_msg)
             
        resp.raise_for_status()
        
        playlist = db.query(UserPlaylist).filter_by(
            platform_account_id=platform_account_id, 
            playlist_id=playlist_id
        ).first()
        
        if playlist:
            new_count = len(track_list)
            meta = dict(playlist.meta_data or {})
            meta["track_count"] = new_count
            playlist.meta_data = meta
            db.commit()
            logger.info(f"Updated SC playlist {playlist_id} track count to {new_count}")

        return f"Added {added_count} track(s) to playlist."


    def remove_tracks_from_playlist(self, db: Session, platform_account_id: int, playlist_id: str, track_uris: List[str]):
        """
        Removes tracks from a playlist.
        """
        if not playlist_id:
            return "Playlist ID is missing."
            
        # 1. Fetch current
        resp = requests.get(
            f"{self.BASE_API_URL}/playlists/{playlist_id}",
            headers=self._headers()
        )
        if resp.status_code == 404:
            raise Exception("Playlist not found.")
        resp.raise_for_status()
        
        current_playlist = resp.json()
        current_tracks = current_playlist.get("tracks", [])
        
        # 2. Filter out keys
        ids_to_remove = set()
        for uri in track_uris:
            try:
                # URI: soundcloud:track:123
                ids_to_remove.add(str(uri.split(":")[-1]))
            except ValueError:
                continue
                
        new_track_list = []
        removed_count = 0
        
        for t in current_tracks:
            tid = str(t.get("id"))
            
            if tid in ids_to_remove:
                removed_count += 1
                continue 
                
            new_track_list.append({"id": tid})
            
        if removed_count == 0:
            return "None of the specified tracks were found in the playlist."

        # 3. Update
        playlist_update = {
             "title": current_playlist.get("title"),
             "tracks": new_track_list
        }
        
        logger.info(f"DEBUG: Playlist Remove Payload: {json.dumps(playlist_update)}")

        final_payload = {
            "playlist": playlist_update
        }
        
        headers = self._headers()
        headers["Content-Type"] = "application/json"

        resp = requests.put(
            f"{self.BASE_API_URL}/playlists/{playlist_id}",
            headers=headers,
            data=json.dumps(final_payload)
        )
        
        if resp.status_code != 200:
             error_msg = f"Failed to remove tracks: {resp.status_code} - {resp.text}"
             logger.error(f"DEBUG: SC API Error: {error_msg}")
             raise Exception(error_msg)
             
        resp.raise_for_status()
        
        playlist = db.query(UserPlaylist).filter_by(
            platform_account_id=platform_account_id, 
            playlist_id=playlist_id
        ).first()
        
        if playlist:
             new_count = len(new_track_list)
             meta = dict(playlist.meta_data or {})
             meta["track_count"] = new_count
             playlist.meta_data = meta
             db.commit()
        
        return f"Removed {removed_count} track(s) from playlist."

    # ---------------- Favorites ----------------
    
    def play_liked_songs(self, db: Session, platform_account_id: int):
        """
        Plays the user's liked songs (starts with the most recent one).
        """
        resp = requests.get(
            f"{self.BASE_API_URL}/me/likes/tracks",
            headers=self._headers(),
            params={"limit": 1}
        )
        resp.raise_for_status()
        data = resp.json()
        
        collection = []
        if isinstance(data, list):
            collection = data
        elif isinstance(data, dict):
            collection = data.get("collection", [])
            
        if not collection:
            return "You have no liked songs on SoundCloud."
            
        item = collection[0]
        track = item.get("track", item)
        user = track.get("user", {})

        return {
            "message": f"Playing your liked songs from SoundCloud. Starting with {track.get('title')}.",
            "track_info": {
                "title": track.get("title"),
                "subtitle": user.get("username"),
                "type": "song",
                "image": track.get("artwork_url") or user.get("avatar_url"),
                "permalink_url": track.get("permalink_url"),
                "uri": f"soundcloud:track:{track.get('id')}"
            }
        }

    def add_track_to_favorites(self, db: Session, platform_account_id: int, track_id: str):
        # Per PDF: POST https://api.soundcloud.com/likes/tracks/TRACK_ID
        resp = requests.post(
            f"{self.BASE_API_URL}/likes/tracks/{track_id}",
            headers=self._headers()
        )
        if resp.status_code == 404:
            raise Exception("Track not found.")
        resp.raise_for_status()
        
        # Check if exists first
        track_uri = f"soundcloud:track:{track_id}"
        existing = db.query(UserLikedSong).filter_by(
            platform_account_id=platform_account_id,
            track_uri=track_uri
        ).first()

        if existing:
            logger.info(f"Track already exists in DB cache: {track_id}")
            return "Added to Liked Songs (Already cached)."

        # Fetch metadata for cache
        try:
            track_resp = requests.get(
                f"{self.BASE_API_URL}/tracks/{track_id}",
                headers=self._headers()
            )
            track_resp.raise_for_status()
            track = track_resp.json()
            
            user = track.get("user", {})
            
            db.add(UserLikedSong(
                platform_account_id=platform_account_id,
                track_uri=track_uri,
                meta_data={
                    "track_name": track.get("title", ""),
                    "artist": user.get("username", ""),
                    "album_name": "",
                    "duration_ms": track.get("duration", 0),
                    "image": track.get("artwork_url")
                }
            ))
            db.commit()
            logger.info(f"Cached liked song '{track.get('title')}' to DB.")
            
        except Exception as e:
            logger.error(f"Failed to cache liked song metadata: {e}")
            
        return "Added to Liked Songs."

    def remove_track_from_favorites(self, db: Session, platform_account_id: int, track_id: str):
        resp = requests.delete(
            f"{self.BASE_API_URL}/likes/tracks/{track_id}",
            headers=self._headers()
        )
        if resp.status_code == 404:
            raise Exception("Track not found in favorites.")
        resp.raise_for_status()
        
        track_uri = f"soundcloud:track:{track_id}"
        existing = db.query(UserLikedSong).filter_by(
            platform_account_id=platform_account_id,
            track_uri=track_uri
        ).first()
        
        if existing:
            db.delete(existing)
            db.commit()
            logger.info(f"Removed soundcloud:track:{track_id} from local cache.")

        return "Removed from Liked Songs."
