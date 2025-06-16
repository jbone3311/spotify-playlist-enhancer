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

from core import (
    TrackMetadata,
    PlaylistInfo,
    fetch_user_playlists,
    fetch_playlist_tracks_with_metadata,
    fetch_liked_tracks,
    fetch_audio_features,
    fetch_artist_genres
)

# Load environment variables
load_dotenv()

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

def display_track_table(tracks: List[TrackMetadata], features: Dict[str, dict]) -> None:
    """Display tracks in a spreadsheet format with analysis data."""
    if not tracks:
        st.warning("No tracks to display.")
        return
        
    # Create DataFrame with track info and audio features
    data = []
    for track_meta in tracks:
        track = track_meta.track
        # Basic track info from Spotify API
        track_info = {
            'Name': track['name'],
            'Artists': ', '.join(artist['name'] for artist in track['artists']),
            'Album': track['album']['name'],
            'Album Type': track['album']['album_type'],
            'Release Date': track['album']['release_date'],
            'Added At': track_meta.added_at,
            'Duration': format_duration(track['duration_ms']),
            'Duration (ms)': track['duration_ms'],
            'Popularity': track['popularity'],
            'Explicit': track['explicit'],
            'Track Number': track['track_number'],
            'Disc Number': track['disc_number'],
            'Preview URL': track['preview_url'] if track['preview_url'] else 'N/A',
            'ISRC': track['external_ids'].get('isrc', 'N/A'),
            'Available Markets': len(track['available_markets']),
            'URI': track['uri'],
            'Genres': ', '.join(track_meta.genres) if track_meta.genres else 'N/A'
        }
        
        # Add audio features if available
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
    tab1, tab2, tab3, tab4 = st.tabs(["Track Details", "Audio Features", "Analysis", "Genres"])
    
    with tab1:
        # Display track details in a spreadsheet format
        st.dataframe(
            df[[
                'Name', 'Artists', 'Album', 'Release Date', 'Added At',
                'Duration', 'Popularity', 'Explicit', 'Genres'
            ]],
            use_container_width=True
        )
        
        # Allow sorting by any column
        st.subheader("Sort Tracks")
        sort_by = st.selectbox(
            "Sort by",
            ['Name', 'Artists', 'Album', 'Release Date', 'Added At', 'Duration', 'Popularity', 'Genres']
        )
        sort_order = st.radio("Sort order", ["Ascending", "Descending"])
        
        sorted_df = df.sort_values(
            by=sort_by,
            ascending=(sort_order == "Ascending")
        )
        
        # Display sorted results
        st.dataframe(
            sorted_df[[
                'Name', 'Artists', 'Album', 'Release Date', 'Added At',
                'Duration', 'Popularity', 'Explicit', 'Genres'
            ]],
            use_container_width=True
        )
        
        # Detailed view of selected track
        st.subheader("Track Details")
        selected_track = st.selectbox(
            "Select a track to view details",
            sorted_df['Name'].tolist()
        )
        
        track = sorted_df[sorted_df['Name'] == selected_track].iloc[0]
        
        with st.expander(f"{track['Name']} - {track['Artists']}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Basic Information**")
                st.write(f"Album: {track['Album']}")
                st.write(f"Release Date: {track['Release Date']}")
                st.write(f"Added to Playlist: {track['Added At']}")
                st.write(f"Duration: {track['Duration']}")
                st.write(f"Popularity: {track['Popularity']}")
                st.write(f"Explicit: {'Yes' if track['Explicit'] else 'No'}")
                st.write(f"Track Number: {track['Track Number']}")
                st.write(f"Disc Number: {track['Disc Number']}")
                st.write(f"Available Markets: {track['Available Markets']}")
                st.write(f"Genres: {track['Genres']}")
            
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
                else:
                    st.warning("Audio features not available for this track")
    
    with tab2:
        if 'Tempo' in df.columns:
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
        else:
            st.warning("Audio features are not available for any tracks in this playlist")
    
    with tab3:
        st.subheader("Playlist Statistics")
        
        # Basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tracks", len(df))
            st.metric("Unique Artists", df['Artists'].nunique())
        with col2:
            st.metric("Unique Albums", df['Album'].nunique())
            st.metric("Average Duration", format_duration(int(df['Duration (ms)'].mean())))
        with col3:
            st.metric("Average Popularity", f"{df['Popularity'].mean():.1f}")
            if 'Tempo' in df:
                st.metric("Average Tempo", f"{df['Tempo'].mean():.1f} BPM")
        
        # Release date range
        st.subheader("Release Date Range")
        release_dates = pd.to_datetime(df['Release Date'], errors='coerce')
        if not release_dates.isna().all():
            st.write(f"From {release_dates.min().strftime('%Y-%m-%d')} to {release_dates.max().strftime('%Y-%m-%d')}")
        
        # Album types distribution
        st.subheader("Album Types")
        album_types = df['Album Type'].value_counts()
        st.bar_chart(album_types)
        
        # Preview availability
        st.subheader("Preview Availability")
        preview_available = df['Preview URL'].ne('N/A').sum()
        st.write(f"{preview_available} tracks have previews available")
    
    with tab4:
        st.subheader("Genre Analysis")
        
        # Get all genres and their counts
        all_genres = []
        for genres in df['Genres']:
            if genres != 'N/A':
                all_genres.extend([g.strip() for g in genres.split(',')])
        
        if all_genres:
            genre_counts = pd.Series(all_genres).value_counts()
            
            # Display top genres
            st.write("Top Genres")
            st.bar_chart(genre_counts.head(20))
            
            # Display genre distribution
            st.write("Genre Distribution")
            fig = px.pie(
                values=genre_counts.values,
                names=genre_counts.index,
                title="Genre Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Display tracks by genre
            st.write("Tracks by Genre")
            selected_genre = st.selectbox(
                "Select a genre to view tracks",
                sorted(genre_counts.index)
            )
            
            genre_tracks = df[df['Genres'].str.contains(selected_genre, na=False)]
            st.dataframe(
                genre_tracks[['Name', 'Artists', 'Album', 'Release Date', 'Popularity']],
                use_container_width=True
            )
        else:
            st.warning("No genre information available for tracks in this playlist")

def main() -> None:
    """Main Streamlit app entry point."""
    st.title("📊 Spotify Playlist Analyzer")
    st.markdown("A data analysis and LLM-powered tool for playlist management")
    
    # Initialize session state
    if 'client' not in st.session_state:
        try:
            logger.info("Initializing Spotify client...")
            # Initialize Spotify client with minimal scopes for playlist management
            scopes = [
                'playlist-read-private',
                'playlist-modify-private',
                'user-library-read',
                'user-library-modify',
                'user-read-private',
                'user-read-email',
                'user-top-read',
                'user-read-recently-played',
                'user-read-currently-playing',
                'user-read-playback-state',
                'user-modify-playback-state',
                'streaming',
                'app-remote-control',
                'user-read-playback-position'
            ]
            
            try:
                sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
                    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
                    scope=' '.join(scopes),
                    cache_path='.spotify_cache'
                ))
                st.session_state.client = sp
                logger.info("Successfully initialized Spotify client")
                st.sidebar.success("Connected to Spotify")
            except Exception as e:
                logger.error(f"Failed to initialize Spotify client: {e}", exc_info=True)
                st.sidebar.error(f"Failed to connect to Spotify: {str(e)}")
                return
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}", exc_info=True)
            st.sidebar.error(f"Failed to connect to Spotify: {str(e)}")
            return
    
    # Sidebar controls
    st.sidebar.header("Analysis Options")
    
    # Fetch playlists
    st.sidebar.info("Fetching your playlists...")
    try:
        logger.info("Fetching user playlists...")
        playlists = fetch_user_playlists(st.session_state.client)
        if not playlists:
            logger.warning("No playlists found")
            st.sidebar.warning("No playlists found. Please create a playlist in Spotify first.")
            return
            
        # Get playlist names for selection
        playlist_names = ["Liked Songs"] + [p.name for p in playlists]
        logger.info(f"Found {len(playlists)} playlists: {playlist_names}")
        st.sidebar.success(f"Found {len(playlists)} playlists")
    except Exception as e:
        logger.error(f"Failed to fetch playlists: {e}", exc_info=True)
        st.sidebar.error(f"Failed to fetch playlists: {str(e)}")
        return
    
    # Playlist selection
    selected_playlist = st.sidebar.selectbox(
        "Select Playlist",
        playlist_names
    )
    logger.info(f"Selected playlist: {selected_playlist}")
    
    # Status container for progress messages
    status_container = st.empty()
    
    # Process button
    if st.sidebar.button("Run Analysis"):
        with status_container:
            st.info("Starting analysis...")
            
            try:
                # Fetch tracks
                if selected_playlist == "Liked Songs":
                    logger.info("Fetching liked tracks...")
                    st.info("Fetching your liked tracks...")
                    track_uris = fetch_liked_tracks(st.session_state.client)
                    logger.info(f"Found {len(track_uris)} liked tracks")
                    
                    # For liked songs, we don't have added_at metadata
                    tracks = []
                    for i in range(0, len(track_uris), 50):
                        logger.info(f"Fetching track details for batch {i//50 + 1}")
                        batch = track_uris[i:i + 50]
                        results = st.session_state.client.tracks(batch)
                        for track in results['tracks']:
                            tracks.append(TrackMetadata(
                                uri=track['uri'],
                                added_at="N/A",  # Liked songs don't have added_at
                                track=track
                            ))
                else:
                    logger.info(f"Fetching tracks from playlist: {selected_playlist}")
                    st.info(f"Fetching tracks from {selected_playlist}...")
                    playlist = playlists[playlist_names.index(selected_playlist) - 1]
                    tracks = fetch_playlist_tracks_with_metadata(
                        st.session_state.client,
                        playlist.id
                    )
                
                if not tracks:
                    logger.warning("No tracks found in selected playlist")
                    st.warning("No tracks found in the selected playlist.")
                    return
                    
                logger.info(f"Successfully fetched {len(tracks)} tracks")
                st.success(f"Found {len(tracks)} tracks")
                
                # Fetch audio features
                logger.info("Starting audio features analysis...")
                st.info("Analyzing audio features...")
                track_uris = [track.uri for track in tracks]
                try:
                    features = fetch_audio_features(
                        st.session_state.client,
                        track_uris
                    )
                    logger.info(f"Successfully analyzed {len(features)} tracks")
                    st.success(f"Analyzed {len(features)} tracks")
                except Exception as e:
                    logger.error(f"Failed to fetch audio features: {e}", exc_info=True)
                    st.error(f"Failed to fetch audio features: {str(e)}")
                    st.warning("Some features may be missing. The analysis will be incomplete.")
                    features = {}
                
                # Display results
                logger.info("Displaying track analysis...")
                st.header("Track Analysis")
                display_track_table(tracks, features)
                
            except Exception as e:
                logger.error(f"Error during analysis: {e}", exc_info=True)
                st.error(f"Error during analysis: {str(e)}")

if __name__ == '__main__':
    main() 