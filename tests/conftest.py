"""
Shared test fixtures for Spotify Playlist Enhancer tests.
"""

import pytest
from unittest.mock import MagicMock
import os
from typing import Dict, List

@pytest.fixture
def mock_spotify_client():
    """Create a mock Spotify client for testing."""
    client = MagicMock()
    
    # Mock playlist response
    mock_playlist_response = {
        'items': [
            {
                'id': 'playlist1',
                'name': 'Test Playlist 1',
                'tracks': {'total': 10}
            },
            {
                'id': 'playlist2',
                'name': 'Test Playlist 2',
                'tracks': {'total': 20}
            }
        ]
    }
    client.current_user_playlists.return_value = mock_playlist_response
    
    # Mock liked tracks response
    mock_liked_tracks = {
        'items': [
            {'track': {'uri': 'spotify:track:track1'}},
            {'track': {'uri': 'spotify:track:track2'}}
        ]
    }
    client.current_user_saved_tracks.return_value = mock_liked_tracks
    
    # Mock playlist tracks response
    mock_playlist_tracks = {
        'items': [
            {'track': {'uri': 'spotify:track:track1'}},
            {'track': {'uri': 'spotify:track:track2'}}
        ]
    }
    client.playlist_items.return_value = mock_playlist_tracks
    
    # Mock audio features response
    mock_audio_features = [
        {
            'danceability': 0.8,
            'energy': 0.7,
            'key': 5,
            'loudness': -6.0,
            'mode': 1,
            'speechiness': 0.1,
            'acousticness': 0.2,
            'instrumentalness': 0.0,
            'liveness': 0.1,
            'valence': 0.8,
            'tempo': 120.0,
            'time_signature': 4
        }
    ]
    client.audio_features.return_value = mock_audio_features
    
    return client

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv('SPOTIFY_CLIENT_ID', 'test_client_id')
    monkeypatch.setenv('SPOTIFY_CLIENT_SECRET', 'test_client_secret') 