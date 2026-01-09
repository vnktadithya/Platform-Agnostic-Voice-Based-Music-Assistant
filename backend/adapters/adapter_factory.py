from backend.adapters.soundcloud_adapter import SoundCloudAdapter
from backend.adapters.mock_soundcloud_adapter import MockSoundCloudAdapter
from backend.utils.feature_flags import is_soundcloud_enabled

"""Adapter selection factory for SoundCloud

 DESIGN NOTE:
 ------------
 This function is the SINGLE place where runtime decisions are made
 about whether to use the real SoundCloud adapter or the mock adapter.

 - Core services and sync logic must NEVER contain platform conditionals
 - Enabling real SoundCloud support should only require:
     1. Setting ENABLE_SOUNDCLOUD=true
     2. Providing valid OAuth credentials

 No other part of the system should be modified."""

def get_soundcloud_adapter(access_token: str = None):
    if is_soundcloud_enabled():
        return SoundCloudAdapter(access_token=access_token)
    return MockSoundCloudAdapter()
