"""
Tests for CLI functionality of Spotify Playlist Enhancer.
"""

import pytest
from click.testing import CliRunner
from cli import cli, display_playlists
from core import PlaylistInfo, TrackMetadata
from datetime import datetime

def test_display_playlists(capsys):
    """Test playlist display functionality."""
    playlists = [
        PlaylistInfo(
            id="1",
            name="Test Playlist 1",
            track_count=10,
            description="",
            owner="Test Owner",
            is_public=True,
            is_collaborative=False,
            created_at=None,
            updated_at=None,
            image_url="https://example.com/image1.jpg"
        ),
        PlaylistInfo(
            id="2",
            name="Test Playlist 2",
            track_count=20,
            description="",
            owner="Test Owner",
            is_public=True,
            is_collaborative=False,
            created_at=None,
            updated_at=None,
            image_url="https://example.com/image2.jpg"
        )
    ]
    display_playlists(playlists)
    captured = capsys.readouterr()
    assert "Test Playlist 1" in captured.out
    assert "Test Playlist 2" in captured.out
    assert "10" in captured.out
    assert "20" in captured.out

@pytest.mark.parametrize("command,expected", [
    (["analyze", "--playlist", "1"], "Fetching tracks from"),
    (["analyze", "--playlist", "1", "--export"], "Data exported to"),
    (["duplicate-liked", "--name", "Test Playlist"], "Creating new playlist"),
    (["shuffle", "--playlist", "1"], "Shuffling playlist")
])
def test_cli_commands(monkeypatch, command, expected):
    """Test CLI commands with different options."""
    runner = CliRunner()
    
    # Patch Spotify client and core functions
    if command[0] == "shuffle":
        class DummyClient:
            def playlist_replace_items(self, playlist_id, items):
                pass
        monkeypatch.setattr("cli.init_spotify_client", lambda: DummyClient())
    else:
        monkeypatch.setattr("cli.init_spotify_client", lambda: None)
    monkeypatch.setattr("cli.fetch_user_playlists", lambda client: [
        PlaylistInfo(
            id="1",
            name="Test Playlist",
            track_count=10,
            description="",
            owner="Test Owner",
            is_public=True,
            is_collaborative=False,
            created_at=None,
            updated_at=None,
            image_url="https://example.com/image1.jpg"
        )
    ])
    monkeypatch.setattr("cli.fetch_playlist_tracks_with_metadata", lambda client, pid: [
        TrackMetadata(
            id="track1",
            name="Test Track",
            artist="Test Artist",
            album="Test Album",
            duration_ms=180000,
            popularity=80,
            added_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
            genres=[],
            uri="spotify:track:track1"
        )
    ])
    monkeypatch.setattr("cli.fetch_liked_tracks", lambda client: ['spotify:track:track1'])
    monkeypatch.setattr("cli.fetch_audio_features", lambda client, uris: [
        {'danceability': 0.8, 'energy': 0.7}
    ])
    monkeypatch.setattr("cli.create_playlist", lambda client, name, description: "new_playlist_id")
    monkeypatch.setattr("cli.add_tracks_to_playlist", lambda client, pid, uris: None)
    monkeypatch.setattr("cli.get_playlist_track_uris", lambda client, pid: ['spotify:track:track1'])
    monkeypatch.setattr("cli.export_analysis", lambda tracks, features: print("Data exported to"))
    
    # Ensure playlist argument is string for shuffle command (Click parses from string)
    if command[0] == "shuffle":
        command = [command[0], "--playlist", "1"]
    
    result = runner.invoke(cli, command)
    assert result.exit_code == 0
    assert expected in result.output 