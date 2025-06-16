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
import traceback

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

def export_analysis(tracks, features):
    """Dummy export_analysis for testing purposes."""
    pass

@click.group()
def cli():
    """Spotify Playlist Enhancer - CLI Interface"""
    pass

@cli.command()
@click.option('--export', is_flag=True, help='Export analysis to JSON file')
@click.option('--playlist', type=int, help='Playlist number to analyze')
def analyze(export: bool, playlist: int):
    """Analyze a playlist and display track information."""
    try:
        client = init_spotify_client()
        playlists = fetch_user_playlists(client)
        click.echo("\nAvailable playlists:")
        for i, playlist_info in enumerate(playlists, 1):
            click.echo(f"{i}. {playlist_info.name} ({playlist_info.track_count} tracks)")
        if playlist is None:
            playlist = click.prompt("Enter playlist number to analyze", type=int)
        selected_playlist = playlists[playlist - 1]
        click.echo(f"\nSelected playlist: {selected_playlist.name}")
        click.echo(f"Fetching tracks from playlist: {selected_playlist.name}")
        tracks = fetch_playlist_tracks_with_metadata(client, selected_playlist.id)
        click.echo(f"Successfully fetched {len(tracks)} tracks")
        click.echo("Starting audio features analysis...")
        track_uris = [track.uri for track in tracks]
        audio_features = fetch_audio_features(client, track_uris)
        click.echo(f"Successfully analyzed {len(audio_features)} tracks")
        if export:
            export_analysis(tracks, audio_features)
        click.echo("Displaying track analysis...")
        for track, features in zip(tracks, audio_features):
            click.echo(f"Track: {track.name} by {track.artist}")
            if features:
                click.echo(f"  Danceability: {features.get('danceability', 'N/A')}")
                click.echo(f"  Energy: {features.get('energy', 'N/A')}")
                click.echo(f"  Valence: {features.get('valence', 'N/A')}")
            else:
                click.echo("  No audio features available")
    except Exception as e:
        logger.error(f"Error in analyze command: {e}")
        logger.error(traceback.format_exc())
        raise

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
@click.option('--playlist', prompt='Playlist number', type=int, help='Number of the playlist to shuffle')
def shuffle(playlist: int):
    """Shuffle a playlist."""
    try:
        playlist = int(playlist)  # Ensure playlist is always an int
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