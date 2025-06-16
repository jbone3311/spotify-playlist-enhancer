"""
Shared test fixtures for Spotify Playlist Enhancer tests.
"""

import pytest
from unittest.mock import MagicMock
import os
from datetime import datetime
from typing import Dict, List
from core import PlaylistInfo, TrackMetadata

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
                'tracks': {'total': 10},
                'description': '',
                'owner': {'display_name': 'Test Owner'},
                'public': True,
                'collaborative': False,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z',
                'images': [{'url': 'https://example.com/image1.jpg'}]
            },
            {
                'id': 'playlist2',
                'name': 'Test Playlist 2',
                'tracks': {'total': 20},
                'description': '',
                'owner': {'display_name': 'Test Owner'},
                'public': True,
                'collaborative': False,
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-02T00:00:00Z',
                'images': [{'url': 'https://example.com/image2.jpg'}]
            }
        ]
    }
    client.current_user_playlists.return_value = mock_playlist_response
    
    # Mock liked tracks response
    mock_liked_tracks = {
        'items': [
            {
                'track': {
                    'id': 'track1',
                    'name': 'Test Track 1',
                    'artists': [{'name': 'Test Artist 1'}],
                    'album': {'name': 'Test Album 1'},
                    'duration_ms': 180000,
                    'popularity': 80,
                    'uri': 'spotify:track:track1'
                },
                'added_at': '2024-01-01T00:00:00Z'
            },
            {
                'track': {
                    'id': 'track2',
                    'name': 'Test Track 2',
                    'artists': [{'name': 'Test Artist 2'}],
                    'album': {'name': 'Test Album 2'},
                    'duration_ms': 240000,
                    'popularity': 75,
                    'uri': 'spotify:track:track2'
                },
                'added_at': '2024-01-02T00:00:00Z'
            }
        ]
    }
    client.current_user_saved_tracks.return_value = mock_liked_tracks
    
    # Mock playlist tracks response
    mock_playlist_tracks = {
        'items': [
            {
                'track': {
                    'id': 'track1',
                    'name': 'Test Track 1',
                    'artists': [{'name': 'Test Artist 1'}],
                    'album': {'name': 'Test Album 1'},
                    'duration_ms': 180000,
                    'popularity': 80,
                    'uri': 'spotify:track:track1'
                },
                'added_at': '2024-01-01T00:00:00Z'
            },
            {
                'track': {
                    'id': 'track2',
                    'name': 'Test Track 2',
                    'artists': [{'name': 'Test Artist 2'}],
                    'album': {'name': 'Test Album 2'},
                    'duration_ms': 240000,
                    'popularity': 75,
                    'uri': 'spotify:track:track2'
                },
                'added_at': '2024-01-02T00:00:00Z'
            }
        ]
    }
    client.playlist_tracks.return_value = mock_playlist_tracks
    
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
    monkeypatch.setenv('SPOTIPY_REDIRECT_URI', 'http://localhost:8888/callback') 