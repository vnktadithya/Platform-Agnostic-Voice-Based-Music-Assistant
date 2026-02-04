import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database_models import PlatformAccount

client = TestClient(app)

@pytest.fixture
def mock_spotify_adapter(monkeypatch):
    class MockAdapter:
        @staticmethod
        def get_auth_manager():
            return None

        @staticmethod
        def handle_auth_callback(code):
            return {
                "user": {"id": "sp_user", "email": "sp@test.com", "name": "Sp User"},
                "tokens": {
                    "refresh_token": "rt_valid",
                    "access_token": "at_valid",
                    "expires_at": 3600,
                    "scope": "read",
                    "token_type": "Bearer"
                }
            }
    monkeypatch.setattr("backend.api.v1.adapter_routes.SpotifyAdapter", MockAdapter)

@pytest.fixture
def mock_sync_task(monkeypatch):
    class MockTask:
        def delay(self, *args, **kwargs):
            return None
    monkeypatch.setattr("backend.api.v1.adapter_routes.sync_spotify_library", MockTask())
    monkeypatch.setattr("backend.api.v1.adapter_routes.sync_soundcloud_library", MockTask())

def test_spotify_callback_new_user(client, test_db, mock_spotify_adapter, mock_sync_task):
    """Test Spotify callback for a new user flow."""
    response = client.get("/v1/adapter/spotify/callback", params={"code": "auth_code_123"})
    
    # Should redirect
    # Disable redirect following to verify the Location header
    response = client.get("/v1/adapter/spotify/callback", params={"code": "auth_code_123"}, follow_redirects=False)
    assert response.status_code == 307
    assert "http://localhost:5173/chat" in response.headers["location"]
    
    # Verify DB
    acc = test_db.query(PlatformAccount).filter_by(platform_user_id="sp_user").first()
    assert acc is not None
    assert acc.owner.email == "sp@test.com"

def test_soundcloud_login_redirect(client, monkeypatch):
    monkeypatch.setattr("backend.api.v1.adapter_routes.is_soundcloud_enabled", lambda: True)
    monkeypatch.setattr("backend.adapters.soundcloud_adapter.SoundCloudAdapter.get_auth_url", lambda: ("http://sc.com/login", "verifier123"))
    
    response = client.get("/v1/adapter/soundcloud/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "http://sc.com/login"
    assert "soundcloud_verifier" in response.cookies
