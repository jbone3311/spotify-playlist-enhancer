"""
Core functionality for Spotify Playlist Enhancer.
Handles authentication, Spotify API interactions, and analysis.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import requests
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback')

@dataclass
class PlaylistInfo:
    """Container for playlist metadata."""
    id: str
    name: str
    track_count: int

@dataclass
class TrackMetadata:
    """Container for track metadata including when it was added."""
    uri: str
    added_at: str
    track: dict
    genres: List[str] = None  # Add genres field

def verify_env_variables() -> None:
    """Verify and log environment variables."""
    load_dotenv()
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    logger.info("Environment Variables Status:")
    logger.info(f"SPOTIFY_CLIENT_ID: {'✓ Set' if client_id else '✗ Missing'}")
    logger.info(f"SPOTIFY_CLIENT_SECRET: {'✓ Set' if client_secret else '✗ Missing'}")
    logger.info(f"REDIRECT_URI: {REDIRECT_URI}")
    
    if not client_id or not client_secret:
        raise ValueError("Missing required environment variables. Please check your .env file.")

def init_spotify_client() -> spotipy.Spotify:
    """
    Initialize and return an authenticated Spotify client.
    
    Returns:
        spotipy.Spotify: Authenticated client instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    verify_env_variables()
    
    scope = [
        'playlist-read-private',
        'playlist-modify-private',
        'user-library-read',
        'user-library-modify',
        'user-read-private',
        'user-read-email',
        'user-top-read',
        'user-read-recently-played',
        'user-read-currently-playing',
        'user-read-playback-state',
        'user-modify-playback-state',
        'streaming',
        'app-remote-control',
        'user-read-playback-position'
    ]
    
    try:
        logger.info("Initializing Spotify client with:")
        logger.info(f"Client ID: {os.getenv('SPOTIFY_CLIENT_ID')[:8]}...")
        logger.info(f"Redirect URI: {REDIRECT_URI}")
        logger.info(f"Scopes: {', '.join(scope)}")
        
        auth_manager = SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=REDIRECT_URI,
            scope=scope,
            cache_handler=None  # Disable caching to force new token
        )
        
        # Force token refresh
        if not auth_manager.get_cached_token():
            logger.info("No cached token found, requesting new token...")
            auth_manager.get_access_token()
        
        client = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Successfully initialized Spotify client")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        raise

def fetch_user_playlists(client: spotipy.Spotify) -> List[PlaylistInfo]:
    """Fetch all user playlists using Spotipy's public methods."""
    playlists = []
    offset = 0
    limit = 50
    while True:
        try:
            response = client.current_user_playlists(limit=limit, offset=offset)
            items = response.get('items', [])
            for item in items:
                playlists.append(PlaylistInfo(
                    id=item['id'],
                    name=item['name'],
                    track_count=item['tracks']['total']
                ))
            logger.info(f"Fetched {len(items)} playlists at offset {offset}")
            if len(items) < limit:
                break
            offset += limit
        except Exception as e:
            logger.error(f"Error fetching playlists: {e}")
            logger.error(traceback.format_exc())
            break
    return playlists

def fetch_playlist_tracks_with_metadata(client: spotipy.Spotify, playlist_id: str) -> List[TrackMetadata]:
    """Fetch all tracks from a playlist using Spotipy's public methods."""
    tracks = []
    offset = 0
    limit = 100
    while True:
        try:
            response = client.playlist_items(playlist_id, limit=limit, offset=offset)
            items = response.get('items', [])
            for item in items:
                if item['track']:  # Skip None tracks
                    tracks.append(TrackMetadata(
                        uri=item['track']['uri'],
                        added_at=item['added_at'],
                        track=item['track']
                    ))
            logger.info(f"Fetched {len(items)} tracks at offset {offset}")
            if len(items) < limit:
                break
            offset += limit
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {e}")
            logger.error(traceback.format_exc())
            break
    return tracks

def fetch_liked_tracks(client: spotipy.Spotify) -> List[str]:
    """Fetch all liked tracks using Spotipy's public methods."""
    track_uris = []
    offset = 0
    limit = 50
    while True:
        try:
            response = client.current_user_saved_tracks(limit=limit, offset=offset)
            items = response.get('items', [])
            for item in items:
                if item['track']:  # Skip None tracks
                    track_uris.append(item['track']['uri'])
            logger.info(f"Fetched {len(items)} liked tracks at offset {offset}")
            if len(items) < limit:
                break
            offset += limit
        except Exception as e:
            logger.error(f"Error fetching liked tracks: {e}")
            logger.error(traceback.format_exc())
            break
    return track_uris

