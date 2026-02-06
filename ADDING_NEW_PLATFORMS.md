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
You need to register your new platform in two key services to handle credentials and action dispatching.

#### **A. Music Action Service (`backend/services/music_action_service.py`)**

1. Add a helper method to initialize your adapter.
2. Update `perform_music_action` to check capabilities.
3. Implement platform-specific action methods (e.g., `_newplatform_play_song`).

```python
# [Inside MusicActionService class]

    @staticmethod
    def _get_newplatform_adapter(parameters: Dict) -> NewPlatformAdapter:
        token = parameters.get("access_token")
        if not token:
             raise RuntimeError("NewPlatform access_token missing.")
        return NewPlatformAdapter(token)

    # ... existing methods ...

    @staticmethod
    def perform_music_action(action: str, platform: str, parameters: Dict = {}) -> str:
        # ... existing capability check ...

        if required_cap:
             # Add your platform here
             if platform == "spotify":
                 caps = SpotifyAdapter.get_capabilities()
             elif platform == "newplatform":  # <--- ADD THIS
                 caps = NewPlatformAdapter.get_capabilities()
        
        # ... rest of the function ...

    # --- Implement Platform Specific Actions ---
    
    @staticmethod
    def _newplatform_play_song(parameters: Dict):
        """
        Example implementation of a play action for the new platform.
        This roughly matches the pattern used by _spotify_play_song.
        """
        return MusicActionService._get_newplatform_adapter(parameters).play_by_query(
            parameters["db_session"],
            parameters["platform_account_id"],
            parameters.get("song_name", ""),
            resolve_only=parameters.get("resolve_only", False)
        )
```

#### **B. Dialog Manager (`backend/services/dialog_manager.py`)**

Update the logic to retrieve credentials for your new platform.

```python
# [Inside DialogManager class]

    def _get_platform_credentials(self) -> dict:
        # ... existing code ...
        
            if self.platform == "spotify":
                access_token = get_valid_spotify_access_token(self.db, account)
                return {"platform": "spotify", "credentials" : {"access_token": access_token}}
            
            # <--- ADD THIS BLOCK --->
            if self.platform == "newplatform":
                access_token = get_valid_newplatform_access_token(self.db, account)
                return {"platform": "newplatform", "credentials" : {"access_token": access_token}}
            # <---------------------->

            raise ValueError(f"Unsupported platform: {self.platform}")
```

And update the `_handle_music_action` method to initialize the adapter context (like user ID).

```python
# [Inside DialogManager class]

    async def _handle_music_action(self, action: str, parameters: dict):
        # ... credentials resolution ...

        # ---------- Spotify path ----------
        if platform == "spotify":
            # ... existing spotify logic ...

        # <--- ADD THIS BLOCK --->
        elif platform == "newplatform":
             complete_params["access_token"] = access_token
             # If your adapter needs specific user info initialized:
             adapter = NewPlatformAdapter(access_token=access_token)
             user = adapter.get_me() 
             complete_params["user_id"] = user["id"]
        # <---------------------->

        else:
            raise ValueError(f"Unsupported platform: {platform}")
```

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
