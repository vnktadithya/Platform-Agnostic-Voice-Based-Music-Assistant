import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.custom_exceptions import AuthenticationError, DeviceNotFoundException, ExternalAPIError

client = TestClient(app)

@pytest.fixture
def mock_routes(monkeypatch):
    """Inject a dummy router to test global exception handlers without relying on real logic."""
    from fastapi import APIRouter
    router = APIRouter()
    
    @router.get("/force_auth_error")
    def force_auth_error():
        raise AuthenticationError("Forced Auth Error")

    @router.get("/force_device_error")
    def force_device_error():
        raise DeviceNotFoundException("Forced Device Error")

    @router.get("/force_api_error")
    def force_api_error():
        raise ExternalAPIError("Forced API Error")
        
    app.include_router(router)
    return router

def test_authentication_error_handler(mock_routes):
    response = client.get("/force_auth_error")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_ERROR"

def test_device_not_found_handler(mock_routes):
    response = client.get("/force_device_error")
    assert response.status_code == 409
    assert response.json()["code"] == "DEVICE_NOT_FOUND"

def test_external_api_error_handler(mock_routes):
    response = client.get("/force_api_error")
    assert response.status_code == 502
    assert response.json()["code"] == "EXTERNAL_API_ERROR"
