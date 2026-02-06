<div align="center">
  <img src="docs/assets/logo.png" alt="SAM Logo" width="200" height="200" />
  
  # SAM: Self Adaptive Music Intelligence
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
  [![Three.js](https://img.shields.io/badge/Three.js-Black?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Groq](https://img.shields.io/badge/AI-Groq%20Llama3-orange?style=for-the-badge)](https://groq.com/)
  [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

  <p align="center">
    <b>A Platform-Agnostic, Voice-Controlled, 3D Music Assistant.</b><br />
    Experience music with immersive visuals and low-latency intelligence.
  </p>
</div>

---

## 🚀 Overview

**SAM** (Self Adaptive Music) is a next-generation voice assistant designed to revolutionize how you interact with music. Breaking away from static playlists, SAM uses advanced **LLMs (Groq Llama 3)** to understand natural language and intent, executing complex commands across multiple platforms like **Spotify** and **SoundCloud**.

All of this happens within a stunning **3D immersive interface** built with React Three Fiber, where the environment reacts to the music and your voice in real-time.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🗣️ Conversational AI** | Powered by **Groq (Llama 3)** for near-instant natural language understanding. Context-aware interactions allow for follow-up requests. |
| **🎵 Platform Agnostic** | Seamlessly controls **Spotify** and **SoundCloud** from a single interface. Extensible design allows easy addition of new music providers. |
| **🌌 Immersive 3D UI** | A cinematic experience built with **Three.js**. The "Living Tether" connecting SAM to platforms physically reacts to data flow and music energy. |
| **⚡ Low Latency** | Optimized architecture using **Redis** for caching and **WebSockets** for real-time state synchronization (< 500ms response time). |
| **🔄 Smart Sync** | Background **Celery workers** keep your playlists, liked songs, and libraries in sync across all connected platforms. |
| **🧠 Adaptive Intelligence** | Logs user interactions and feedback to build a dataset for future fine-tuning, allowing the model to learn your preferences over time. |

---

## 🏗️ Architecture

SAM follows a clean, modular architecture designed for performance and scalability.

<div align="center">
  <img src="docs/assets/architecture.png" alt="SAM Architecture Diagram" width="800" />
</div>

### System Workflow

The following diagram details the end-to-end data flow, from user input to music execution.

<div align="center">
  <img src="docs/assets/process_workflow.png" alt="SAM Workflow Diagram" width="800" />
</div>

### Project Structure

```bash
personal-voice-assistant/
├── backend/                 # FastAPI Application
│   ├── adapters/            # Platform-specific logic (Spotify, SoundCloud)
│   ├── api/                 
│   │   ├── v1/              # REST endpoints
│   ├── configurations/      # Postgres and Redis Configuration
│   ├── services/            # Core business logic (LLM, Sync, Search)
│   ├── models/              # Database schemas (SQLAlchemy)
│   ├── tests/               # Unit and Integration tests
│   ├── utils/               # Helper functions
│   ├── celery_worker.py     # Background Tasks scheduler
│   ├── main.py              # Entry point to fastAPI application
│   ├── socket_manager.py    # Web Secket
│   ├── README.md            # Backend Architecture
│
├── frontend/                # React + Vite Application
│   ├── public/              # Platform Logos and 3d models
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── canvas/      # 3D R3F scenes (Orbits, Particles)
│   │   │   └── overlay/     # HTML UI layers (Chat, HUD)
│   │   ├── pages/           # Web Pages
│   │   ├── services/        # API and Voice clients
│   │   ├── hooks/           # Custom React hooks (Audio, Chat, Platform logic)
│   │   ├── constants/       # paltform themes
│   │   └── store/           # Zustand state management
│   │   ├── types/           # Shared TypeScript interfaces and type definitions
│   │   ├── utils/           # helper functions
│   │   ├── App.tsx          # root component
│   │   ├── main.tsx         # Entry point for application
│   │   ├── index.css        # global styles
│   ├── index.html           # Main entry point
│   ├── README.md            # Frontend Architecture
├── docs/                    # Documentation assets
└── README.md                # You are here
```

---

## ⚠️ Service Requirements

Before setting up SAM, ensure you meet the requirements for the music platforms you intend to use.

> [!IMPORTANT]
> **Spotify Integration Requirements:**
> 1.  **Premium Subscription**: Spotify's API restricts playback control to Premium users only.
> 2.  **Developer Dashboard**: Since this app is in "Development Mode", you **MUST** manually add your email address to the allowed users list in your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

> [!NOTE]
> **SoundCloud Integration Requirements:**
> *   **Active Account**: A free SoundCloud account is sufficient. No premium subscription is needed.

---

## 🛠️ Getting Started

Follow these steps to set up a local instance of SAM.

### Prerequisites

*   **Python** 3.10+
*   **Node.js** 18+
*   **Redis** (Must be running locally or via Docker)
*   **PostgreSQL** (Local or Cloud instance)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/personal-voice-assistant.git
cd personal-voice-assistant

# Setup Backend Virtual Environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Backend Dependencies
pip install -r requirements.txt

# Setup Frontend
cd frontend
npm install
```

### 2. Configuration (`.env`)

Create a `.env` file in the root directory. This is critical for the application to function.

```env
# --- Data & Security ---
DATABASE_URL="postgresql://postgres:password@localhost:5432/sam_db"
REDIS_HOST="localhost"
REDIS_PORT=6379
SESSION_SECRET_KEY="your-session-secret-key"

# --- AI & Voice ---
# Logic, TTS & STT: https://console.groq.com/keys
GROQ_API_KEY="gsk_..." 

# --- Spotify ---
# https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID="your_spotify_client_id"
SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
SPOTIFY_REDIRECT_URI="http://localhost:8000/adpter/spotify/callback"

# --- SoundCloud ---
ENABLE_SOUNDCLOUD=true
SOUNDCLOUD_CLIENT_ID="your_soundcloud_client_id"
SOUNDCLOUD_CLIENT_SECRET="your_soundcloudc_client_secret"
SOUNDCLOUD_REDIRECT_URI="http://localhost:8000/v1/adapter/soundcloud/callback"
```

### 3. Running the Application

You will need **5 separate terminal instances** to run the full stack.

### Terminal 1: Redis (Message Broker)
Required for Celery task queue and background job coordination.
```bash
# Windows (run Redis inside WSL) / Linux
sudo service redis-server start

# macOS (using Homebrew)
brew services start redis
```

#### Terminal 2: Backend API
Starts the FastAPI server and WebSocket manager.
```bash
# Make sure venv is active
uvicorn backend.main:app --reload
```

#### Terminal 3: Celery Worker
Handles heavy background tasks like library synchronization.
```bash
# Windows (requires gevent)
celery -A backend.celery_worker worker --loglevel=info --pool=gevent

# Linux / Mac
celery -A backend.celery_worker worker --loglevel=info
```

#### Terminal 4: Celery Beat
Scheduler for periodic tasks (e.g., refreshing tokens every hour).
```bash
celery -A backend.celery_worker beat --loglevel=info
```

#### Terminal 5: Frontend
Launches the 3D interface.
```bash
cd frontend
npm run dev
```

Visit **`http://localhost:5173`** to enter SAM.

---

## 🗣️ Usage

Once inside the application, click on mic button to activate the "Listening" state (or ensure your mic is authorized). Additionally the platform supports text input as well. 

**Try these commands:**
*   *"Play Blinding Lights by The Weeknd"*
*   *"Play some lo-fi beats"*
*   *"Increase volume"*
*   *"Pause"*
*   *"Add this song to my Gym playlist"*

---

## 🤝 Contributing

I welcome contributions! Please check the specific documentation for the component you want to modify:

*   **[Backend Documentation](backend/README.md)**: API reference, Services, and Architecture deep dive.
*   **[Frontend Documentation](frontend/README.md)**: Component structure, 3D Engine, and State Management.
*   **[Adding New Platforms](ADDING_NEW_PLATFORMS.md)**: Step-by-step guide to integrating Apple Music, YouTube, etc.

---

## 📄 License

This project is licensed under the **MIT License**.
