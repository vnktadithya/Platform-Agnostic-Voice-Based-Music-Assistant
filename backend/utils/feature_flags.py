import os

def is_soundcloud_enabled() -> bool:
    return os.getenv("ENABLE_SOUNDCLOUD", "false").lower() == "true"
