import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database_models import PlatformAccount, SystemUser

client = TestClient(app)

@pytest.fixture
def mock_sync_spotify(monkeypatch):
    """Mock the Celery task so we don't actually try to enqueue background jobs."""
    class MockTask:
        def delay(self, *args, **kwargs):
            return None
    monkeypatch.setattr("backend.api.v1.user_routes.sync_spotify_library", MockTask())

def test_onboard_user_new(test_db, mock_sync_spotify):
    """Test onboarding a completely new user."""
    payload = {
        "platform_name": "spotify",
        "platform_user_id": "new_user_123",
        "refresh_token": "rt_123"
    }
    response = client.post("/v1/users/onboard", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "platform_account_id" in data
    
    # Verify DB
    test_db.expire_all() # Ensure we see committed data
    acc = test_db.query(PlatformAccount).filter_by(platform_user_id="new_user_123").first()
    assert acc is not None, "Failed to find newly created account in DB"
    assert acc.system_user_id is not None

def test_onboard_user_existing(test_db, mock_sync_spotify):
    """Test onboarding a user that already exists (should be idempotent/update)."""
    # 1. Create User
    user = SystemUser()
    test_db.add(user)
    test_db.flush()
    acc = PlatformAccount(
        system_user_id=user.id,
        platform_name="spotify",
        platform_user_id="existing_user",
        refresh_token="old_rt"
    )
    test_db.add(acc)
    test_db.commit()
    
    # 2. Onboard again
    payload = {
        "platform_name": "spotify",
        "platform_user_id": "existing_user",
        "refresh_token": "new_rt" # Duplicate onboarding triggers sync but preserves existing account
    }
    response = client.post("/v1/users/onboard", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "already exists" in data["message"]
