"""
Streamlit web interface for Spotify Playlist Enhancer.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional
import json
import logging

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

# Page config
st.set_page_config(
    page_title="Spotify Playlist Enhancer",
    page_icon="🎵",
    layout="wide"
)

def display_stats(features: Dict[str, dict]) -> None:
    """Display analysis statistics and charts."""
    if not features:
        st.warning("No audio features available to analyze.")
        return
        
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame.from_dict(features, orient='index')
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average BPM", f"{df['tempo'].mean():.1f}")
    with col2:
        st.metric("Average Energy", f"{df['energy'].mean():.2f}")
    with col3:
        st.metric("Average Danceability", f"{df['danceability'].mean():.2f}")
    
    # Distribution charts
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(df, x='tempo', title='Tempo Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(df, x='energy', title='Energy Distribution')
        st.plotly_chart(fig, use_container_width=True)

def main() -> None:
    """Main Streamlit application."""
    st.title("🎵 Spotify Playlist Enhancer")
    
    # Status section
    with st.expander("Connection Status", expanded=True):
        if 'client' not in st.session_state:
            try:
                st.info("Initializing Spotify client...")
                st.session_state.client = init_spotify_client()
                st.success("Successfully connected to Spotify!")
            except Exception as e:
                st.error(f"Failed to initialize Spotify client: {e}")
                st.error("Please check your .env file and make sure your credentials are correct.")
                return
        else:
            st.success("Connected to Spotify")
    
    # Sidebar controls
    st.sidebar.header("Options")
    
    # Fetch playlists
    try:
        st.sidebar.info("Fetching your playlists...")
        playlists = fetch_user_playlists(st.session_state.client)
        playlist_names = [p.name for p in playlists]
        playlist_names.insert(0, "Liked Songs")
        
        selected_playlist = st.sidebar.selectbox(
            "Select Playlist",
            playlist_names
        )
        st.sidebar.success(f"Found {len(playlists)} playlists")
    except Exception as e:
        st.error(f"Failed to fetch playlists: {e}")
        return
    
    # Enhancement options
    tempo_buckets = st.sidebar.checkbox("Create Tempo Buckets")
    energy_buckets = st.sidebar.checkbox("Create Energy Buckets")
    enhance = st.sidebar.checkbox("Add Recommended Tracks")
    shuffle = st.sidebar.checkbox("Shuffle Playlist")
    export = st.sidebar.checkbox("Export Analysis")
    
    if enhance:
        num_recommendations = st.sidebar.slider(
            "Number of Recommendations",
            min_value=1,
            max_value=20,
            value=5
        )
    
    # Process button
    if st.sidebar.button("Run Analysis"):
        with st.spinner("Processing..."):
            try:
                # Fetch tracks
                if selected_playlist == "Liked Songs":
                    st.info("Fetching your liked tracks...")
                    track_uris = fetch_liked_tracks(st.session_state.client)
                else:
                    st.info(f"Fetching tracks from {selected_playlist}...")
                    playlist = playlists[playlist_names.index(selected_playlist) - 1]
                    track_uris = get_playlist_track_uris(
                        st.session_state.client,
                        playlist.id
                    )
                
                st.info(f"Found {len(track_uris)} tracks")
                
                # Fetch audio features
                st.info("Analyzing audio features...")
                features = fetch_audio_features(
                    st.session_state.client,
                    track_uris
                )
                
                # Display stats
                display_stats(features)
                
                # TODO: Implement remaining features
                if tempo_buckets:
                    st.info("Tempo bucketing not yet implemented")
                if energy_buckets:
                    st.info("Energy bucketing not yet implemented")
                if enhance:
                    st.info("Track enhancement not yet implemented")
                if shuffle:
                    st.info("Playlist shuffle not yet implemented")
                if export:
                    st.info("JSON export not yet implemented")
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")

if __name__ == '__main__':
    main() 