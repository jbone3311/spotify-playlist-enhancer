# Spotify Playlist Enhancer

> **Status** ⚙️ Playlist Browser & Liked-Songs Loader implemented
> **Stack** Python 3 · Spotipy · LLM Analysis

## Key Features

1. **Playlist & Library Browser** – Lists every playlist and your entire "Liked Songs" for one-click selection.
2. **Audio Feature Analysis** – Analyzes BPM, energy, danceability, valence and key for each track via Spotify's audio-features API.
3. **Tempo Buckets** – Auto-groups tracks into Slow (<90 BPM), Medium (90-140 BPM) and Fast (>140 BPM) playlists.
4. **Energy Buckets** – Optional low / mid / high energy splits using Spotify's energy score.
5. **Auto-Create Playlists** – Builds new private playlists named Auto: and fills them in batches of 100 tracks.
6. **In-Place Shuffle** – Randomizes the order of any selected playlist and writes it back to Spotify.
7. **LLM Recommendations** – Uses AI to suggest similar tracks based on audio features and metadata.
8. **Stats Dashboard** – Displays average BPM, energy, and key distribution for any analyzed set.
9. **JSON Export** – One-click download of the full analysis and bucket assignments.
10. **Dual Interface** – Command-line script for power users and a Streamlit web UI with check-boxes and progress bars.

---

## 1 Project Goal

A data analysis tool that enhances your Spotify library through AI-powered insights and automated organization. This tool focuses on metadata analysis and playlist management - it does not handle audio playback or streaming.

---

## 2 Feature Catalogue

| #     | Feature                        | API Endpoints                                                    | UI Exposure                   | Description                                                                                            |
| ----- | ------------------------------ | ---------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| F‑1 ✅ | **Playlist Browser**           | GET /v1/me/playlists                                             | Dropdown / CLI list           | Fetch & paginate all playlists.                                                                        |
| F‑2 ✅ | **Liked‑Songs Loader**         | GET /v1/me/tracks                                                | Button: _Analyze Liked Songs_ | Pull entire Saved Library (50‑track paging).                                                           |
| F‑3 ✅ | **Track Analyzer**             | GET /v1/audio-features                                           | Background                    | Batch‑fetch BPM, energy, danceability, valence, key.                                                   |
| F‑4   | **Tempo Bucketer**             | —                                                                | Automatic                     | Classify tracks: _Slow_ <90 BPM, _Medium_ 90‑140, _Fast_ \>140.                                        |
| F‑5   | **Energy Bucketer**            | —                                                                | Checkbox                      | Classify by energy: _Low_ <0.33, _Mid_ 0.33‑0.66, _High_ \>0.66.                                       |
| F‑6   | **Auto‑Create Playlists**      | POST /v1/users/{uid}/playlists\`\`POST /v1/playlists/{id}/tracks | Background                    | For every bucket, build a private playlist named Auto:<Bucket>.                                        |
| F‑7   | **Playlist Shuffle**           | PUT /v1/playlists/{id}/tracks                                    | Button / CLI flag             | Retrieve URIs, randomise, replace items.                                                               |
| F‑8   | **LLM Recommendations**        | GET /v1/recommendations                                          | Button _Enhance_              | Use AI to suggest similar tracks based on audio features and metadata.                                 |
| F‑9 ✅ | **Stats Dashboard**            | —                                                                | Streamlit main panel          | Show track‑count, avg BPM, avg Energy, key distribution.                                               |
| F‑10 ✅ | **JSON Export**                | —                                                                | Download link                 | Export analysis outcome (buckets.json).                                                                |

> **All features are optional toggles except F‑1 & F‑3 which are required.**

---

## 3 User Flows

### 3.1 CLI

1. `python main.py`
2. Choose _Playlist_ **OR** `L` for _Liked Songs_.
3. Toggle enhancements via prompts (Tempo buckets, Energy buckets, LLM Recommendations, Shuffle, JSON export).
4. Script prints summary table plus any created playlist IDs.

### 3.2 Streamlit UI

* **Sidebar**  
   * Playlist dropdown (plus _Liked Songs_ option)  
   * Check‑boxes → Tempo Buckets, Energy Buckets, LLM Recommendations, Shuffle, JSON Export  
   * Slider → # of recommended tracks to add (for _LLM Recommendations_)  
   * **Run** button
* **Main Panel**  
   * Step progress / spinners  
   * Stats dashboard (avg BPM, Energy, distribution charts)  
   * Success alerts with links to new playlists  
   * _Download JSON_ button (if export selected)

---

## 4 System Modules

```
core.py        <‑‑ auth, Spotify helpers, analysis, buckets, shuffle
cli.py         <‑‑ arg‑parsing / interactive prompts
app.py         <‑‑ Streamlit UI
export.py      <‑‑ JSON serialization utilities
requirements.txt
docker-compose.yml (optional)
```

---

## 5 LLM Coding Tasks

| ID   | Module · Function            | Done when …                                                |
| ---- | ---------------------------- | ---------------------------------------------------------- |
| T‑01 | init_spotify_client() ✅    | Auth succeeds, token refreshes, scopes correct.            |
| T‑02 | fetch_user_playlists() ✅   | Returns \[{id,name,track_total}\]. Handles paging.        |
| T‑03 | fetch_liked_tracks() ✅     | Returns all Saved track URIs.                              |
| T‑04 | get_playlist_track_uris() ✅ | Returns full URI list for given playlist.                  |
| T‑05 | fetch_audio_features() ✅   | Batch size ≤100; skips None.                               |
| T‑06 | bucket_by_tempo()          | Dict with keys Slow/Medium/Fast.                           |
| T‑07 | bucket_by_energy()         | Dict Low/Mid/High.                                         |
| T‑08 | create_playlist()           | Returns playlist ID.                                       |
| T‑09 | add_tracks()                | Adds all URIs in ≤100‑track chunks.                        |
| T‑10 | shuffle_playlist()          | Replaces items with shuffled order.                        |
| T‑11 | get_llm_recommendations()   | Returns ≤N URIs based on AI analysis of features.          |
| T‑12 | export_json() ✅           | Writes analysis + bucket info to file path.                |
| T‑13 | cli.main() ✅              | Full CLI flow per §3.1.                                    |
| T‑14 | app.py ✅                  | Streamlit UI per §3.2.                                     |

All functions MUST have type hints, docstrings, and log info ≥DEBUG level.

---

## 6 Environment

| Variable                | Purpose        |
| ----------------------- | -------------- |
| SPOTIFY_CLIENT_ID     | app client ID  |
| SPOTIFY_CLIENT_SECRET | app secret     |
| SPOTIFY_REDIRECT_URI  | OAuth redirect |

Sample `.env.example`:

```
SPOTIFY_CLIENT_ID=your-id
SPOTIFY_CLIENT_SECRET=your-secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

---

## 7 Quick Start

```bash
# Clone & install
$ git clone https://github.com/your-user/spotify-playlist-enhancer.git
$ cd spotify-playlist-enhancer
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt
$ cp .env.example .env  # add credentials

# Run CLI
$ python cli.py

# Run Web UI
$ streamlit run app.py
```

---

## 8 Contributing

All PRs must map to a **single feature ID (F‑#)** and update its corresponding **task ID (T‑##)**. Include docstring unit tests if practical. Continuous Integration will run `pytest` and `ruff` lint. 