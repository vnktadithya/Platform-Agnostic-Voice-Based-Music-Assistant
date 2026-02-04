# Backend Documentation

The brain of **SAM (Self Adaptive Music Intelligence)**. This backend is a high-performance, asynchronous system built with **FastAPI**, designed to handle real-time voice processing, complex natural language understanding, and seamless music platform integration.

## 🏗️ Architecture Deep Dive

The backend follows a **Clean Architecture** principle, separating concerns into distinct layers:

### 1. The Core Loop
1.  **Input**: Audio is received via `multipart/form-data` at `/v1/voice/process`.
2.  **Transliteration (STT)**: audio is sent to **Groq (Whisper v3)**. We use a specialized system prompt to force **transliteration** (e.g., Telugu words written in English script). This ensures compatibility with music search APIs that primarily index in Latin characters.
3.  **Understanding (LLM)**: The text is processed by **Groq (Llama 3)**. The `DialogManager` maintains conversation context in a sliding window to support multi-turn interactions.
4.  **Action Dispatch**: If a music command is detected, `MusicActionService` dynamically routes the request to the active platform (Spotify or SoundCloud).
5.  **Feedback**: A response is generated, synthesized to speech (if enabled), and sent back to the frontend alongside the action payload.

### 2. Intelligent Search Layer
To optimize latency and reduce API rate limits, we implement a multi-tiered search strategy:
*   **Tier 1: Redis Cache**: Checks if this specific query has been resolved recently. (Fastest)
*   **Tier 2: Local Database**: Checks `SearchCache` table for historical matches.
    *   **Normalization**: Queries are stripped of special characters and lowercased (e.g., "PlaY... Nuvvu-Nenantu!" -> "play nuvvu nenantu") before caching. This increases cache hit rates by resolving minor speech variations to the same entry.
*   **Tier 3: Platform API**: Falls back to the external API (Spotify/SoundCloud).
    *   *Result*, *Action*, and *Metadata* are then cached back to Tier 1 & 2 for future speed.

### 3. Background Synchronization (Celery)
SAM doesn't just react; it proactively manages your library.
*   **Worker Pool**: Running on `gevent` for extensive I/O concurrency.
*   **Periodic Tasks**:
    *   `refresh_all_spotify_libraries`: Every **6 hours**, keeps user playlists and liked songs in sync.
    *   `purge_expired_search_cache`: Every **24 hours**, cleans up old cache entries to save DB space.

---

## 🔧 Setup & Installation

### Prerequisites
*   Python 3.10+
*   Redis Server (Must be running)
*   PostgreSQL Database

### 1. Virtual Environment
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 2. Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Migration
The application uses SQLAlchemy. Tables are automatically created on startup in `main.py`, but ensure your database exists.

---

## 🔑 Environment Variables

Create a `.env` file in the root. **All credentials are required for full functionality.**

### Core Infrastructure
| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. <br>`postgresql://user:pass@localhost:5432/dbname` |
| `REDIS_HOST` | Host for Redis (Cache & Celery). Default: `localhost` |
| `REDIS_PORT` | Port for Redis. Default: `6379` |
| `SESSION_SECRET_KEY`| Random string for encrypting session cookies. |

### AI Services
| Variable | Description | Get It Here |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Powers both STT and LLM. We chose Groq for its **unmatched inference speed**. | [Groq Console](https://console.groq.com/keys) |
| `ELEVENLABS_API_KEY`| (Optional) For high-quality TTS voices. | [ElevenLabs](https://elevenlabs.io/) |

### Music Platforms
**Spotify Configuration**
*   **Why**: Required for remote control and library sync.
*   **Redirect URI**: Must match `http://localhost:8000/adpter/spotify/callback`.
*   [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
    *   `SPOTIFY_CLIENT_ID`
    *   `SPOTIFY_CLIENT_SECRET`
    *   `SPOTIFY_REDIRECT_URI`

**SoundCloud Configuration**
*   **Why**: Enables access to SoundCloud's unique library.
*   **Note**: SoundCloud requires a manually registered app.
    *   `ENABLE_SOUNDCLOUD=true`
    *   `SOUNDCLOUD_CLIENT_ID`
    *   `SOUNDCLOUD_CLIENT_SECRET`
    *   `SOUNDCLOUD_REDIRECT_URI`

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/voice/process` | Main entry point. Handles audio blob, returns text + audio + action. |
| `POST` | `/v1/chat/message` | Text-only interface. Uses the same logic pipeline as voice. |
| `GET` | `/v1/adapter/spotify/login` | Initiates OAuth flow for Spotify. |
| `GET` | `/v1/adapter/spotify/callback` | Handles OAuth code exchange and token storage. |
| `GET` | `/v1/user/status` | Returns current user sync status and connected platforms. |

---

## 🧪 Testing

We adhere to **industry-standard testing practices** using `pytest`. Our test suite covers:

*   **Integration Tests** (`test_integration.py`): Verifies the full chain from API -> Service -> DB.
*   **Unit Tests**:
    *   `test_dialog_manager.py`: Ensures conversation context is maintained.
    *   `test_sequencing.py`: Validates that music commands (Immediate vs Deferred) are sequenced correctly.
    *   `test_data_sync.py`: Checks if playlists are correctly parsed and stored.

**Run Tests:**
```bash
pytest backend/tests
```

---

## 🚀 Running the Services

The backend consists of three distinct processes that must run simultaneously.

**1. API Server (Uvicorn)**
Serves the HTTP endpoints and WebSockets.
```bash
uvicorn backend.main:app --reload
```

**2. Task Worker (Celery)**
Executes heavy background tasks (syncing libraries) without blocking the API.
```bash
celery -A backend.celery_worker worker --loglevel=info --pool=gevent
```

**3. Scheduler (Celery Beat)**
Triggers periodic maintenance tasks (cache purge, sync).
```bash
celery -A backend.celery_worker beat --loglevel=info
```
