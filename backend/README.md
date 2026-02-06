# Backend Documentation

The **SAM Backend** is a high-performance, asynchronous FastAPI application that serves as the brain of the voice assistant. It orchestrates the complex interplay between Speech-to-Text (STT), Large Language Models (LLM), and third-party music APIs.

---

## 🛠️ Technical Stack

**Core Framework**: Python 3.10+, FastAPI, Pydantic
**Database**: PostgreSQL, SQLAlchemy (ORM), Redis
**Real-time & Async**: Python-SocketIO, Uvicorn (ASGI)
**Task Queue**: Celery (Gevent), Redis Broker
**AI & Processing**: Groq Cloud (Llama 3, Whisper, TTS), TheFuzz
**Testing**: Pytest

---

## 🏗️ Architecture & Core Loop

The backend prioritizes **latency** and **accuracy**. The core processing loop is orchestrated primarily through `chat_routes.py` (which handles both voice and text inputs via `DialogManager`):

### 1. The Voice/Chat Pipeline
1.  **Ingestion & Transliteration**:
    *   **Endpoint**: `/v1/chat/process_voice` or `/v1/chat/process_text`.
    *   **STT Engine**: Groq (Whisper-large-v3) converts audio to text.
    *   **Innovation**: We use a custom system prompt to force *transliteration* of non-English terms (e.g., Telugu song titles) into Latin script. This is critical for compatibility with music search APIs.
2.  **Intent Understanding (LLM)**:
    *   **Engine**: Groq (Llama 3-8b-8192).
    *   **Service**: `LLM_service.py` wraps the LLM calls.
    *   **Context**: Controlled by `DialogManager`, which maintains a session history (via `SessionManager` + Redis) to support follow-up queries (e.g., "Play it" implies the song mentioned previously).
    *   **Output**: Structured JSON containing the `action` (PLAY, PAUSE, ADD_TO_PLAYLIST, LIKE_SONG ETC), `parameters` (song_name, artist_name, playlist_name etc), and `reply` (text response).
3.  **Action Execution**:
    *   **Service**: `MusicActionService` is the central dispatcher.
    *   It determines the **Active Platform** (Spotify vs. SoundCloud) based on user preference or explicit command.
    *   It calls the appropriate **Adapter** (`SpotifyAdapter` or `SoundCloudAdapter`).
4.  **Feedback Loop**:
    *   The system returns the response immediately, often including the TTS audio (or audio path) and the execution status in a single JSON payload.

### 2. Intelligent Caching Layer
To bypass the latency of external Music APIs, We use a 3-tier search strategy:
*   **Tier 1 (Redis)**: Hot cache for identical queries made recently.
*   **Tier 2 (PostgreSQL `search_cache`)**: Persistent cache of "normalized" queries.
    *   *Example*: "Play ShaPE _oF-You" and "play shape of you song" both resolve to **shape of you**-the same cached track URI.
*   **Tier 3 (Platform API)**: The fallback. Results are immediately cached to Tier 1 & 2.

---

## 🧩 Key Services

The logic is modularized into `backend/services/`:

| Service | Responsibility |
| :--- | :--- |
| **`dialog_manager.py`** | Manages conversation flow. It orchestrates the LLM call, action parsing, and response generation. |
| **`LLM_service.py`** | Wraps interactions with the Groq API (Llama 3), handling prompt construction and JSON parsing. |
| **`music_action_service.py`** | The "Router". It receives high-level intents (PLAY, SKIP) and delegates them to the correct platform adapter. |
| **`session_manager.py`** | Manages user session state and context history in Redis, enabling multi-turn conversations. |
| **`socket_manager.py`** | Handles real-time WebSockets to push state updates (LISTENING, THINKING, SPEAKING) to the frontend. |
| **`library_sync_service.py`** | Handles the massive job of fetching, parsing, and storing thousands of songs/playlists from Spotify/SoundCloud into our local DB. |
| **`data_sync_service.py`** | The "Glue" connecting Celery workers to the sync logic. Handles token refreshing and task distribution. |
| **`speech_to_text.py`** | Wrapper for Groq's transcription API. |
| **`text_to_speech.py`** | Wrapper for Groq's TTS API service. |
| **`cache_service.py`** | Abstracted interface for Redis operations. |

---

## 💾 Database Schema (PostgreSQL)

We use **SQLAlchemy** ORM. Key tables in `backend/models/database_models.py`:

### `users` (`system_users`)
The root entity.
*   `id`: Int (Primary Key)
*   `email`: User's identifier.
*   `created_at`: Timestamp of the account creation.

### `platform_accounts`
Stores the credentials for connected services.
*   `id`: Primary key.
*   `system_user_id`: Foreign Key to **system_users**.
*   `platform_name`: "spotify" | "soundcloud".
*   `access_token`, `refresh_token`: Encrypted storage.
*   `meta_data`: JSON column for platform-specific extras (profile pic, user URI).
*   `last_synced`: Timestamp of the last full library sync.

### `user_playlists` & `user_liked_songs`
Mirror the user's remote library.
*   `id`: Primary key.
*   `platform_account_id`: Foreign Key to Platform Account.
*   `track_uri` / `playlist_id`: Unique identifiers.
*   `meta_data`: JSON storing names, artists, album art, etc.
*   `last_synced`: Timestamp of the last library sync.

### `search_cache`
The secret sauce for speed.
*   `id`: Primary key
*   `platform_account_id`: Foreign Key to Platform Account.
*   `normalized_query`: The standardized version of the user's search text.
*   `track_uri`: The resolved actionable URI (e.g., `spotify:track:123`).
*   `meta_data`: Additional info like song title/artist for verification.
*   `timestamp`: Timestamp of the last library sync.

### `interaction_logs`
*   `id`: Primary key
*   `platform_account_id`: Foreign Key to Platform Account.
*   `session_id`: Session id provided by browser.
*   `user_input`: The text of what the user said.
*   `llm_response`: The full JSON response from the LLM.
*   `final_action`: The executed action (e.g., `play_song`), for analytics.
*   `timestamp`: Timestamp of the last interaction.

---

## 🔌 API Reference

### Core Endpoints (`api/v1/`)

#### Chat & Voice (`chat_routes.py` & `voice_routes.py`)
*   **POST** `/v1/chat/process_text`: Main text chat loop. Input: `{text, platform}`. Output: `{reply, action_result}`.
*   **POST** `/v1/chat/process_voice`: Main voice loop. Input: `audio file`, `platform`. Output: `{transcribed_text, reply, action_result}`.
*   **POST** `/v1/voice/stt`: Standalone Speech-to-Text utility.
*   **POST** `/v1/voice/tts`: Standalone Text-to-Speech utility.

#### Search (`search_routes.py`)
*   **GET** `/v1/search`: Queries the Cache first, then the Platform API.

#### Users (`user_routes.py`)
*   **POST** `/v1/users/onboard`: Register a new platform account and trigger initial library sync.

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
*   **Worker**: Runs on `gevent` pool to handle I/O bound tasks.
*   **Beat**: Schedules the `refresh_all_spotify_libraries` and `refresh_all_soundcloud_libraries` task every 6 hours. This helps us to get the data from the respective platform if user performs any action internally.
