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

# Constants
REDIRECT_URI = "http://127.0.0.1:8888/callback"

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
        'user-read-playback-position',
        'user-read-private'  # Required for audio features
    ]
    
    try:
        logger.info("Initializing Spotify client with:")
        logger.info(f"Client ID: {os.getenv('SPOTIFY_CLIENT_ID')[:8]}...")
        logger.info(f"Redirect URI: {REDIRECT_URI}")
        logger.info(f"Scopes: {', '.join(scope)}")
        
        client = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=REDIRECT_URI,
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
    Fetch audio features for a batch of tracks using Spotipy's official method.
    Args:
        client: Authenticated Spotify client
        track_uris: List of track URIs
    Returns:
        Dict[str, dict]: Map of track URI to audio features
    """
    features = {}
    batch_size = 100  # Spotify's limit for audio-features endpoint
    logger.info(f"Starting to fetch audio features for {len(track_uris)} tracks")
    # Log the access token (first 10 chars for security)
    token = client._auth_manager.get_access_token()
    logger.info(f"Access token: {token[:10]}...")
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        try:
            track_ids = [uri.split(':')[-1] for uri in batch]
            logger.info(f"Processing batch {i//batch_size + 1} of {(len(track_uris) + batch_size - 1) // batch_size}")
            logger.info(f"Sample track IDs: {track_ids[:3]}")
            results = client.audio_features(track_ids)
            if not results:
                logger.warning(f"No results returned for batch {i//batch_size + 1}")
                continue
            logger.info(f"Received {len(results)} feature sets for batch {i//batch_size + 1}")
            if results:
                logger.info(f"Sample feature set: {results[0]}")
            for uri, feature in zip(batch, results):
                if feature:
                    features[uri] = feature
                else:
                    logger.warning(f"No features available for track {uri}")
        except Exception as e:
            logger.error(f"Error fetching audio features for batch {i//batch_size + 1}: {str(e)}")
            logger.error(f"First track ID in batch: {track_ids[0] if track_ids else 'None'}")
            # Log the full error response if available
            if hasattr(e, 'response'):
                logger.error(f"Full error response: {e.response.text}")
            raise
    logger.info(f"Successfully fetched features for {len(features)} tracks")
    return features

def fetch_artist_genres(client: spotipy.Spotify, artist_ids: List[str]) -> Dict[str, List[str]]:
    """
    Fetch genres for a list of artists using Spotipy's official method.
    Args:
        client: Authenticated Spotify client
        artist_ids: List of Spotify artist IDs
    Returns:
        Dict[str, List[str]]: Map of artist ID to list of genres
    """
    genres = {}
    batch_size = 50  # Spotify's limit for artists endpoint
    # Log the access token (first 10 chars for security)
    token = client._auth_manager.get_access_token()
    logger.info(f"Access token: {token[:10]}...")
    for i in range(0, len(artist_ids), batch_size):
        batch = artist_ids[i:i + batch_size]
        try:
            results = client.artists(batch)
            if not results or 'artists' not in results:
                logger.warning(f"No results returned for artist batch {i//batch_size + 1}")
                continue
            for artist in results['artists']:
                if artist:
                    genres[artist['id']] = artist.get('genres', [])
                else:
                    logger.warning(f"No artist data available for ID in batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error fetching artist genres: {e}")
            # Log the full error response if available
            if hasattr(e, 'response'):
                logger.error(f"Full error response: {e.response.text}")
            continue
    return genres

def fetch_playlist_tracks_with_metadata(client: spotipy.Spotify, playlist_id: str) -> List[TrackMetadata]:
    """
    Fetch all tracks from a playlist with metadata including when they were added.
    Uses the Spotify Web API playlist-tracks endpoint.
    
    Args:
        client: Authenticated Spotify client
        playlist_id: Spotify playlist ID
        
    Returns:
        List[TrackMetadata]: List of track metadata including when they were added
    """
    tracks = []
    offset = 0
    limit = 100  # Spotify's limit for playlist-tracks endpoint
    
    while True:
        try:
            # Use the playlist-tracks endpoint with fields parameter
            results = client._get(
                f"playlists/{playlist_id}/tracks",
                limit=limit,
                offset=offset,
                fields='items(added_at,track)'
            )
            
            if not results or 'items' not in results:
                break
                
            # Collect all artist IDs
            artist_ids = set()
            for item in results['items']:
                if item['track']:  # Skip None tracks
                    for artist in item['track']['artists']:
                        artist_ids.add(artist['id'])
            
            # Fetch genres for all artists
            artist_genres = fetch_artist_genres(client, list(artist_ids))
            
            # Create track metadata with genres
            for item in results['items']:
                if item['track']:  # Skip None tracks
                    # Get all genres from all artists of the track
                    track_genres = set()
                    for artist in item['track']['artists']:
                        track_genres.update(artist_genres.get(artist['id'], []))
                    
                    tracks.append(TrackMetadata(
                        uri=item['track']['uri'],
                        added_at=item['added_at'],
                        track=item['track'],
                        genres=sorted(list(track_genres))  # Convert set to sorted list
                    ))
            
            offset += limit
            if len(results['items']) < limit:
                break
                
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {e}")
            break
    
    logger.info(f"Fetched {len(tracks)} tracks with metadata from playlist {playlist_id}")
    return tracks 