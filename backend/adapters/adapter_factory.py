from backend.adapters.soundcloud_adapter import SoundCloudAdapter
def get_soundcloud_adapter(access_token: str = None):
    if is_soundcloud_enabled():
        return SoundCloudAdapter(access_token=access_token)
    raise ValueError("SoundCloud is disabled in configuration.")
