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
    
    logger.info("Starting to fetch user playlists...")
    logger.info(f"Using client: {client}")
    
    try:
        # First, verify we can access the user's profile
        user = client.current_user()
        logger.info(f"Successfully authenticated as user: {user['id']}")
        
        while True:
            try:
                logger.info(f"Fetching playlists batch: offset={offset}, limit={limit}")
                results = client.current_user_playlists(limit=limit, offset=offset)
                
                if not results:
                    logger.warning("No results returned from current_user_playlists")
                    break
                    
                if 'items' not in results:
                    logger.error(f"Unexpected response format: {results}")
                    break
                    
                if not results['items']:
                    logger.info("No more playlists to fetch")
                    break
                    
                logger.info(f"Received {len(results['items'])} playlists in this batch")
                
                for item in results['items']:
                    try:
                        playlist = PlaylistInfo(
                            id=item['id'],
                            name=item['name'],
                            track_count=item['tracks']['total']
                        )
                        logger.info(f"Found playlist: {playlist.name} (ID: {playlist.id}, Tracks: {playlist.track_count})")
                        playlists.append(playlist)
                    except KeyError as e:
                        logger.error(f"Missing key in playlist data: {e}")
                        logger.error(f"Playlist data: {item}")
                        continue
                
                offset += limit
                if len(results['items']) < limit:
                    logger.info("Reached end of playlist list")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching playlist batch: {e}")
                if hasattr(e, 'response'):
                    logger.error(f"Error response status: {e.response.status_code}")
                    logger.error(f"Error response headers: {e.response.headers}")
                    logger.error(f"Error response body: {e.response.text}")
                break
        
        logger.info(f"Successfully fetched {len(playlists)} playlists")
        return playlists
        
    except Exception as e:
        logger.error(f"Error in fetch_user_playlists: {e}")
        if hasattr(e, 'response'):
            logger.error(f"Error response status: {e.response.status_code}")
            logger.error(f"Error response headers: {e.response.headers}")
            logger.error(f"Error response body: {e.response.text}")
        raise

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

def get_spotify_token(client) -> str:
    """Return the current access token from a Spotipy client."""
    try:
        token = client._auth_manager.get_access_token(as_dict=False)
        logger.info(f"Fetched access token from Spotipy client: {token[:10]}...")
        return token
    except Exception as e:
        logger.error(f"Failed to get access token from Spotipy client: {e}")
        return None

