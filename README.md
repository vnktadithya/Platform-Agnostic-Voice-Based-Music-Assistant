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

SAM is a voice assistant designed as a dynamic interface for music control. It bridges the gap between static playlists and conversational interaction using advanced LLM integration and real-time 3D visualization.

- **True Intelligence**: Powered by **Groq**, SAM understands context, manages conversations, and executes commands instantly.
- **Visual Feedback**: Voice inputs trigger real-time reactions in a 3D particle system, creating a tangible feedback loop.
- **Extensible Architecture**: Built to control multiple platforms (Spotify, SoundCloud) with a modular adapter pattern.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🗣️ Conversational AI** | Natural language understanding via **Groq (Llama 3)**. Handles context-aware queries and music commands. |
| **🎵 Platform Agnostic** | Seamlessly controls **Spotify** and **SoundCloud**. modular design allows easy integration of new providers. |
| **🌌 Immersive 3D UI** | Built with **React Three Fiber**. A digital orb and particle system that reacts to voice activity and music energy. |
| **⚡ Low Latency** | Optimized architecture using **Redis** and **WebSockets** for instant playback control. |
| **🔄 Smart Sync** | Background **Celery workers** keep libraries, playlists, and liked songs in sync across platforms. |

---

## 🏗️ Architecture

SAM follows a clean architecture designed for scalability and performance.

<div align="center">
  <img src="docs/assets/architecture.png" alt="SAM Architecture Diagram" width="800" />
</div>

**The Flow:**
1.  **User** speaks to the **Frontend (React)**.
2.  **Voice Service** (Groq) transcribes and interprets the intent.
3.  **Backend (FastAPI)** orchestrates the action via **Music Adapters**.
4.  **Celery Workers** handle heavy lifting (syncing libraries) in the background.
5.  **Redis** ensures state is shared instantly across the system.

---

## 🛠️ Technology Stack

### Backend
*   **Framework**: FastAPI (Python)
*   **Database**: PostgreSQL & SQLAlchemy (ORM)
*   **Async Tasks**: Celery with Redis Broker
*   **Real-time**: Socket.IO
*   **AI Engine**: Groq API (Llama 3-8b-8192)
*   **Environment**: Gevent (Windows compatibility for Celery)

### Frontend
*   **Core**: React (Vite) + TypeScript
*   **3D Engine**: Three.js / @react-three/fiber / Drei
*   **State Management**: Zustand
*   **Styling**: Tailwind CSS + Framer Motion

---

## 🚀 Getting Started

Follow these steps to set up a local instance.

### Prerequisites
*   **Python** 3.10+
*   **Node.js** 18+
*   **PostgreSQL** (Local or Cloud)
*   **Redis** (Local or Cloud)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/personal-voice-assistant.git
cd personal-voice-assistant

# Backend Setup
pip install -r requirements.txt

# Frontend Setup
cd frontend
npm install
```

### 2. Configuration (.env)

Create a `.env` file in the root directory.

> [!IMPORTANT]
> The project relies on these keys for functionality.

**Data & Security**
```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/sam_db"
REDIS_HOST="localhost"
REDIS_PORT=6379
SESSION_SECRET_KEY="your-super-secret-key"
```

**AI & Voice**
```env
# Get from https://console.groq.com/keys
GROQ_API_KEY="gsk_..."
```

**Music Platforms**
```env
# Spotify (https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_ID="your_spotify_id"
SPOTIFY_CLIENT_SECRET="your_spotify_secret"
SPOTIFY_REDIRECT_URI="http://localhost:8000/adpter/spotify/callback"

# SoundCloud
ENABLE_SOUNDCLOUD=true
SOUNDCLOUD_CLIENT_ID="your_soundcloud_id"
SOUNDCLOUD_CLIENT_SECRET="your_soundcloud_secret"
SOUNDCLOUD_REDIRECT_URI="http://localhost:8000/v1/adapter/soundcloud/callback"
```

### 3. Running the Project

**1. Start Redis Server**

*   **1.1 Windows (WSL)**: 
    ```bash
    sudo service redis-server start
    ```
    *Note: Redis must be run inside WSL.*

*   **1.2 macOS**:
    ```bash
    brew services start redis
    ```

*   **1.3 Linux**:
    ```bash
    sudo systemctl start redis
    ```

**2. Start Backend (API)**
```bash
# From root directory
uvicorn backend.main:app --reload
```

**3. Start Celery Worker (Background Tasks)**
```bash
# From root directory (Windows)
celery -A backend.celery_worker worker --loglevel=info --pool=gevent
```

**4. Start Celery Beat (Periodic Scheduler)**
```bash
# From root directory
celery -A backend.celery_worker beat --loglevel=info
```

**5. Start Frontend**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173`.

---

## 📚 Documentation Links

*   **[Backend Documentation](backend/README.md)**: Deep dive into API endpoints, database schema, and services.
*   **[Frontend Documentation](frontend/README.md)**: Explore the 3D component structure and visual effects.
*   **[Adding New Platforms](ADDING_NEW_PLATFORMS.md)**: Integrating Apple Music, YouTube, and more.

---
