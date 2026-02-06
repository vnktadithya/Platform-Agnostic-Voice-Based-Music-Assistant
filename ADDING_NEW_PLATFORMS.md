# Extending SAM: How to Add a New Music Platform

SAM is designed to be **Platform Agnostic**. Adding support for a new service (e.g., Apple Music, YouTube Music, Tidal) is an easy & structured process involving both Backend logic and Frontend visuals.

---

## 🖥️ Backend Implementation

### 1. Create the Adapter
Create `backend/adapters/new_platform_adapter.py`. It MUST inherit from `AdapterBase` and implement core methods.

```python
from backend.adapters.adapter_base import AdapterBase

class NewPlatformAdapter(AdapterBase):
    def play(self, uris):
        # Call platform API to play
        pass
        
    def search_track_uris(self, query, limit=1):
        # Return list of URIs
        return ["newplatform:track:123"]
    
    @staticmethod
    def get_capabilities():
        return {
            "playback_control": True,
            "search": True
        }

    .....
# Implement all the actions supported by the specific API service
```

### 2. Implement Data Synchronization
Update `backend/services/data_sync_service.py` to handle token refreshes and library fetching.

1.  **Token Management**: Implement `refresh_<newplatform>_access_token(refresh_token)`.
2.  **Valid Token Retrieval**: Implement `get_valid_<newplatform>_access_token(db, account)`.
    *   *Logic*: Check DB expiration -> Return if valid -> Else refresh -> Update DB -> Return.
3.  **Library Sync**: Implement `sync_<newplatform>_library(platform_account_id)`.
    *   Fetch playlists/liked songs and store them using `sync_user_library` (shared utility).

### 3. Register Routes & Auth
Update `backend/api/v1/adapter_routes.py`:
*   **GET** `/v1/adapter/<newplatform>/login`: Redirect user to the platform's OAuth page.
*   **GET** `/v1/adapter/<newplatform>/callback`: Handle the redirect code, exchange for tokens, and create a `PlatformAccount` in the DB.

### 4. Service Registry
1.  **Music Action Service**: Update `backend/services/music_action_service.py` to recognize the new platform string and initialize your adapter.
2.  **Dialog Manager** (Optional): If the platform has unique actions (e.g., "Thumbs Up"), update `_handle_music_action` in `backend/services/dialog_manager.py`.

### 5. Config
Add credentials to `.env`:
```env
NEWPLATFORM_CLIENT_ID="..."
NEWPLATFORM_CLIENT_SECRET="..."
NEWPLATFORM_REDIRECT_URI="..."
```

---

## 🎨 Frontend Implementation

### 1. Add Visual Assets
1.  **Logo**: Add a transparent PNG to `frontend/public/logos/<newplatform>.png`.
2.  **3D Model**: Add a `.glb` model to `frontend/public/models/<newplatform>.glb`.
    *   *Tip*: Use `gltf-pipeline` to optimize it.

### 2. Register Variable Constants
Update `frontend/src/constants/theme.ts`:
```typescript
export const PLATFORM_THEME = {
    // ... existing
    newplatform: { color: '#FF0000', label: 'NEW PLATFORM' }
};
```

### 3. Create the Orbit
Update `frontend/src/components/canvas/PlatformOrbit.tsx`. Add to the `PLATFORMS` array:
```typescript
const PLATFORMS = [
    // ...
    { 
        id: 'newplatform', 
        name: 'New Platform', 
        color: 'platform color', 
        position: [x, y, z], // Choose a unique spot in 3D space
        logo: '/logos/<newplatform>.png' 
    }
];
```
*   **Logic**: Update the `handleSelect` function (line ~365) to allow connection logic for `newplatform`.

### 4. Add Visuals
Update `frontend/src/components/overlay/PlatformVisuals.tsx`.
*   Import your new 3D model component.
*   Add a conditional block:
    ```tsx
    {activePlatform === 'newplatform' && (
        <Canvas> <NewPlatformModel /> </Canvas>
    )}
    ```

### 5. Document Capabilities
Update `frontend/src/components/Features.tsx`. Add a `CapabilityCard` to the list so users know what features are supported (e.g., "Library Sync", "Play by Voice").

---

## ✅ Verification Checklist

1.  **Env**: Credentials added to `.env`.
2.  **Backend**: Restart `uvicorn` and `celery`.
3.  **Frontend**: Restart `npm run dev`.
4.  **Test**:
    *   Say *"Play [Song] on New Platform"*.
    *   Verify the Orbit beam connects.
    *   Verify the music plays on the device.
