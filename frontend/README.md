# Frontend Documentation

The visual soul of **SAM**. Built with **React** and **Three.js** (@react-three/fiber), this frontend delivers a futuristic, cinematic interface that reacts to your voice and music in real time.

---

## 🏗️ Technical Stack

*   **framework**: React 18 + Vite
*   **Language**: TypeScript
*   **3D Engine**: Three.js / @react-three/fiber / Drei
*   **State Management**: Zustand
*   **Styling**: Tailwind CSS + Framer Motion
*   **Protocols**: Socket.IO (Real-time voice/music sync)

---

## 🌌 The Visual Experience (Three.js)

The application is split into two layers: the **3D Canvas** and the **HTML Overlay**.

### 1. Canvas Layer (`components/canvas`)
This is the immersive background.
*   **`CanvasContainer`**: The entry point. Handles pixel ratio, shadows, and the main camera.
*   **`SamCore.tsx`**: The central orb. It uses a custom shader material that pulses based on the `voiceState` (Listening, Thinking, Speaking).
*   **`LivingTether.tsx`**: The complex Bezier curve visualization connecting SAM to the active platform (Spotify/SoundCloud).
    *   **Logic**: It calculates control points dynamically based on the platform's orbit position and adds "energy packet" particles that travel along the curve.
*   **`PlatformOrbit.tsx`**: Renders the orbiting icons. It manages the physics of rotation and the "selection" state when a user clicks a platform.
*   **`HeroParticles.tsx`**: The background starfield. Instanced meshes that react to mouse hover and audio frequency data.

### 2. Overlay Layer (`components/overlay`)
The user interface on top of the canvas.
*   **`ChatOverlay.tsx`**: The main HUD. It manages the microphone button, transcript display, and "Now Playing" widgets.
*   **`InputArea.tsx`**: Text input fallback for voice commands.
*   **`DeviceWarning.tsx`**: A proactive alert system that detects if the user has an active Spotify device.

---

## 🧠 State Management (Zustand)

We use **Zustand** for its performance (subscriptions over context).

### `useMusicStore.ts`
The single source of truth for playback.
*   `isPlaying`: boolean
*   `currentTrack`: { name, artist, albumArt }
*   `volume`: number
*   **Actions**: `play()`, `pause()`, `next()`, `setVolume()`. These actions typically emit Socket.IO events to the backend.

### `useUIStore.ts`
Controls the visual state.
*   `activeView`: "home" | "chat"
*   `theme`: "spotify" (green) | "soundcloud" (orange) | "default" (blue).
*   **Effect**: changing the theme creates a global color shift in the 3D scene (Orb, Tether, Lights).

### `useChatStore.ts`
Manages the conversation.
*   `messages`: Array of { text, sender, timestamp }.
*   `voiceState`: "idle" | "listening" | "processing" | "speaking".

---

## 🔌 Real-Time Communication

The frontend connects to the backend via `ws://localhost:8000`.

**Key Events:**
*   `client-init`: Sent on startup. Handshake.
*   `spotify_status`: Received when track chances. Updates `useMusicStore`.
*   `voice_response`: Binary audio buffer received after a command. Played via Web Audio API.

---

## 🎨 Asset Workflow

### Adding 3D Models
The project uses `.glb` files for platform logos and the central orb.
1.  Place file in `public/models/`.
2.  **Crucial**: Optimize using glTF-Pipeline to reduce size.
    ```bash
    gltf-pipeline -i my-model.glb -o my-model-opt.glb --draco
    ```
3.  Preload in React:
    ```typescript
    useGLTF.preload('/models/my-model-opt.glb')
    ```

---

## 🚀 Running Locally

```bash
# Install dependencies
npm install

# Start Dev Server
npm run dev

# Build for Production
npm run build
```
