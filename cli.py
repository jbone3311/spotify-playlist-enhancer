"""
Command-line interface for Spotify Playlist Enhancer.
"""

import logging
import json
from typing import List, Optional, Dict
import click
from datetime import datetime
from core import (
    init_spotify_client,
    fetch_user_playlists,
    fetch_liked_tracks,
    get_playlist_track_uris,
    fetch_audio_features,
    fetch_playlist_tracks_with_metadata,
    PlaylistInfo,
    TrackMetadata
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def display_playlists(playlists: List[PlaylistInfo]) -> None:
    """Display available playlists in a formatted table."""
    click.echo("\nAvailable Playlists:")
    click.echo("-" * 60)
    click.echo(f"{'#':<4} {'Name':<40} {'Tracks':<8}")
    click.echo("-" * 60)
    
    for i, playlist in enumerate(playlists, 1):
        click.echo(f"{i:<4} {playlist.name:<40} {playlist.track_count:<8}")
    click.echo("-" * 60)

def export_to_json(data: Dict, filename: str) -> None:
    """Export data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        click.echo(f"\nData exported to {filename}")
    except Exception as e:
        click.echo(f"Error exporting to JSON: {e}", err=True)

def create_playlist(client, name: str, description: str = "") -> str:
    """Create a new playlist and return its ID."""
    try:
        user = client.current_user()
        playlist = client.user_playlist_create(
            user['id'],
            name,
            public=False,
            description=description
        )
        return playlist['id']
    except Exception as e:
        click.echo(f"Error creating playlist: {e}", err=True)
        raise

def add_tracks_to_playlist(client, playlist_id: str, track_uris: List[str]) -> None:
    """Add tracks to a playlist in batches."""
    batch_size = 100
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        try:
            client.playlist_add_items(playlist_id, batch)
            click.echo(f"Added batch of {len(batch)} tracks")
        except Exception as e:
            click.echo(f"Error adding tracks: {e}", err=True)
            raise

@click.group()
def cli():
    """Spotify Playlist Enhancer - CLI Interface"""
    pass

@cli.command()
@click.option('--export', is_flag=True, help='Export analysis to JSON')
@click.option('--playlist', type=int, help='Select playlist by number (0 for Liked Songs)')
def analyze(export, playlist):
    """Analyze a playlist or liked songs."""
    try:
        # Initialize Spotify client
        client = init_spotify_client()
        if not client:
            return

        # Get user's playlists
        playlists = fetch_user_playlists(client)
        if not playlists:
            click.echo("No playlists found.")
            return

        # Display playlists for selection
        click.echo("\nAvailable playlists:")
        for i, playlist_info in enumerate(playlists, 1):
            click.echo(f"{i}. {playlist_info.name} ({playlist_info.track_count} tracks)")

        # If --playlist option is provided, use it; otherwise prompt
        if playlist is None:
            selection = click.prompt("\nEnter playlist number (or 0 for Liked Songs)", type=int)
        else:
            selection = playlist

        if selection == 0:
            click.echo("\nAnalyzing Liked Songs...")
            tracks = fetch_liked_tracks(client)
            playlist_name = "Liked Songs"
        else:
            if selection < 1 or selection > len(playlists):
                click.echo("Invalid selection.")
                return
            playlist_info = playlists[selection - 1]
            click.echo(f"\nAnalyzing playlist: {playlist_info.name}")
            tracks = fetch_playlist_tracks_with_metadata(client, playlist_info.id)
            playlist_name = playlist_info.name

        if not tracks:
            click.echo("No tracks found.")
            return

        # Fetch audio features for all tracks
        logger.info("Fetching audio features...")
        try:
            # Debug logging for track URIs
            track_uris = [track.uri for track in tracks]
            logger.info(f"Track URIs type: {type(track_uris)}")
            logger.info(f"First few track URIs: {track_uris[:3]}")
            logger.info(f"Track URIs length: {len(track_uris)}")
            
            audio_features = fetch_audio_features(client, [track.uri for track in tracks])
        except Exception as e:
            logger.error(f"Error fetching audio features: {e}")
            audio_features = {}
        
        # Create analysis data
        analysis = {
            'playlist_name': playlist_name,
            'total_tracks': len(tracks),
            'tracks': []
        }

        # Process each track
        for track, features in zip(tracks, audio_features):
            track_data = {
                'name': track['track']['name'],
                'artists': [artist['name'] for artist in track['track']['artists']],
                'genres': track.get('genres', []),
                'audio_features': features
            }
            analysis['tracks'].append(track_data)

        # Export to JSON if requested
        if export:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"playlist_analysis_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(analysis, f, indent=2)
            click.echo(f"\nAnalysis exported to {filename}")

        # Display summary
        click.echo(f"\nAnalysis complete!")
        click.echo(f"Total tracks: {len(tracks)}")
        click.echo(f"Playlist: {playlist_name}")

    except Exception as e:
        click.echo(f"Error: {str(e)}")
        logging.error(f"Error in analyze command: {str(e)}", exc_info=True)

@cli.command()
@click.option('--name', prompt='New playlist name', help='Name for the new playlist')
@click.option('--description', default='', help='Description for the new playlist')
def duplicate_liked(name: str, description: str):
    """Create a new playlist with half of your liked songs."""
    try:
        # Initialize Spotify client
        client = init_spotify_client()
        
        # Fetch liked tracks
        click.echo("\nFetching your liked tracks...")
        track_uris = fetch_liked_tracks(client)
        
        if not track_uris:
            click.echo("No liked tracks found!")
            return
            
        # Take half of the tracks
        half_tracks = track_uris[:len(track_uris)//2]
        
        # Create new playlist
        click.echo(f"\nCreating new playlist: {name}")
        playlist_id = create_playlist(client, name, description)
        
        # Add tracks to playlist
        click.echo(f"\nAdding {len(half_tracks)} tracks to playlist...")
        add_tracks_to_playlist(client, playlist_id, half_tracks)
        
        click.echo("\nPlaylist created successfully!")
        
    except Exception as e:
        logger.error(f"Error in duplicate_liked: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--playlist', prompt='Playlist number', help='Number of the playlist to shuffle')
def shuffle(playlist: int):
    """Shuffle a playlist."""
    try:
        # Initialize Spotify client
        client = init_spotify_client()
        
        # Fetch user's playlists
        playlists = fetch_user_playlists(client)
        display_playlists(playlists)
        
        if not 1 <= playlist <= len(playlists):
            click.echo("Invalid playlist number!")
            return
            
        selected_playlist = playlists[playlist - 1]
        click.echo(f"\nShuffling playlist: {selected_playlist.name}")
        
        # Get tracks
        track_uris = get_playlist_track_uris(client, selected_playlist.id)
        
        # Shuffle tracks
        import random
        random.shuffle(track_uris)
        
        # Clear playlist
        client.playlist_replace_items(selected_playlist.id, [])
        
        # Add shuffled tracks
        add_tracks_to_playlist(client, selected_playlist.id, track_uris)
        
        click.echo("\nPlaylist shuffled successfully!")
        
    except Exception as e:
        logger.error(f"Error in shuffle: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli() 