def fetch_audio_features(client, track_uris: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch audio features for a list of track URIs using a Spotipy client for authentication."""
    logger.info(f"Input track_uris type: {type(track_uris)}")
    logger.info(f"Input track_uris length: {len(track_uris)}")
    logger.info(f"First few input track_uris: {track_uris[:3]}")
    
    if not isinstance(track_uris, list):
        logger.warning(f"Converting track_uris from {type(track_uris)} to list")
        track_uris = list(track_uris)
    
    logger.info(f"Starting to fetch audio features for {len(track_uris)} tracks")
    
    token = get_spotify_token(client)
    if not token:
        logger.error("Failed to get authentication token")
        return {}
    
    logger.info(f"Got token: {token[:10]}...")
    
    features = {}
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i + 100]
        logger.info(f"Processing batch {i//100 + 1}")
        logger.info(f"Batch type: {type(batch)}")
        logger.info(f"Batch length: {len(batch)}")
        logger.info(f"First few batch items: {batch[:3]}")
        
        track_ids = [uri.split(':')[-1] for uri in batch]
        logger.info(f"Track IDs type: {type(track_ids)}")
        logger.info(f"Track IDs length: {len(track_ids)}")
        logger.info(f"First few track IDs: {track_ids[:3]}")
        
        try:
            response = requests.get(
                'https://api.spotify.com/v1/audio-features',
                headers={'Authorization': f'Bearer {token}'},
                params={'ids': ','.join(track_ids)}
            )
            logger.info(f"API Response status: {response.status_code}")
            logger.info(f"API Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Raw API response: {data}")
                for track_id, track_features in zip(track_ids, data.get('audio_features', [])):
                    if track_features:
                        features[track_id] = track_features
            else:
                logger.error(f"Error response from Spotify API: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching audio features for batch: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
    
    return features

def fetch_artist_genres(client: spotipy.Spotify, artist_ids: List[str]) -> Dict[str, List[str]]:
    """Fetch genres for a list of artist IDs."""
    # Debug logging for input
    logger.info(f"Input artist_ids type: {type(artist_ids)}")
    logger.info(f"Input artist_ids length: {len(artist_ids)}")
    logger.info(f"First few input artist_ids: {artist_ids[:3] if isinstance(artist_ids, list) else 'Not a list'}")
    
    if not artist_ids:
        return {}
    
    # Convert to list if it's a set
    if isinstance(artist_ids, set):
        logger.warning(f"artist_ids is type {type(artist_ids)}, converting to list.")
        artist_ids = list(artist_ids)
        logger.info(f"Converted artist_ids type: {type(artist_ids)}")
        logger.info(f"Converted artist_ids length: {len(artist_ids)}")
    
    genres = {}
    # Process in batches of 50 (Spotify's limit)
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i + 50]
        logger.info(f"Batch type before processing: {type(batch)}")
        logger.info(f"Batch length before processing: {len(batch)}")
        
        if not isinstance(batch, list):
            logger.warning(f"batch is type {type(batch)}, converting to list.")
            batch = list(batch)
            logger.info(f"Converted batch type: {type(batch)}")
            logger.info(f"Converted batch length: {len(batch)}")
        
        try:
            artists = client.artists(batch)
            for artist in artists['artists']:
                if artist and 'id' in artist and 'genres' in artist:
                    genres[artist['id']] = artist['genres']
        except Exception as e:
            logger.error(f"Error fetching genres for artists batch: {str(e)}")
            continue
    return genres

def fetch_playlist_tracks_with_metadata(client: spotipy.Spotify, playlist_id: str) -> List[TrackMetadata]:
    """Fetch tracks from a playlist with full metadata and return a list of TrackMetadata objects."""
    logger.info(f"Starting to fetch tracks for playlist {playlist_id}")
    tracks = []
    offset = 0
    limit = 100
    
    try:
        # First verify we can access the playlist
        playlist = client.playlist(playlist_id)
        logger.info(f"Successfully accessed playlist: {playlist['name']}")
        
        while True:
            logger.info(f"Fetching tracks batch: offset={offset}, limit={limit}")
            results = client.playlist_tracks(playlist_id, offset=offset, limit=limit)
            
            if not results or 'items' not in results:
                logger.warning("No tracks found in response")
                break
                
            items = results['items']
            if not items:
                break
                
            logger.info(f"Received {len(items)} tracks in this batch")
            
            # Collect unique artist IDs
            artist_ids = set()
            for item in items:
                if item and 'track' in item and item['track']:
                    track = item['track']
                    if 'artists' in track:
                        for artist in track['artists']:
                            if artist and 'id' in artist:
                                artist_ids.add(artist['id'])
            
            logger.info(f"Found {len(artist_ids)} unique artists in this batch")
            
            # Fetch genres for all artists
            artist_genres = fetch_artist_genres(client, list(artist_ids))
            
            # Process tracks
            for item in items:
                if not item or 'track' not in item or not item['track']:
                    continue
                    
                track = item['track']
                if not track or not track.get('id'):
                    continue
                
                # Get all artists and their genres
                artists = []
                for artist in track.get('artists', []):
                    if artist and 'id' in artist:
                        artist_info = {
                            'id': artist['id'],
                            'name': artist.get('name', 'Unknown Artist'),
                            'genres': artist_genres.get(artist['id'], [])
                        }
                        artists.append(artist_info)
                
                # Create track info
                track_info = {
                    'id': track['id'],
                    'name': track.get('name', 'Unknown Track'),
                    'artists': artists,
                    'album': {
                        'id': track['album']['id'],
                        'name': track['album'].get('name', 'Unknown Album'),
                        'release_date': track['album'].get('release_date', ''),
                        'images': track['album'].get('images', [])
                    },
                    'duration_ms': track.get('duration_ms', 0),
                    'popularity': track.get('popularity', 0),
                    'explicit': track.get('explicit', False),
                    'added_at': item.get('added_at', '')
                }
                
                # Create a TrackMetadata object
                track_metadata = TrackMetadata(
                    uri=track['uri'],
                    added_at=item.get('added_at', ''),
                    track=track,
                    genres=sorted(list(set(genre for artist in artists for genre in artist['genres'])))
                )
                
                tracks.append(track_metadata)
                logger.debug(f"Added track: {track_metadata.track['name']} by {', '.join(a['name'] for a in track_metadata.track['artists'])}")
            
            offset += limit
            if not results.get('next'):
                break
                
        logger.info(f"Successfully fetched {len(tracks)} tracks from playlist {playlist_id}")
        return tracks
        
    except Exception as e:
        logger.error(f"Error fetching tracks for playlist {playlist_id}: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response body: {e.response.text}")
        return [] 