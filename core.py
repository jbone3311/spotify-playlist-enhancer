"""
Core functionality for Spotify Playlist Enhancer.
Handles authentication, Spotify API interactions, and analysis.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PlaylistInfo:
    """Container for playlist metadata."""
    id: str
    name: str
    track_count: int

def init_spotify_client() -> spotipy.Spotify:
    """
    Initialize and return an authenticated Spotify client.
    
    Returns:
        spotipy.Spotify: Authenticated client instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    load_dotenv()
    
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    scope = [
        'playlist-read-private',
        'playlist-modify-private',
        'user-library-read',
        'user-library-modify'
    ]
    
    try:
        client = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope=scope
        ))
        logger.info("Successfully initialized Spotify client")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        raise

def fetch_user_playlists(client: spotipy.Spotify) -> List[PlaylistInfo]:
    """
    Fetch all playlists for the authenticated user.
    
    Args:
        client: Authenticated Spotify client
        
    Returns:
        List[PlaylistInfo]: List of playlist metadata
    """
    playlists = []
    offset = 0
    limit = 50
    
    while True:
        try:
            results = client.current_user_playlists(limit=limit, offset=offset)
            if not results['items']:
                break
                
            for item in results['items']:
                playlists.append(PlaylistInfo(
                    id=item['id'],
                    name=item['name'],
                    track_count=item['tracks']['total']
                ))
            
            offset += limit
            if len(results['items']) < limit:
                break
                
        except Exception as e:
            logger.error(f"Error fetching playlists: {e}")
            break
    
    logger.info(f"Fetched {len(playlists)} playlists")
    return playlists

def fetch_liked_tracks(client: spotipy.Spotify) -> List[str]:
    """
    Fetch all liked track URIs for the authenticated user.
    
    Args:
        client: Authenticated Spotify client
        
    Returns:
        List[str]: List of track URIs
    """
    tracks = []
    offset = 0
    limit = 50
    
    while True:
        try:
            results = client.current_user_saved_tracks(limit=limit, offset=offset)
            if not results['items']:
                break
                
            for item in results['items']:
                tracks.append(item['track']['uri'])
            
            offset += limit
            if len(results['items']) < limit:
                break
                
        except Exception as e:
            logger.error(f"Error fetching liked tracks: {e}")
            break
    
    logger.info(f"Fetched {len(tracks)} liked tracks")
    return tracks

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

def fetch_audio_features(client: spotipy.Spotify, track_uris: List[str]) -> Dict[str, dict]:
    """
    Fetch audio features for a batch of tracks.
    
    Args:
        client: Authenticated Spotify client
        track_uris: List of track URIs
        
    Returns:
        Dict[str, dict]: Map of track URI to audio features
    """
    features = {}
    batch_size = 100
    
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        try:
            results = client.audio_features(batch)
            for uri, feature in zip(batch, results):
                if feature:  # Skip None features
                    features[uri] = feature
        except Exception as e:
            logger.error(f"Error fetching audio features: {e}")
            continue
    
    logger.info(f"Fetched audio features for {len(features)} tracks")
    return features 