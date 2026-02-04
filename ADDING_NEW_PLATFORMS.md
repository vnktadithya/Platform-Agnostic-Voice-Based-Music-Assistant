# Extending SAM: How to Add a New Platform

One of SAM's core philosophies is being **Platform Agnostic**. We designed the architecture so that adding support for **Apple Music**, **YouTube Music**, or **Tidal** is a structured, predictable process.

Follow this guide to integrate a new platform.

---

## 🖥️ Backend Implementation

### 1. Create the Adapter
Go to `backend/adapters/` and create `new_platform_adapter.py`.
It must inherit from `AdapterBase` and implement the abstract methods.

```python
from backend.adapters.adapter_base import AdapterBase

class NewPlatformAdapter(AdapterBase):
    def play(self, ...):
        # Implementation using platform's API
        pass
        
    def search(self, query, ...):
        # Implementation
        pass
    
    @staticmethod
    def get_capabilities():
        return {
            "playback_control": True,
            "playlist_creation": False # If not supported
        }
```

### 2. Register the Service
Open `backend/services/music_action_service.py`.
1.  Add a Dispatcher method: `_newplatform_play_song`.
2.  Update the `perform_music_action` logic to recognize the new platform string.

```python
@staticmethod
def _newplatform_play_song(parameters: Dict):
    return MusicActionService._get_newplatform_adapter(parameters).play(...)
```

### 3. Update Database Models (Optional)
If the new platform requires specific metadata fields that don't fit into the generic `meta_data` JSON column in `PlatformAccount`, update `backend/models/database_models.py`.

### 4. Configuration
Add the necessary credentials to `.env`:
```env
NEWPLATFORM_CLIENT_ID="class"
NEWPLATFORM_SECRET="secret"
```

---

## 🎨 Frontend Implementation

### 1. Add Visual Assets
1.  Add the high-quality 3D logo (`.glb` or `.gltf`) to `frontend/public/models/`.
2.  Add a texture/image to `frontend/public/textures/` for UI icons.

### 2. Register the Orbit
Open `frontend/src/components/canvas/PlatformOrbit.tsx`.
Add your new platform to the `PLATFORMS` array. This automatically generates the 3D orbit and interactable icon.

```typescript
const PLATFORMS = [
  { name: 'spotify', ... },
  { name: 'soundcloud', ... },
  { name: 'newplatform', color: '#FF0000', icon: '...' } // Add this
];
```

---

## ✅ Verification

1.  Restart the Backend (to load new Env vars and code).
2.  Restart the Frontend.
3.  Say: *"Play [Song] on NewPlatform"*.
4.  **Success**: SAM understands the intent, routes it to your new adapter, and music plays.

---

**You're done!** You've just expanded SAM's universe. 🚀
