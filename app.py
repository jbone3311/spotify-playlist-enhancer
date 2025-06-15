"""
Streamlit web interface for Spotify Playlist Enhancer.
A data analysis and LLM-powered tool for playlist management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime

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
    page_title="Spotify Playlist Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def format_duration(ms: int) -> str:
    """Format duration in milliseconds to MM:SS format."""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
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

def display_track_table(tracks: List[dict], features: Dict[str, dict]) -> None:
    """Display tracks in a spreadsheet format with analysis data."""
    if not tracks:
        st.warning("No tracks to display.")
        return
        
    # Create DataFrame with track info and audio features
    data = []
    for track in tracks:
        # Basic track info from Spotify API
        track_info = {
            'Name': track['name'],
            'Artists': ', '.join(artist['name'] for artist in track['artists']),
            'Album': track['album']['name'],
            'Album Type': track['album']['album_type'],
            'Release Date': track['album']['release_date'],
            'Duration': format_duration(track['duration_ms']),
            'Duration (ms)': track['duration_ms'],
            'Popularity': track['popularity'],
            'Explicit': track['explicit'],
            'Track Number': track['track_number'],
            'Disc Number': track['disc_number'],
            'Preview URL': track['preview_url'] if track['preview_url'] else 'N/A',
            'ISRC': track['external_ids'].get('isrc', 'N/A'),
            'Available Markets': len(track['available_markets']),
            'URI': track['uri']
        }
        
        # Add audio features if available (exactly as returned by Spotify API)
        if track['uri'] in features:
            feature = features[track['uri']]
            track_info.update({
                'Danceability': feature['danceability'],
                'Energy': feature['energy'],
                'Key': feature['key'],
                'Loudness': feature['loudness'],
                'Mode': feature['mode'],
                'Speechiness': feature['speechiness'],
                'Acousticness': feature['acousticness'],
                'Instrumentalness': feature['instrumentalness'],
                'Liveness': feature['liveness'],
                'Valence': feature['valence'],
                'Tempo': feature['tempo'],
                'Time Signature': feature['time_signature']
            })
        
        data.append(track_info)
    
    df = pd.DataFrame(data)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Track Details", "Audio Features", "Analysis"])
    
    with tab1:
        # Add search and filter controls
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search tracks", "")
        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Name", "Artists", "Album", "Duration", "Popularity", "Release Date"]
            )
        
        # Filter and sort the dataframe
        if search:
            mask = df.apply(lambda x: x.astype(str).str.contains(search, case=False).any(), axis=1)
            df_display = df[mask]
        else:
            df_display = df
            
        if sort_by:
            df_display = df_display.sort_values(by=sort_by)
        
        # Display track information in a more organized way
        for _, track in df_display.iterrows():
            with st.expander(f"{track['Name']} - {track['Artists']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Basic Information**")
                    st.write(f"Album: {track['Album']}")
                    st.write(f"Release Date: {track['Release Date']}")
                    st.write(f"Duration: {track['Duration']}")
                    st.write(f"Popularity: {track['Popularity']}")
                    st.write(f"Explicit: {'Yes' if track['Explicit'] else 'No'}")
                    st.write(f"Track Number: {track['Track Number']}")
                    st.write(f"Disc Number: {track['Disc Number']}")
                    st.write(f"Available Markets: {track['Available Markets']}")
                
                with col2:
                    if 'Tempo' in track:
                        st.write("**Audio Features**")
                        st.write(f"Danceability: {track['Danceability']:.2f}")
                        st.write(f"Energy: {track['Energy']:.2f}")
                        st.write(f"Loudness: {track['Loudness']:.2f} dB")
                        st.write(f"Speechiness: {track['Speechiness']:.2f}")
                        st.write(f"Acousticness: {track['Acousticness']:.2f}")
                        st.write(f"Instrumentalness: {track['Instrumentalness']:.2f}")
                        st.write(f"Liveness: {track['Liveness']:.2f}")
                        st.write(f"Valence: {track['Valence']:.2f}")
                        st.write(f"Tempo: {track['Tempo']:.1f} BPM")
                        st.write(f"Time Signature: {track['Time Signature']}/4")
        
        # Export button
        if st.button("Export Analysis to JSON"):
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "tracks": data,
                "audio_features": features
            }
            
            json_str = json.dumps(export_data, indent=2)
            st.download_button(
                label="Download Analysis",
                data=json_str,
                file_name=f"playlist_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with tab2:
        if 'Tempo' in df:
            # Create a grid of audio feature plots
            st.subheader("Audio Features Distribution")
            
            # First row: Tempo and Energy
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Tempo', 'Tempo Distribution (BPM)'),
                    use_container_width=True
                )
            with col2:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Energy', 'Energy Distribution'),
                    use_container_width=True
                )
            
            # Second row: Danceability and Valence
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Danceability', 'Danceability Distribution'),
                    use_container_width=True
                )
            with col2:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Valence', 'Valence Distribution'),
                    use_container_width=True
                )
            
            # Third row: Acousticness and Instrumentalness
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Acousticness', 'Acousticness Distribution'),
                    use_container_width=True
                )
            with col2:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Instrumentalness', 'Instrumentalness Distribution'),
                    use_container_width=True
                )
            
            # Fourth row: Speechiness and Liveness
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Speechiness', 'Speechiness Distribution'),
                    use_container_width=True
                )
            with col2:
                st.plotly_chart(
                    create_audio_features_plot(df, 'Liveness', 'Liveness Distribution'),
                    use_container_width=True
                )
            
            # Fifth row: Loudness
            st.plotly_chart(
                create_audio_features_plot(df, 'Loudness', 'Loudness Distribution (dB)'),
                use_container_width=True
            )
    
    with tab3:
        if 'Tempo' in df:
            # Create correlation heatmap
            st.subheader("Audio Features Correlation")
            audio_features = [
                'Danceability', 'Energy', 'Loudness', 'Speechiness',
                'Acousticness', 'Instrumentalness', 'Liveness', 'Valence',
                'Tempo'
            ]
            
            corr = df[audio_features].corr()
            fig = px.imshow(
                corr,
                title="Audio Features Correlation",
                color_continuous_scale="RdBu",
                aspect="auto"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display key statistics
            st.subheader("Playlist Statistics")
            
            # Basic Statistics
            st.write("### Basic Information")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tracks", len(df))
                st.metric("Unique Artists", df['Artists'].nunique())
                st.metric("Unique Albums", df['Album'].nunique())
            
            with col2:
                st.metric("Average Duration", format_duration(int(df['Duration (ms)'].mean())))
                st.metric("Average Popularity", f"{df['Popularity'].mean():.1f}")
                st.metric("Total Duration", format_duration(int(df['Duration (ms)'].sum())))
            
            with col3:
                st.metric("Explicit Tracks", df['Explicit'].sum())
                st.metric("Available Markets (avg)", f"{df['Available Markets'].mean():.1f}")
                st.metric("Release Date Range", f"{df['Release Date'].min()} to {df['Release Date'].max()}")
            
            with col4:
                st.metric("Album Types", df['Album Type'].nunique())
                st.metric("Tracks with Preview", df['Preview URL'].ne('N/A').sum())
                st.metric("Tracks with ISRC", df['ISRC'].ne('N/A').sum())
            
            # Audio Features Statistics
            st.write("### Audio Features Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Tempo**")
                st.write(f"Average: {df['Tempo'].mean():.1f} BPM")
                st.write(f"Range: {df['Tempo'].min():.1f} - {df['Tempo'].max():.1f} BPM")
                st.write(f"Standard Deviation: {df['Tempo'].std():.1f} BPM")
                
                st.write("**Energy**")
                st.write(f"Average: {df['Energy'].mean():.2f}")
                st.write(f"Range: {df['Energy'].min():.2f} - {df['Energy'].max():.2f}")
                st.write(f"Standard Deviation: {df['Energy'].std():.2f}")
                
                st.write("**Danceability**")
                st.write(f"Average: {df['Danceability'].mean():.2f}")
                st.write(f"Range: {df['Danceability'].min():.2f} - {df['Danceability'].max():.2f}")
                st.write(f"Standard Deviation: {df['Danceability'].std():.2f}")
            
            with col2:
                st.write("**Loudness**")
                st.write(f"Average: {df['Loudness'].mean():.1f} dB")
                st.write(f"Range: {df['Loudness'].min():.1f} - {df['Loudness'].max():.1f} dB")
                st.write(f"Standard Deviation: {df['Loudness'].std():.1f} dB")
                
                st.write("**Valence**")
                st.write(f"Average: {df['Valence'].mean():.2f}")
                st.write(f"Range: {df['Valence'].min():.2f} - {df['Valence'].max():.2f}")
                st.write(f"Standard Deviation: {df['Valence'].std():.2f}")
                
                st.write("**Acousticness**")
                st.write(f"Average: {df['Acousticness'].mean():.2f}")
                st.write(f"Range: {df['Acousticness'].min():.2f} - {df['Acousticness'].max():.2f}")
                st.write(f"Standard Deviation: {df['Acousticness'].std():.2f}")

def main() -> None:
    """Main Streamlit application."""
    st.title("📊 Spotify Playlist Analyzer")
    st.markdown("A data analysis and LLM-powered tool for playlist management")
    
    # Create a container for status messages at the bottom
    status_container = st.container()
    
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
            st.info("Ready to analyze playlists")
    
    # Sidebar controls
    st.sidebar.header("Analysis Options")
    
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
    
    # Analysis options
    st.sidebar.subheader("Analysis Options")
    tempo_buckets = st.sidebar.checkbox("Create Tempo Buckets")
    energy_buckets = st.sidebar.checkbox("Create Energy Buckets")
    llm_recommendations = st.sidebar.checkbox("Get LLM Recommendations")
    shuffle = st.sidebar.checkbox("Shuffle Playlist")
    
    if llm_recommendations:
        num_recommendations = st.sidebar.slider(
            "Number of Recommendations",
            min_value=1,
            max_value=20,
            value=5
        )
    
    # Process button
    if st.sidebar.button("Run Analysis"):
        with status_container:
            st.info("Starting analysis...")
            
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
                
                st.success(f"Found {len(track_uris)} tracks")
                
                # Fetch track details
                st.info("Fetching track details...")
                tracks = []
                for i in range(0, len(track_uris), 50):
                    batch = track_uris[i:i + 50]
                    results = st.session_state.client.tracks(batch)
                    tracks.extend(results['tracks'])
                st.success(f"Fetched details for {len(tracks)} tracks")
                
                # Fetch audio features
                st.info("Analyzing audio features...")
                features = fetch_audio_features(
                    st.session_state.client,
                    track_uris
                )
                st.success(f"Analyzed {len(features)} tracks")
                
                # Display results
                st.header("Track Analysis")
                display_track_table(tracks, features)
                
                # TODO: Implement remaining features
                if tempo_buckets:
                    st.info("Tempo bucketing not yet implemented")
                if energy_buckets:
                    st.info("Energy bucketing not yet implemented")
                if llm_recommendations:
                    st.info("LLM recommendations not yet implemented")
                if shuffle:
                    st.info("Playlist shuffle not yet implemented")
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")

if __name__ == '__main__':
    main() 