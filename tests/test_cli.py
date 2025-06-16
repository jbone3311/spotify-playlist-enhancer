"""
Tests for CLI functionality of Spotify Playlist Enhancer.
"""

import pytest
from click.testing import CliRunner
from cli import main, display_playlists

class DummyPlaylist:
    def __init__(self, id, name, track_count):
        self.id = id
        self.name = name
        self.track_count = track_count

def test_display_playlists(capsys):
    """Test playlist display functionality."""
    playlists = [
        DummyPlaylist("1", "Test Playlist 1", 10),
        DummyPlaylist("2", "Test Playlist 2", 20)
    ]
    display_playlists(playlists)
    captured = capsys.readouterr()
    assert "Test Playlist 1" in captured.out
    assert "Test Playlist 2" in captured.out
    assert "10" in captured.out
    assert "20" in captured.out

@pytest.mark.parametrize("user_input, expected", [("1", "Fetching tracks from"), ("L", "Fetching Liked Songs")])
def test_main_cli(monkeypatch, user_input, expected):
    """Test CLI main function with playlist and liked songs selection."""
    runner = CliRunner()
    # Patch Spotify client and core functions
    monkeypatch.setattr("cli.init_spotify_client", lambda: None)
    monkeypatch.setattr("cli.fetch_user_playlists", lambda client: [DummyPlaylist("1", "Test Playlist", 10)])
    monkeypatch.setattr("cli.get_playlist_track_uris", lambda client, pid: ["spotify:track:track1"])
    monkeypatch.setattr("cli.fetch_liked_tracks", lambda client: ["spotify:track:track1"])
    monkeypatch.setattr("cli.fetch_audio_features", lambda client, uris: {"spotify:track:track1": {"danceability": 0.8, "energy": 0.7}})
    # Patch click.prompt to simulate user input
    monkeypatch.setattr("click.prompt", lambda *a, **k: user_input)
    result = runner.invoke(main, ["--export"])
    assert result.exit_code == 0
    assert expected in result.output 