"""
Command-line interface for Spotify Playlist Enhancer.
"""

import logging
from typing import List, Optional
import click
from core import (
    init_spotify_client,
    fetch_user_playlists,
    fetch_liked_tracks,
    get_playlist_track_uris,
    fetch_audio_features,
    PlaylistInfo
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

@click.command()
@click.option('--tempo-buckets', is_flag=True, help='Create tempo-based playlists')
@click.option('--energy-buckets', is_flag=True, help='Create energy-based playlists')
@click.option('--enhance', is_flag=True, help='Add recommended tracks')
@click.option('--shuffle', is_flag=True, help='Shuffle the playlist')
@click.option('--export', is_flag=True, help='Export analysis to JSON')
def main(
    tempo_buckets: bool,
    energy_buckets: bool,
    enhance: bool,
    shuffle: bool,
    export: bool
) -> None:
    """Spotify Playlist Enhancer - CLI Interface"""
    try:
        # Initialize Spotify client
        client = init_spotify_client()
        
        # Fetch user's playlists
        playlists = fetch_user_playlists(client)
        display_playlists(playlists)
        
        # Get user selection
        while True:
            choice = click.prompt(
                "\nEnter playlist number or 'L' for Liked Songs",
                type=str
            )
            
            if choice.upper() == 'L':
                click.echo("\nFetching Liked Songs...")
                track_uris = fetch_liked_tracks(client)
                break
            elif choice.isdigit() and 1 <= int(choice) <= len(playlists):
                playlist = playlists[int(choice) - 1]
                click.echo(f"\nFetching tracks from '{playlist.name}'...")
                track_uris = get_playlist_track_uris(client, playlist.id)
                break
            else:
                click.echo("Invalid selection. Please try again.")
        
        # Fetch audio features
        click.echo("\nAnalyzing tracks...")
        features = fetch_audio_features(client, track_uris)
        
        # TODO: Implement remaining features
        if tempo_buckets:
            click.echo("Tempo bucketing not yet implemented")
        if energy_buckets:
            click.echo("Energy bucketing not yet implemented")
        if enhance:
            click.echo("Track enhancement not yet implemented")
        if shuffle:
            click.echo("Playlist shuffle not yet implemented")
        if export:
            click.echo("JSON export not yet implemented")
            
        click.echo("\nAnalysis complete!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    main() 