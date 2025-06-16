"""
Core functionality for Spotify Playlist Enhancer.
Handles authentication, Spotify API interactions, and analysis.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import requests
import traceback
from datetime import datetime
import random
import json

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
    description: str = ''
    owner: str = ''
    is_public: bool = True
    is_collaborative: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image_url: Optional[str] = None

@dataclass
class TrackMetadata:
    """Container for track metadata including when it was added."""
    id: str
    name: str
    artist: str
    artist_id: str
    album: str
    duration_ms: int
    popularity: int
    added_at: str
    genres: List[str]
    uri: str

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

def init_spotify_client() -> Optional[spotipy.Spotify]:
    """Initialize Spotify client with environment variables."""
    try:
        verify_env_variables()
        
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('REDIRECT_URI', 'http://127.0.0.1:8888/callback')
        
        logger.info("Initializing Spotify client with:")
        logger.info(f"Client ID: {client_id[:8]}...")
        logger.info(f"Redirect URI: {redirect_uri}")
        
        scopes = [
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
            'playlist-read-collaborative',
            'playlist-modify-public',
            'playlist-modify-private',
            'user-follow-read',
            'user-follow-modify',
            'user-read-email'  # Required for audio features and analysis
        ]
        
        logger.info(f"Scopes: {', '.join(scopes)}")
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scopes,
            open_browser=True
        )
        
        client = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Successfully initialized Spotify client")
        return client
        
    except Exception as e:
        logger.error(f"Error initializing Spotify client: {e}")
        return None

def paginate_api_call(client, api_method, **kwargs):
    """
    Helper function to handle pagination for Spotify API calls.
    
    Args:
        client: Spotify client instance
        api_method: The API method to call (e.g., client.current_user_playlists)
        **kwargs: Additional arguments to pass to the API method
        
    Returns:
        list: Combined results from all pages
    """
    results = []
    offset = 0
    limit = kwargs.pop('limit', 50)
    
    while True:
        try:
            response = api_method(limit=limit, offset=offset, **kwargs)
            items = response.get('items', [])
            results.extend(items)
            
            if len(items) < limit:
                break
                
            offset += limit
        except Exception as e:
            logger.error(f"Error in pagination: {e}")
            logger.error(traceback.format_exc())
            raise
            
    return results

def fetch_user_playlists(sp: spotipy.Spotify) -> List[PlaylistInfo]:
    """
    Fetch all playlists for the current user.
    
    Args:
        sp: Authenticated Spotify client
        
    Returns:
        List[PlaylistInfo]: List of playlist information objects
        
    Raises:
        Exception: If there's an error fetching playlists
    """
    try:
        logger.info("Fetching user playlists...")
        playlists = paginate_api_call(sp, sp.current_user_playlists)
        
        playlist_info = []
        for p in playlists:
            try:
                # Parse dates safely
                created_at = None
                updated_at = None
                try:
                    if 'created_at' in p:
                        created_at = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse created_at for playlist {p.get('id', 'unknown')}")
                
                try:
                    if 'updated_at' in p:
                        updated_at = datetime.fromisoformat(p['updated_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse updated_at for playlist {p.get('id', 'unknown')}")
                
                playlist = PlaylistInfo(
                    id=p['id'],
                    name=p['name'],
                    description=p.get('description', ''),
                    track_count=p['tracks']['total'],
                    owner=p['owner']['display_name'],
                    is_public=p['public'],
                    is_collaborative=p['collaborative'],
                    created_at=created_at,
                    updated_at=updated_at,
                    image_url=p['images'][0]['url'] if p['images'] else None
                )
                playlist_info.append(playlist)
                logger.debug(f"Found playlist: {playlist.name} (ID: {playlist.id}, Tracks: {playlist.track_count})")
            except Exception as e:
                logger.error(f"Error processing playlist {p.get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"Successfully fetched {len(playlist_info)} playlists")
        return playlist_info
        
    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        logger.error(traceback.format_exc())
        raise

def fetch_playlist_tracks_with_metadata(client: spotipy.Spotify, playlist_id: str) -> List[TrackMetadata]:
    """Fetch tracks from a playlist with metadata."""
    try:
        tracks = []
        results = client.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                if item['track']:
                    track = item['track']
                    artist = track['artists'][0]['name'] if track['artists'] else "Unknown Artist"
                    artist_id = track['artists'][0]['id'] if track['artists'] else None
                    
                    # Get artist genres if we have an artist ID
                    genres = []
                    if artist_id:
                        try:
                            artist_info = client.artist(artist_id)
                            genres = artist_info.get('genres', [])
                        except Exception as e:
                            logger.warning(f"Could not fetch genres for artist {artist_id}: {e}")
                    
                    track_metadata = TrackMetadata(
                        id=track['id'],
                        name=track['name'],
                        artist=artist,
                        artist_id=artist_id,
                        album=track['album']['name'],
                        duration_ms=track['duration_ms'],
                        popularity=track['popularity'],
                        added_at=item['added_at'],
                        genres=genres,
                        uri=track['uri']
                    )
                    tracks.append(track_metadata)
            
            if results['next']:
                results = client.next(results)
            else:
                results = None
        
        return tracks
    except Exception as e:
        logger.error(f"Error fetching playlist tracks: {e}")
        return []

def fetch_liked_tracks(sp: spotipy.Spotify) -> List[TrackMetadata]:
    """
    Fetch all liked tracks with their metadata.
    
    Args:
        sp: Authenticated Spotify client
        
    Returns:
        List[TrackMetadata]: List of track metadata objects
        
    Raises:
        Exception: If there's an error fetching liked tracks
    """
    try:
        logger.info("Fetching liked tracks...")
        tracks = paginate_api_call(sp, sp.current_user_saved_tracks)
        
        track_metadata = []
        for item in tracks:
            try:
                track = item['track']
                if not track:
                    continue
                    
                metadata = TrackMetadata(
                    id=track['id'],
                    name=track['name'],
                    artist=track['artists'][0]['name'],
                    artist_id=track['artists'][0]['id'],
                    album=track['album']['name'],
                    duration_ms=track['duration_ms'],
                    popularity=track['popularity'],
                    added_at=item['added_at'],
                    genres=[]  # Will be populated later
                )
                track_metadata.append(metadata)
                logger.debug(f"Found liked track: {metadata.name} by {metadata.artist}")
            except Exception as e:
                logger.error(f"Error processing liked track {item.get('track', {}).get('id', 'unknown')}: {e}")
                continue
                
        logger.info(f"Successfully fetched {len(track_metadata)} liked tracks")
        return track_metadata
        
    except Exception as e:
        logger.error(f"Error fetching liked tracks: {e}")
        logger.error(traceback.format_exc())
        raise

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
    """
    Fetch audio features for a list of track URIs.
    """
    # Filter out None values
    track_uris = [uri for uri in track_uris if uri]
    
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

def shuffle_playlist(client: spotipy.Spotify, playlist_id: str) -> None:
    """
    Shuffle the tracks in a playlist using the Spotify API.
    """
    try:
        # Get the current tracks in the playlist
        tracks = get_playlist_track_uris(client, playlist_id)
        if not tracks:
            logger.warning("No tracks found in playlist.")
            return

        # Shuffle the track URIs
        random.shuffle(tracks)

        # Batch the tracks into chunks of 100
        batch_size = 100
        for i in range(0, len(tracks), batch_size):
            batch = tracks[i:i + batch_size]
            client.playlist_replace_items(playlist_id, batch)
            logger.info(f"Updated batch {i//batch_size + 1} of playlist {playlist_id}.")

        logger.info(f"Playlist {playlist_id} shuffled successfully.")
    except Exception as e:
        logger.error(f"Error shuffling playlist: {e}")
        raise

def export_analysis(tracks: List[TrackMetadata], features: Dict[str, dict]) -> None:
    """
    Export playlist analysis data to a JSON file.
    """
    try:
        # Create a dictionary with track and feature data
        data = {
            "tracks": [
                {
                    "id": track.id,
                    "name": track.name,
                    "artist": track.artist,
                    "album": track.album,
                    "duration_ms": track.duration_ms,
                    "popularity": track.popularity,
                    "added_at": track.added_at,
                    "genres": track.genres,
                    "uri": track.uri
                }
                for track in tracks
            ],
            "audio_features": features
        }

        # Generate a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"playlist_analysis_{timestamp}.json"

        # Write the data to a JSON file
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        logger.info(f"Analysis exported to {filename}")
    except Exception as e:
        logger.error(f"Error exporting analysis: {e}")
        raise

def get_audio_analysis(client: spotipy.Spotify, track_id: str) -> Optional[dict]:
    """Get detailed audio analysis for a track."""
    try:
        if not track_id:
            logger.warning("No track ID provided for audio analysis")
            return None
            
        analysis = client.audio_analysis(track_id)
        return analysis
    except Exception as e:
        logger.error(f"Error getting audio analysis for track {track_id}: {e}")
        return None

def get_track_recommendations(client: spotipy.Spotify, seed_tracks: List[str], limit: int = 20) -> List[TrackMetadata]:
    """
    Get track recommendations based on seed tracks.
    """
    try:
        recommendations = client.recommendations(
            seed_tracks=seed_tracks[:5],  # Spotify allows max 5 seed tracks
            limit=limit
        )
        
        tracks = []
        for track in recommendations['tracks']:
            metadata = TrackMetadata(
                id=track['id'],
                name=track['name'],
                artist=track['artists'][0]['name'],
                artist_id=track['artists'][0]['id'],
                album=track['album']['name'],
                duration_ms=track['duration_ms'],
                popularity=track['popularity'],
                added_at=track['added_at'],
                genres=track['artists'][0]['genres'],
                uri=track['uri']
            )
            tracks.append(metadata)
        
        return tracks
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return []

def get_artist_details(client: spotipy.Spotify, artist_id: str) -> Optional[dict]:
    """Get detailed information about an artist."""
    try:
        if not artist_id or artist_id == 'None':
            logger.warning("No artist ID provided")
            return None
        artist_info = client.artist(artist_id)
        top_tracks = client.artist_top_tracks(artist_id)
        related_artists = client.artist_related_artists(artist_id)
        return {
            'info': artist_info,
            'top_tracks': top_tracks['tracks'],
            'related_artists': related_artists['artists']
        }
    except Exception as e:
        logger.error(f"Error getting artist details for {artist_id}: {e}")
        return None

def get_playlist_recommendations(client: spotipy.Spotify, playlist_id: str, limit: int = 20) -> List[TrackMetadata]:
    """Get track recommendations based on tracks in a playlist."""
    try:
        tracks = fetch_playlist_tracks_with_metadata(client, playlist_id)
        if not tracks:
            logger.warning("No tracks found in playlist for recommendations")
            return []
        seed_tracks = [track.id for track in tracks[:5] if track.id]
        if not seed_tracks:
            logger.warning("No valid seed tracks found")
            return []
        recommendations = client.recommendations(
            seed_tracks=seed_tracks,
            limit=limit,
            market='US',
            min_popularity=50
        )
        recommended_tracks = []
        for track in recommendations['tracks']:
            track_metadata = TrackMetadata(
                id=track['id'],
                name=track['name'],
                artist=track['artists'][0]['name'],
                artist_id=track['artists'][0]['id'],
                album=track['album']['name'],
                duration_ms=track['duration_ms'],
                popularity=track['popularity'],
                added_at=datetime.now().isoformat(),
                genres=[],
                uri=track['uri']
            )
            recommended_tracks.append(track_metadata)
        return recommended_tracks
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return [] 