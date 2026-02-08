from backend.adapters.soundcloud_adapter import SoundCloudAdapter
from backend.utils.feature_flags import is_soundcloud_enabled
def get_soundcloud_adapter(access_token: str = None):
    if is_soundcloud_enabled():
        return SoundCloudAdapter(access_token=access_token)
    raise ValueError("SoundCloud is disabled in configuration.")