def get_playlist_track_uris(client: spotipy.Spotify, playlist_id: str) -> List[str]:
    """
    Fetch all track URIs from a specific playlist.
    
    Args:
        client: Authenticated Spotify client
        playlist_id: Spotify playlist ID
        
    Returns:
        List[str]: List of track URIs
    """
    tracks = []
    offset = 0
    limit = 100
    
    while True:
        try:
            results = client.playlist_items(
                playlist_id,
                limit=limit,
                offset=offset,
                fields='items.track.uri'
            )
            
            if not results['items']:
                break
                
            for item in results['items']:
                if item['track']:  # Skip None tracks
                    tracks.append(item['track']['uri'])
            
            offset += limit
            if len(results['items']) < limit:
                break
                
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {e}")
            break
    
    logger.info(f"Fetched {len(tracks)} tracks from playlist {playlist_id}")
    return tracks

def get_spotify_token(client) -> str:
    """Return the current access token from a Spotipy client."""
    try:
        token = client._auth_manager.get_access_token(as_dict=False)
        logger.info(f"Fetched access token from Spotipy client: {token[:10]}...")
        return token
    except Exception as e:
        logger.error(f"Failed to get access token from Spotipy client: {e}")
        return None

def fetch_audio_features(client: spotipy.Spotify, track_uris: List[str]) -> Dict[str, dict]:
    """Fetch audio features for a list of track URIs using Spotipy's built-in method."""
    logger.info(f"Input track_uris type: {type(track_uris)}")
    logger.info(f"Input track_uris length: {len(track_uris)}")
    logger.info(f"First few track_uris: {track_uris[:3]}")
    
    if not track_uris:
        logger.warning("No track URIs provided")
        return {}
        
    if not isinstance(track_uris, list):
        track_uris = list(track_uris)
        logger.info(f"Converted track_uris to list. New type: {type(track_uris)}")
        
    track_ids = [uri.split(':')[-1] for uri in track_uris]
    logger.info(f"Track IDs type: {type(track_ids)}")
    logger.info(f"Track IDs length: {len(track_ids)}")
    logger.info(f"First few track IDs: {track_ids[:3]}")
    
    batch_size = 100
    features_map = {}
    
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}")
        logger.info(f"Batch type: {type(batch)}")
        logger.info(f"Batch length: {len(batch)}")
        logger.info(f"First few batch items: {batch[:3]}")
        
        try:
            # Get access token for debugging
            token = client._auth_manager.get_access_token()
            logger.info(f"Fetched access token from Spotipy client: {token[:10]}...")
            logger.info(f"Got token: {token[:10]}...")
            
            results = client.audio_features(batch)
            if results:
                # Map features to track URIs
                for track_id, features in zip(batch, results):
                    if features:  # Skip None features
                        track_uri = f"spotify:track:{track_id}"
                        features_map[track_uri] = features
                logger.info(f"Successfully fetched features for batch {i//batch_size + 1}")
            else:
                logger.warning(f"No features returned for batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error fetching audio features for batch: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Log response details if available
            if hasattr(e, 'response'):
                logger.error(f"API Response status: {e.response.status_code}")
                logger.error(f"API Response headers: {e.response.headers}")
                try:
                    logger.error(f"Error response from Spotify API: {e.response.json()}")
                except:
                    logger.error("Could not parse error response as JSON")
            
            continue
            
    return features_map

def fetch_artist_genres(client: spotipy.Spotify, artist_ids: List[str]) -> Dict[str, List[str]]:
    """Fetch genres for a list of artist IDs using Spotipy's public methods."""
    genres = {}
    if not artist_ids:
        return genres
    if isinstance(artist_ids, set):
        artist_ids = list(artist_ids)
    batch_size = 50
    for i in range(0, len(artist_ids), batch_size):
        batch = artist_ids[i:i + batch_size]
        try:
            response = client.artists(batch)
            for artist in response.get('artists', []):
                genres[artist['id']] = artist.get('genres', [])
        except Exception as e:
            logger.error(f"Error fetching genres for artist batch: {e}")
            logger.error(traceback.format_exc())
            continue
    return genres 