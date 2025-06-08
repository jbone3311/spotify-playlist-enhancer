# Spotify Playlist Enhancer

A powerful tool that super-charges your Spotify library without leaving Spotify. All logic relies exclusively on Spotify's Web API – no third-party audio services, no client playback hacks.

## Features

1. **Playlist & Library Browser** – Lists every playlist and your entire "Liked Songs" for one-click selection.
2. **Audio Analysis** – Pulls BPM, energy, danceability, valence and key for each track via Spotify's audio-features API.
3. **Tempo Buckets** – Auto-groups tracks into Slow (<90 BPM), Medium (90-140 BPM) and Fast (>140 BPM) playlists.
4. **Energy Buckets** – Optional low / mid / high energy splits using Spotify's energy score.
5. **Auto-Create Playlists** – Builds new private playlists named Auto:<Bucket> and fills them in batches of 100 tracks.
6. **In-Place Shuffle** – Randomizes the order of any selected playlist and writes it back to Spotify.
7. **AI Recommendations** – Adds up to N similar tracks (seeded by the playlist) after you preview and approve them.
8. **Stats Dashboard** – Displays average BPM, energy, and key distribution for any analyzed set.
9. **JSON Export** – One-click download of the full analysis and bucket assignments.
10. **Dual Interface** – Command-line script for power users and a Streamlit web UI with check-boxes and progress bars.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/spotify-playlist-enhancer.git
   cd spotify-playlist-enhancer
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Spotify API credentials:
   ```bash
   SPOTIFY_CLIENT_ID=your-client-id
   SPOTIFY_CLIENT_SECRET=your-client-secret
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

5. Run the application:

   - CLI version:
     ```bash
     python cli.py
     ```

   - Web UI version:
     ```bash
     streamlit run app.py
     ```

## Usage

### CLI Interface

```bash
python cli.py [--tempo-buckets] [--energy-buckets] [--enhance] [--shuffle] [--export]
```

Options:
- `--tempo-buckets`: Create tempo-based playlists
- `--energy-buckets`: Create energy-based playlists
- `--enhance`: Add recommended tracks
- `--shuffle`: Shuffle the playlist
- `--export`: Export analysis to JSON

### Web Interface

1. Launch the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Select a playlist or "Liked Songs" from the dropdown
3. Choose enhancement options from the sidebar
4. Click "Run Analysis" to process

## Development

### Project Structure

```
.
├── app.py              # Streamlit web interface
├── cli.py             # Command-line interface
├── core.py            # Core functionality
├── export.py          # JSON serialization utilities
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

### Adding Features

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 