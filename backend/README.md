# Backend Documentation

The **SAM Backend** is a high-performance, asynchronous FastAPI application that serves as the brain of the voice assistant. It orchestrates the complex interplay between Speech-to-Text (STT), Large Language Models (LLM), and third-party music APIs.

---

## 🏗️ Architecture & Core Loop

The backend prioritizes **latency** and **accuracy**. The core processing loop (`voice_routes.py`) follows a strict pipeline:

### 1. The Voice Pipeline
1.  **Ingestion**: Audio blobs (WebM/WAV) are received via `multipart/form-data` at `/v1/voice/process`.
2.  **Transliteration (STT)**:
    *   **Engine**: Groq (Whisper-large-v3).
    *   **Innovation**: We use a custom system prompt to force *transliteration* of non-English terms (e.g., Telugu song titles) into Latin script. This is critical for compatibility with music search APIs that do not support native scripts well.
3.  **Intent Understanding (LLM)**:
    *   **Engine**: Groq (Llama 3-8b-8192).
    *   **Context**: Controlled by `DialogManager`, which maintains a sliding window of the last ~5 turns to support follow-up queries (e.g., "Play it" implies the song mentioned previously).
    *   **Output**: Structured JSON containing the `action` (PLAY, PAUSE, ETC), `parameters` (song name), and `response_text`.
4.  **Action Execution**:
    *   `MusicActionService` is the central dispatcher.
    *   It determines the **Active Platform** (Spotify vs. SoundCloud) based on user preference or explicit command.
    *   It calls the appropriate **Adapter** (`SpotifyAdapter` or `SoundCloudAdapter`).
5.  **Feedback Loop**:
    *   The system returns the text response (for TTS) and the execution status immediately.

### 2. Intelligent Caching Layer
To bypass the latency of external Music APIs, we use a 3-tier search strategy:
*   **Tier 1 (Redis)**: Hot cache for identical queries made recently.
*   **Tier 2 (PostgreSQL `search_cache`)**: Persistent cache of "normalized" queries.
    *   *Example*: "Play Nuvvu-Nenantu" and "play nuvvu nenantu song" both resolve to the same cached track URI.
*   **Tier 3 (Platform API)**: The fallback. Results are immediately cached to Tier 1 & 2.

---

## 🧩 Key Services

The logic is modularized into `backend/services/`:

| Service | Responsibility |
| :--- | :--- |
| **`dialog_manager.py`** | Manages conversation history and prompt engineering. Decides if a query is a *music command* or just *chat*. |
| **`music_action_service.py`** | The "Router". It receives high-level intents (PLAY, SKIP) and delegates them to the correct platform adapter. |
| **`library_sync_service.py`** | Handles the massive job of fetching, parsing, and storing thousands of songs/playlists from Spotify/SoundCloud into our local DB. |
| **`data_sync_service.py`** | The "Glue" connecting Celery workers to the sync logic. Handles token refreshing and task distribution. |
| **`speech_to_text.py`** | Wrapper for Groq's transcription API. |
| **`text_to_speech.py`** | Wrapper for ElevenLabs (or fallback TTS systems). |

---

## 💾 Database Schema (PostgreSQL)

We use **SQLAlchemy** ORM. Key tables in `backend/models/database_models.py`:

### `users`
The root entity.
*   `id`: UUID
*   `email`: User's identifier.

### `platform_accounts`
Stores the credentials for connected services.
*   `user_id`: FK to User.
*   `platform_name`: "spotify" | "soundcloud".
*   `access_token`, `refresh_token`: Encrypted storage.
*   `meta_data`: JSON column for platform-specific extras (profile pic, user URI).

### `search_cache`
The secret sauce for speed.
*   `query_hash`: SHA256 hash of the normalized query.
*   `platform`: The service the result is for.
*   `result_uri`: The actionable URI (e.g., `spotify:track:123`).
*   `expires_at`: TTL for the cache entry.

---

## 🔌 API Reference

### Core Endpoints (`api/v1/`)

#### Voice & Chat
*   **POST** `/v1/voice/process`: Upload audio file -> Get Action + Audio Response.
*   **POST** `/v1/chat/message`: Send text -> Get Action + Text Response.

#### Platforms (`adapter_routes.py`)
*   **GET** `/v1/adapter/{platform}/login`: Start OAuth flow.
*   **GET** `/v1/adapter/{platform}/callback`: OAuth callback handler.
*   **GET** `/v1/adapter/{platform}/status`: Check connection status.

---

## 🧪 Testing

We use `pytest` for robust testing.

### Running Tests
```bash
# Run all tests
pytest backend/tests

# Run specific integration tests
pytest backend/tests/test_integration.py
```

### Test Scope
*   **Unit Tests**: Validate `DialogManager` state changes and `MusicActionService` routing.
*   **Integration Tests**: Spin up a test DB and verify that API endpoints correctly create/read records.
*   **Mocking**: We use `unittest.mock` to simulate calls to Groq and Spotify APIs, ensuring tests are fast and free.

---

## ⚙️ Background Tasks (Celery)

SAM relies on Celery for tasks that take >200ms.

*   **Metric**: We purposely offload library synchronization to Celery to keep the Voice API response time under strict limits.
*   **Worker**: Runs on `gevent` pool to handle I/O bound tasks (network requests to Spotify).
*   **Beat**: Schedules the `refresh_all_spotify_libraries` task every 6 hours.

**Commands:**
```bash
# Start Worker
celery -A backend.celery_worker worker --loglevel=info --pool=gevent

# Start Scheduler
celery -A backend.celery_worker beat --loglevel=info
```
