# Frontend Documentation

The visual interface of **SAM**. Built with **React** and **Three.js** (@react-three/fiber), this frontend delivers a futuristic, cinematic experience that visualizes voice and music interactions in real time.

---

## 🏗️ Technical Stack

- **Core**: React 18, TypeScript, Vite
- **Routing**: Wouter
- **3D Engine**: Three.js, React Three Fiber, Drei
- **State Management**: Zustand (Persisted)
- **Styling**: Tailwind CSS, Framer Motion
- **Networking**: Axios (REST), Socket.IO (Real-time events)

---

## 📂 Project Structure

```
frontend/src/
├── components/
│   ├── canvas/         # 3D Scene components (Orb, Tether, Particles)
│   ├── overlay/        # 2D HUD elements (Widgets, Alerts, Input)
│   └── ui/             # Reusable UI primitives (Toast, etc.)
├── pages/              # Main application views (Landing, PlatformSelect, Chat)
├── store/              # Global state management
├── services/           # API clients and audio handling
└── hooks/              # Custom React hooks for logic and controllers
```

---

## 🌌 The Visual Experience (Three.js)

The application renders a hybrid interface: a 3D Canvas background with a 2D HTML overlay.

### 1. Canvas Layer (`components/canvas`)
-   **`SamCore.tsx`**: The central interactive orb. Uses custom shaders to pulse and change color based on the `samState` (IDLE, DRAWING, SPEAKING).
-   **`LivingTether.tsx`**: A dynamic Bezier curve system connecting SAM to the active platform orbit. Usage includes "energy packet" visuals for data transmission flow.
-   **`PlatformOrbit.tsx`**: Manages the rotating platform icons (Spotify/SoundCloud) and their selection physics.
-   **`HeroParticles.tsx`**: Interactive background starfield reacting to mouse depth and audio frequency.

### 2. Pages & Layouts (`pages/`)
-   **`LandingPage.tsx`**: Initial entry with "Click to Start" interaction.
-   **`PlatformSelect.tsx`**: The connection hub. Users link their Spotify/SoundCloud accounts here.
-   **`ChatOverlay.tsx`**: The primary dashboard. Contains the microphone control, transcript logs, and the "Now Playing" HUD.

---

## 🧠 State Management

Global state is centralized in **`store/useStore.ts`** using **Zustand**.

### Key Slices
-   **SamState**: Tracks the assistant's mode (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).
-   **Auth**: Persists the `activePlatform` (Spotify/SoundCloud) and `accountId`.
-   **UI**: Manages session-specific flags like `introSeen`.

---

## ⚙️ Core Logic

### Hooks (`hooks/`)
-   **`useChatHandler`**: The central brain. Orchestrates voice recording, API calls, and response handling.
-   **`useAudioController`**: Bridges the gap between Three.js visuals and audio data (frequency analysis).
-   **`usePlatformStatus`**: Polls the backend to ensure the selected music platform is active and authenticated.

### Services (`services/`)
-   **`VoiceClient.ts`**: Wrapper around the MediaRecorder API. Handles audio buffering and blob creation.
-   **`api.ts`**: Configured Axios instance with interceptors for error handling and auth redirects.

---

## 🎨 Asset Workflow

**Optimizing 3D Models (.glb)**
All 3D assets in `public/models/` must be optimized to ensure performance.
1.  **Compress**: Use `gltf-pipeline` with Draco compression.
    ```bash
    gltf-pipeline -i model.glb -o model-opt.glb --draco
    ```
2.  **Preload**: Use the `useGLTF.preload` method in React to prevent pop-in.

---

## 🚀 Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```
