"""
Streamlit app for Spotify Playlist Enhancer.
Provides a web interface for playlist analysis and management.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import traceback
import numpy as np

from core import (
    TrackMetadata,
    PlaylistInfo,
    fetch_user_playlists,
    fetch_playlist_tracks_with_metadata,
    fetch_liked_tracks,
    fetch_audio_features,
    fetch_artist_genres,
    init_spotify_client,
    shuffle_playlist,
    export_analysis,
    get_playlist_recommendations,
    get_audio_analysis,
    get_artist_details
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config at the very beginning
st.set_page_config(
    page_title="Spotify Playlist Enhancer",
    page_icon="🎵",
    layout="wide"
)

def format_duration(ms: int) -> str:
    """
    Format milliseconds into a human-readable duration string.
    
    Args:
        ms: Duration in milliseconds
        
    Returns:
        str: Formatted duration string (e.g., "3:45")
    """
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def create_audio_features_plot(df: pd.DataFrame, feature: str, title: str) -> go.Figure:
    """Create a histogram with a vertical line for the mean."""
    fig = px.histogram(
        df, 
        x=feature,
        title=title,
        nbins=30,
        color_discrete_sequence=['#1DB954']  # Spotify green
    )
    
    # Add mean line
    mean_value = df[feature].mean()
    fig.add_vline(
        x=mean_value,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_value:.2f}",
        annotation_position="top right"
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title=feature.capitalize(),
        yaxis_title="Count",
        template="plotly_white"
    )
    
    return fig

def display_track_table(tracks: List[TrackMetadata], features: Dict[str, dict]) -> None:
    """
    Display a table of tracks with their metadata and audio features.
    
    Args:
        tracks: List of track metadata objects
        features: Dictionary mapping track URIs to their audio features
    """
    if not tracks:
        st.warning("No tracks to display.")
        return
        
    # Create DataFrame with track info and audio features
    data = []
    for track_meta in tracks:
        track_data = {
            'Name': track_meta.name,
            'Artist': track_meta.artist,
            'Album': track_meta.album,
            'Duration': format_duration(track_meta.duration_ms),
            'Popularity': track_meta.popularity,
            'Genres': ', '.join(track_meta.genres) if track_meta.genres else 'N/A'
        }
        
        # Add audio features if available
        if track_meta.uri in features:
            track_data.update(features[track_meta.uri])
        
        data.append(track_data)
    
    # Create DataFrame and display
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

def main():
    """Main function to run the Streamlit app."""
    st.title("Spotify Playlist Enhancer")
    
    try:
        # Initialize Spotify client
        client = init_spotify_client()
        
        # Fetch user's playlists
        playlists = fetch_user_playlists(client)
        
        if not playlists:
            st.warning("No playlists found!")
            return
            
        # Display playlist selection
        playlist_names = [f"{p.name} ({p.track_count} tracks)" for p in playlists]
        selected_playlist_name = st.selectbox(
            "Select a playlist to enhance",
            playlist_names
        )
        
        # Get the selected playlist object
        selected_playlist = playlists[playlist_names.index(selected_playlist_name)]
        
        st.write(f"Analyzing playlist: {selected_playlist.name}")
        
        # Fetch tracks and their metadata
        tracks = fetch_playlist_tracks_with_metadata(client, selected_playlist.id)
        
        if not tracks:
            st.warning("No tracks found in the selected playlist!")
            return
            
        # Calculate basic statistics
        total_tracks = len(tracks)
        total_duration = sum(track.duration_ms for track in tracks)
        avg_popularity = sum(track.popularity for track in tracks) / total_tracks
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tracks", total_tracks)
        with col2:
            st.metric("Total Duration", format_duration(total_duration))
        with col3:
            st.metric("Average Popularity", f"{avg_popularity:.1f}")
            
        # Fetch audio features
        track_uris = [track.uri for track in tracks if track.uri]
        audio_features = fetch_audio_features(client, track_uris)
        
        # Create and display audio features plot
        if audio_features:
            create_audio_features_plot(audio_features)
            
        # Display track table
        display_track_table(tracks, audio_features)
        
        # After displaying the playlist dropdown, add buttons for shuffle and export
        if selected_playlist:
            st.subheader("Playlist Analysis")
            
            # Display basic playlist info
            st.write(f"**Playlist:** {selected_playlist.name}")
            st.write(f"**Tracks:** {len(tracks)}")
            
            # Add buttons for shuffle and export
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Shuffle Playlist"):
                    try:
                        with st.spinner("Shuffling playlist..."):
                            shuffle_playlist(client, selected_playlist.id)
                            st.success("Playlist shuffled successfully!")
                    except Exception as e:
                        st.error(f"Error shuffling playlist: {e}")
            
            with col2:
                if st.button("Export Analysis"):
                    try:
                        with st.spinner("Exporting analysis..."):
                            export_analysis(tracks, audio_features)
                            st.success("Analysis exported successfully!")
                    except Exception as e:
                        st.error(f"Error exporting analysis: {e}")
            
            # Additional Features
            st.subheader("Additional Features")
            
            # Create three columns for the new buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Get Recommendations"):
                    try:
                        with st.spinner("Getting recommendations..."):
                            recommendations = get_playlist_recommendations(client, selected_playlist.id)
                            if recommendations:
                                st.success(f"Found {len(recommendations)} recommended tracks!")
                                st.write("Recommended Tracks:")
                                for track in recommendations:
                                    genre_text = f" ({', '.join(track.genres)})" if track.genres else ""
                                    st.write(f"- {track.name} by {track.artist}{genre_text}")
                            else:
                                st.warning("No recommendations found. Try selecting a different playlist.")
                    except Exception as e:
                        st.error(f"Error getting recommendations: {e}")
            
            with col2:
                if st.button("Analyze Track"):
                    if tracks:
                        selected_track = st.selectbox(
                            "Select a track to analyze",
                            options=tracks,
                            format_func=lambda x: f"{x.name} by {x.artist}"
                        )
                        if selected_track:
                            try:
                                with st.spinner("Analyzing track..."):
                                    analysis = get_audio_analysis(client, selected_track.id)
                                    if analysis:
                                        st.write("Audio Analysis:")
                                        st.json(analysis)
                                    else:
                                        st.warning("No audio analysis available for this track.")
                            except Exception as e:
                                st.error(f"Error analyzing track: {e}")
                    else:
                        st.warning("No tracks available for analysis.")
            
            with col3:
                if st.button("Artist Details"):
                    if tracks:
                        selected_track = st.selectbox(
                            "Select a track to view artist details",
                            options=tracks,
                            format_func=lambda x: f"{x.name} by {x.artist}",
                            key="artist_select"
                        )
                        if selected_track and selected_track.artist_id:
                            try:
                                with st.spinner("Fetching artist details..."):
                                    details = get_artist_details(client, selected_track.artist_id)
                                    if details:
                                        st.write("Artist Information:")
                                        st.write(f"Name: {details['info']['name']}")
                                        st.write(f"Popularity: {details['info']['popularity']}")
                                        st.write(f"Genres: {', '.join(details['info']['genres'])}")
                                        
                                        st.write("\nTop Tracks:")
                                        for track in details['top_tracks'][:5]:
                                            st.write(f"- {track['name']}")
                                        
                                        st.write("\nRelated Artists:")
                                        for artist in details['related_artists'][:5]:
                                            st.write(f"- {artist['name']}")
                                    else:
                                        st.warning("No artist details available.")
                            except Exception as e:
                                st.error(f"Error fetching artist details: {e}")
                        else:
                            st.warning("No artist ID available for this track.")
                    else:
                        st.warning("No tracks available for artist details.")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 