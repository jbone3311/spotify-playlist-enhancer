"""
Tests for app functionality of Spotify Playlist Enhancer.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
from unittest.mock import patch, MagicMock
from app import (
    format_duration,
    create_audio_features_plot,
    display_track_table
)

def test_format_duration():
    """Test duration formatting."""
    assert format_duration(61000) == "1:01"
    assert format_duration(0) == "0:00"
    assert format_duration(59999) == "0:59"
    assert format_duration(3600000) == "60:00"

def test_create_audio_features_plot():
    """Test audio features plot creation."""
    # Create test data
    df = pd.DataFrame({
        'danceability': [0.5, 0.6, 0.7, 0.8, 0.9]
    })
    
    # Create plot
    fig = create_audio_features_plot(df, 'danceability', 'Test Plot')
    
    # Verify plot properties
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == 'Test Plot'
    assert fig.layout.xaxis.title.text == 'Danceability'
    assert fig.layout.yaxis.title.text == 'Count'
    
    # Verify mean line
    mean_line = [shape for shape in fig.layout.shapes if shape.line.dash == 'dash']
    assert len(mean_line) == 1
    assert mean_line[0].line.color == 'red'

def test_create_audio_features_plot_empty_data():
    """Test audio features plot creation with empty data."""
    df = pd.DataFrame({'danceability': []})
    fig = create_audio_features_plot(df, 'danceability', 'Empty Plot')
    assert isinstance(fig, go.Figure)

def test_display_track_table_empty():
    """Test track table display with empty data."""
    display_track_table([], {})

def test_display_track_table_with_data():
    """Test track table display with sample data."""
    # Sample track data
    tracks = [{
        'name': 'Test Track',
        'artists': [{'name': 'Test Artist'}],
        'album': {'name': 'Test Album', 'album_type': 'album', 'release_date': '2024-01-01'},
        'duration_ms': 180000,
        'popularity': 80,
        'explicit': False,
        'track_number': 1,
        'disc_number': 1,
        'preview_url': 'https://example.com/preview',
        'external_ids': {'isrc': 'TEST123'},
        'available_markets': ['US', 'GB'],
        'uri': 'spotify:track:test123'
    }]
    
    # Sample audio features
    features = {
        'spotify:track:test123': {
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
    }
    
    display_track_table(tracks, features)

def test_display_track_table_missing_features():
    """Test track table display with missing audio features."""
    tracks = [{
        'name': 'Test Track',
        'artists': [{'name': 'Test Artist'}],
        'album': {'name': 'Test Album', 'album_type': 'album', 'release_date': '2024-01-01'},
        'duration_ms': 180000,
        'popularity': 80,
        'explicit': False,
        'track_number': 1,
        'disc_number': 1,
        'preview_url': 'https://example.com/preview',
        'external_ids': {'isrc': 'TEST123'},
        'available_markets': ['US', 'GB'],
        'uri': 'spotify:track:test123'
    }]
    
    display_track_table(tracks, {}) 