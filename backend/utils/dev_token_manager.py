import os
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = 'AQDDszKQ9kAXFrijgI8LGeMYxBA8e9QvwRWeGP5t-RvhkCvWJvGoLtraSeZ7FVvnO-a23OPjTy8zhx0mdmZO8co1ht5JMIv_B_rtC5untxyekEExkdAw3c3f-UIwYpT0VQc'

class DevSpotifyTokenManager:
    _cached_access_token = None

    @staticmethod
    def get_access_token():
        """
        Gets a fresh access token using the refresh token for dev use.
        """
        if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN]):
            raise Exception("Spotify client credentials or refresh token missing in .env")

        token_url = "https://accounts.spotify.com/api/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": SPOTIFY_REFRESH_TOKEN,
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(token_url, data=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.text}")

        access_token = response.json().get("access_token")
        if not access_token:
            raise Exception("No access token returned from Spotify")

        print(access_token)
        return access_token
