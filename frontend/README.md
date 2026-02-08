# Frontend Documentation

The visual interface of **SAM**. Built with **React** and **Three.js** (@react-three/fiber), this frontend delivers a futuristic, cinematic experience that visualizes voice and music interactions in real time.

---

## 🏗️ Tech-Stack

- **Core**: React 18, TypeScript, Vite
- **Routing**: Wouter
- **3D Engine**: Three.js, React Three Fiber, Drei
- **State Management**: Zustand (Persisted)
- **Styling**: Tailwind CSS, Framer Motion
- **Networking**: Axios (REST), Socket.IO (Real-time events)

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
-   **`useAudioController`**: The Audio Engine.
    -   **Ducking/Unducking**: Automatically lowers volume (to 40% on Spotify, 0% on SoundCloud) during voice interaction to prevent STT interference.
    -   **State Management**: Snapshots current volume before speaking and restores it precisely after the interaction ends.
-   **`usePlatformStatus`**: Polls the backend to ensure the selected music platform is active and authenticated.

### Services (`services/`)
-   **`VoiceClient.ts`**: Wrapper around the MediaRecorder API. Handles audio buffering and blob creation.
-   **`api.ts`**: Configured Axios instance with interceptors for error handling and auth redirects.

---

## 🎨 Asset Workflow

**Optimizing 3D Models (.glb)**
All 3D assets in `public/models/` must be optimized and converted to React components to ensure performance.
1.  **Compress**: Use `gltf-pipeline` with Draco compression.
    ```bash
    npx gltf-pipeline -i model.glb -o model-opt.glb --draco
    ```
-   **Output**: Creates model-opt.glb in the current folder.
-   **Action**: Ensure this binary file stays in public/models/.

2. **Generate Component**: Create the React Three Fiber component.
    ```bash
    npx gltfjsx model-opt.glb --types
    ```
3.  **Preload**: The generated file will include useGLTF.preload, but ensure the path matches your public directory structure (e.g., /models/model-opt.glb).

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
