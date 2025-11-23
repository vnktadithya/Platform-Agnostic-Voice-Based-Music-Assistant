# yt_oauth_setup.py

from ytmusicapi import YTMusic, setup_oauth
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Replace these with your Google Cloud OAuth credentials
CLIENT_ID = os.getenv("GOOGLE_CLOUD_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLOUD_CLIENT_SECRET")

# 2. Path where the OAuth tokens will be stored
OAUTH_FILEPATH = "yt_oauth.json"

# 3. Generate the OAuth file (one-time)
#    This will prompt you to visit a URL, authorize the app, and paste back the code.
setup_oauth(
    filepath=OAUTH_FILEPATH,
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

print(f"OAuth setup complete. Credentials saved to {OAUTH_FILEPATH}")

# 4. Verify the setup by initiating the client
yt = YTMusic(OAUTH_FILEPATH)
playlists = yt.get_library_playlists(limit=1)
print("Successfully fetched your first library playlist:", playlists)