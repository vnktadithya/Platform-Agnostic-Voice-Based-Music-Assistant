import fakeredis
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database_models import Base
from backend.main import app
from backend.configurations.database import get_db
import backend.configurations.database as db_module
from fastapi.testclient import TestClient

# -----------------
# Fake Redis fixture
# -----------------
@pytest.fixture(autouse=True)
def fakeredis_patch(monkeypatch):
    fake_client = fakeredis.FakeStrictRedis()
    monkeypatch.setattr('backend.services.session_manager.redis_client', fake_client)
    yield

# -----------------
# Test DB setup
# -----------------
TEST_DATABASE_URL = "sqlite:///./test.db"

# Allow cross-thread access
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables once for the whole session
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Provide DB session to tests
@pytest.fixture(scope="function")
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override get_db for FastAPI app so routes use test DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client(test_db):
    """
    Test client which overrides the app's DB dependency to use test_db (in-memory).
    Yields an httpx/Starlette TestClient that will call into the FastAPI app
    with the test session.
    """
    # override the dependency used by routes: backend.configurations.database.get_db
    def _get_test_db():
        try:
            yield test_db
        finally:
            # nothing to close here; test_db fixture will clean up
            pass

    app.dependency_overrides[db_module.get_db] = _get_test_db

    with TestClient(app) as c:
        yield c

    # clean up override so other tests are not affected
    app.dependency_overrides.pop(db_module.get_db, None)
