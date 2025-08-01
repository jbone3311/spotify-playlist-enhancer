"""
Tests for core functionality of Spotify Playlist Enhancer.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime
from core import (
    verify_env_variables,
    init_spotify_client,
    fetch_user_playlists,
    fetch_liked_tracks,
    fetch_playlist_tracks_with_metadata,
    fetch_audio_features,
    PlaylistInfo,
    TrackMetadata
)

def test_verify_env_variables(mock_env_vars):
    """Test environment variable verification."""
    verify_env_variables()  # Should not raise any exceptions

def test_verify_env_variables_missing(monkeypatch):
    """Test environment variable verification with missing variables."""
    # Patch os.getenv to always return None for the required variables
    monkeypatch.setattr('os.getenv', lambda key, default=None: None)
    with pytest.raises(ValueError):
        verify_env_variables()

@patch('core.SpotifyOAuth')
def test_init_spotify_client(mock_oauth, mock_env_vars):
    """Test Spotify client initialization."""
    mock_oauth.return_value = MagicMock()
    client = init_spotify_client()
    assert client is not None
    mock_oauth.assert_called_once()

def test_fetch_user_playlists(mock_spotify_client):
    """Test fetching user playlists."""
    playlists = fetch_user_playlists(mock_spotify_client)
    assert len(playlists) == 2
    assert isinstance(playlists[0], PlaylistInfo)
    assert playlists[0].id == 'playlist1'
    assert playlists[0].name == 'Test Playlist 1'
    assert playlists[0].track_count == 10
    assert playlists[0].description == ''
    assert playlists[0].owner == 'Test Owner'
    assert playlists[0].is_public is True
    assert playlists[0].is_collaborative is False
    assert isinstance(playlists[0].created_at, datetime)
    assert isinstance(playlists[0].updated_at, datetime)

def test_fetch_liked_tracks(mock_spotify_client):
    """Test fetching liked tracks."""
    tracks = fetch_liked_tracks(mock_spotify_client)
    assert len(tracks) == 2
    assert isinstance(tracks[0], TrackMetadata)
    assert tracks[0].id == 'track1'
    assert tracks[0].name == 'Test Track 1'
    assert tracks[0].artist == 'Test Artist 1'
    assert tracks[0].album == 'Test Album 1'
    assert tracks[0].duration_ms == 180000
    assert tracks[0].popularity == 80
    assert isinstance(tracks[0].added_at, datetime)
    assert isinstance(tracks[0].genres, list)

def test_fetch_playlist_tracks_with_metadata(mock_spotify_client):
    """Test fetching playlist tracks with metadata."""
    tracks = fetch_playlist_tracks_with_metadata(mock_spotify_client, 'playlist1')
    assert len(tracks) == 2
    assert isinstance(tracks[0], TrackMetadata)
    assert tracks[0].id == 'track1'
    assert tracks[0].name == 'Test Track 1'
    assert tracks[0].artist == 'Test Artist 1'
    assert tracks[0].album == 'Test Album 1'
    assert tracks[0].duration_ms == 180000
    assert tracks[0].popularity == 80
    assert isinstance(tracks[0].added_at, datetime)
    assert isinstance(tracks[0].genres, list)

def test_fetch_audio_features(mock_spotify_client):
    """Test fetching audio features."""
    track_uris = ['spotify:track:track1', 'spotify:track:track2']
    features = fetch_audio_features(mock_spotify_client, track_uris)
    
    assert len(features) == 1  # Our mock returns one feature set
    feature = features['spotify:track:track1']
    assert feature['danceability'] == 0.8
    assert feature['energy'] == 0.7
    assert feature['tempo'] == 120.0

def test_fetch_audio_features_empty_list(mock_spotify_client):
    """Test fetching audio features with empty track list."""
    features = fetch_audio_features(mock_spotify_client, [])
    assert len(features) == 0

def test_fetch_audio_features_error_handling(mock_spotify_client):
    """Test error handling in audio features fetching."""
    mock_spotify_client.audio_features.side_effect = Exception("API Error")
    track_uris = ['spotify:track:track1']
    features = fetch_audio_features(mock_spotify_client, track_uris)
    assert len(features) == 0  # Should return empty dict on error 