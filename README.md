<div align="center">
  <img src="docs/assets/logo.png" alt="SAM Logo" width="200" height="200" />
  
  # SAM: Self Adaptive Music Intelligence
  ### The 8-Month Journey to the Ultimate Voice Assistant
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
  [![Three.js](https://img.shields.io/badge/Three.js-Black?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Groq](https://img.shields.io/badge/AI-Groq%20Llama3-orange?style=for-the-badge)](https://groq.com/)
  [![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

  <p align="center">
    <b>A Platform-Agnostic, Voice-Controlled, 3D Music Assistant tailored for the future.</b><br />
    Experience music like never before with immersive visuals and low-latency intelligence.
  </p>
</div>

---

## 🚀 Why SAM?

SAM isn't just a voice assistant; it's a **living, breathing interface** for your music. Born from an intensive 8-month development journey, SAM bridges the gap between static playlists and dynamic, conversational interaction.

- **Worth the Wait**: Every line of code, from the 3D particle systems to the backend orchestration, has been crafted to deliver a premium experience.
- **True Intelligence**: Powered by **Groq**, SAM understands context, manages conversations, and executes complex commands instantly.
- **Visual Symphony**: Your voice doesn't just trigger an action; it ripples through a 3D digital world, creating a feedback loop that feels tangible.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🗣️ Conversational AI** | Natural language understanding via **Groq (Llama 3)**. SAM speaks back, understands context, and even handles non-music queries. |
| **🎵 Platform Agnostic** | Seamlessly controls **Spotify** and **SoundCloud**. Designed to be easily extensible to Apple Music, YouTube Music, and more. |
| **🌌 Immersive 3D UI** | Built with **React Three Fiber**. A stunning digital orb and particle system that reacts to your voice and music energy. |
| **⚡ Low Latency** | Optimized architecture using **Redis** and **WebSockets** for real-time feedback and instant playback control. |
| **🔄 Smart Sync** | Background **Celery workers** keep your libraries, playlists, and liked songs in sync across all platforms. |

---

## 🏗️ Architecture

SAM follows a robust, industry-grade architecture designed for scalability and performance.

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

Follow these steps to set up your own personal SAM instance.

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

Create a `.env` file in the root directory. You will need credentials from various platforms.

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

**1. Start Redis Server** (Ensure it's running in the background)
```bash
redis-server
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

Visit `http://localhost:5173` and start talking to SAM!

---

## 📚 Documentation Links

*   **[Backend Documentation](backend/README.md)**: Deep dive into API endpoints, database schema, and services.
*   **[Frontend Documentation](frontend/README.md)**: Explore the 3D component structure and visual effects.
*   **[Adding New Platforms](ADDING_NEW_PLATFORMS.md)**: Integrating Apple Music, YouTube, and more.

---

<p align="center">
  Made with ❤️ by [Your Name]
</p>
