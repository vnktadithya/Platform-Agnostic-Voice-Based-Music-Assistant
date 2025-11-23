import webbrowser
import requests
import json

# Replace these with your Web application credentials
CLIENT_ID = "374554694813-gt2ei08tktfovraeo9eqsq1tcmlsmrh2.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:8000/adapter/youtube_music/callback"

# Step 1: Generate authorization URL
auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    "?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    "&scope=https://www.googleapis.com/auth/youtube"
    "&access_type=offline"
    "&prompt=consent"
)
print("Open this URL in your browser and authorize:")
print(auth_url)
webbrowser.open(auth_url)

# Step 2: After login, Google will redirect to REDIRECT_URI?code=XYZ
code = input("Paste the `code` query parameter from the redirect URL here: ").strip()

# Step 3: Exchange code for tokens
token_response = requests.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
)
tokens = token_response.json()
if "error" in tokens:
    print("Token exchange failed:", tokens)
    exit(1)

# Step 4: Save tokens in ytmusicapi format
yt_oauth = {
    "access_token": tokens["access_token"],
    "refresh_token": tokens["refresh_token"],
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "token_uri": "https://oauth2.googleapis.com/token",
}
with open("yt_oauth.json", "w") as f:
    json.dump(yt_oauth, f, indent=2)
print("✅ Tokens saved to yt_oauth.json")

oauth_credentials = {
  "installed" : {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
  }
}
with open("oauth_credentials.json", "w") as f:
    json.dump(oauth_credentials, f, indent=2)
print("✅ Tokens saved to oauth_credentials.json")

# Step 5: Verify with ytmusicapi
from ytmusicapi import YTMusic
yt = YTMusic("yt_oauth.json", oauth_credentials="oauth_credentials.json")
print("First library playlist:", yt.get_library_playlists(limit=1))
