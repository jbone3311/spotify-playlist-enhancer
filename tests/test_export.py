"""
Tests for export functionality of Spotify Playlist Enhancer.
"""

import pytest
import json
from unittest.mock import patch, mock_open
from export import export_analysis

def test_export_analysis():
    """Test analysis export functionality."""
    # Test data
    features = {
        'spotify:track:track1': {
            'danceability': 0.8,
            'energy': 0.7
        }
    }
    
    tempo_buckets = {
        'slow': ['spotify:track:track1'],
        'medium': [],
        'fast': []
    }
    
    energy_buckets = {
        'low': ['spotify:track:track1'],
        'medium': [],
        'high': []
    }
    
    # Mock file operations
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        filepath = export_analysis(
            features,
            tempo_buckets=tempo_buckets,
            energy_buckets=energy_buckets,
            filepath='test_output.json'
        )
        
        # Verify file was opened in write mode
        mock_file.assert_called_once_with('test_output.json', 'w')
        
        # Verify JSON was written correctly
        handle = mock_file()
        written = ''.join(call.args[0] for call in handle.write.call_args_list)
        written_data = json.loads(written)
        assert written_data['track_count'] == 1
        assert written_data['audio_features'] == features
        assert written_data['tempo_buckets'] == tempo_buckets
        assert written_data['energy_buckets'] == energy_buckets

def test_export_analysis_minimal():
    """Test analysis export with minimal data."""
    features = {
        'spotify:track:track1': {
            'danceability': 0.8,
            'energy': 0.7
        }
    }
    
    mock_file = mock_open()
    with patch('builtins.open', mock_file):
        filepath = export_analysis(features)
        
        handle = mock_file()
        written = ''.join(call.args[0] for call in handle.write.call_args_list)
        written_data = json.loads(written)
        assert written_data['track_count'] == 1
        assert written_data['audio_features'] == features
        assert 'tempo_buckets' not in written_data
        assert 'energy_buckets' not in written_data

def test_export_analysis_error_handling():
    """Test error handling in analysis export."""
    features = {
        'spotify:track:track1': {
            'danceability': 0.8,
            'energy': 0.7
        }
    }
    
    # Simulate file write error
    mock_file = mock_open()
    mock_file.side_effect = IOError("File write error")
    
    with patch('builtins.open', mock_file), \
         pytest.raises(IOError):
        export_analysis(features, filepath='test_output.json') 