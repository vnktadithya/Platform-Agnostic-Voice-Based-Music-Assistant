# Frontend Documentation

The visual soul of **SAM**. Built with **React** and **Three.js** (@react-three/fiber), this frontend delivers a futuristic, cinematic interface that reacts to your voice and music in real time.

## 🌌 The Visual Experience

SAM is not just buttons and text; it's a 3D environment.

### 1. The Living Tether (`LivingTether.tsx`)
The centerpiece of the UI. It visually connects the **User's Intent** (represented by floating platform icons) to **SAM's Intelligence** (the central orb).
*   **Dynamic Physics**: Uses cubic bezier curves and Perlin noise to create a "breathing" effect.
*   **State Reactive**: The tether tightens when listening, pulses when processing, and relaxes when idle.
*   **Energy Flow**: Simulated light packets travel along the tether, representing data transfer.

### 2. The Orb & Hero Particles (`HeroParticles.tsx`)
*   **The Orb**: A custom 3D shader material that shifts colors based on SAM's mood (listening, speaking, thinking) and the dominant color of the active music platform.
*   **Particles**: Thousands of instanced mesh particles float in the background, providing depth and parallax. They react to mouse movement and audio frequency, making the environment feel alive.

### 3. Platform Orbits (`PlatformOrbit.tsx`)
*   Spotify and SoundCloud are rendered as 3D icons orbiting the central sun (SAM).
*   **Interactive**: You can click an orbit to manually select a platform, triggering a camera transition and tether reconnection.

---

## 🏗️ Architecture & State Management

We use **Zustand** for global state management, chosen for its transient updates (crucial for high-performance 3D loops without re-rendering React components).

### Store Structure (`src/store/`)
*   **`useMusicStore`**: Tracks current song, album art, volume, and playback status. Syncs via WebSockets.
*   **`useChatStore`**: Manages the conversation history and TTS audio queue.
*   **`useUIStore`**: Controls the camera position, active view (Home vs Chat), and visual themes.

### Component Logic (`src/components/`)
*   **`CanvasContainer`**: The WebGL context entry point. Handles `Suspense` for asset loading and Performance monitoring.
*   **`Experience`**: The main scene graph. Contains the lights, camera controls, and 3D objects.
*   **`ChatOverlay`**: The HTML overlay that sits *on top* of the 3D canvas. Handles the Microphone input, Speech recognition feedback, and text transcript display.

---

## 🛠️ Setup & Development

### Prerequisites
*   Node.js 18+
*   NPM

### 1. Installation
```bash
npm install
```

### 2. Development Server
Runs Vite with HMR (Hot Module Replacement).
```bash
npm run dev
```

### 3. Build for Production
Compiles the TypeScript and optimizes 3D assets.
```bash
npm run build
```

---

## 🎨 Styling & Assets

*   **Tailwind CSS**: Used for the HTML UI overlays (Chat box, Login buttons).
*   **Framer Motion**: Handles the smooth enter/exit animations of the UI elements (e.g., the "Listening..." indicator).
*   **GLB Models**: 3D assets (like the specific platform logos) are optimized using `gltf-pipeline` for fast loading.

---

## 🔌 Real-Time Communication

The frontend maintains a persistent **Socket.IO** connection to the backend.
*   **`client-init`**: Handshake to identify the user.
*   **`spotify_status`**: Real-time updates on what song is playing.
*   **`voice_response`**: Receives the audio buffer for SAM's voice.
