
import unittest
import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.configurations.database import Base
from backend.models.database_models import PlatformAccount, SystemUser
from backend.utils.encryption import encrypt_token, decrypt_token, get_fernet

# --- Setup In-Memory DB ---
# Use an in-memory SQLite database for testing to avoid touching production data
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestEncryptionIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # 1. Set a fixed encryption key for the test context
        cls.fixed_key = "2uaPEDqVoqcR3u37nxEgoDoUx1SD5oznv87XKVQOctE="
        os.environ["ENCRYPTION_KEY"] = cls.fixed_key
        
        # 2. Setup DB connection
        cls.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # 3. Create Tables
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Clear tables before each test
        self.db.query(PlatformAccount).delete()
        self.db.query(SystemUser).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_storage_encryption(self):
        """
        Scenario: Simulate 'adapter_routes.py' saving a new account.
        Verify that the data actually lands in the DB in encrypted form.
        """
        # Raw secrets
        raw_refresh = "refresh_secret_123"
        raw_access = "access_secret_456"
        
        # Encrypt (simulating what happens in the router)
        encrypted_refresh = encrypt_token(raw_refresh)
        encrypted_access = encrypt_token(raw_access)
        
        # Create User & Account
        user = SystemUser(email="test@example.com")
        self.db.add(user)
        self.db.commit()
        
        account = PlatformAccount(
            system_user_id=user.id,
            platform_name="spotify",
            platform_user_id="spotify_user_1",
            refresh_token=encrypted_refresh, # Storing ENCRYPTED
            meta_data={
                "access_token": encrypted_access, # Storing ENCRYPTED
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            }
        )
        self.db.add(account)
        self.db.commit()
        
        # --- VERIFICATION ---
        # Query the DB raw object
        stored_account = self.db.query(PlatformAccount).filter_by(platform_user_id="spotify_user_1").first()
        
        # 1. Check Refresh Token in DB is encrypted
        self.assertNotEqual(stored_account.refresh_token, raw_refresh, "Stored refresh token must NOT be plain text")
        self.assertTrue(stored_account.refresh_token.startswith("gAAAA"), "Stored refresh token should look like Fernet (start with gAAAA)")
        
        # 2. Check Access Token in JSON metadata is encrypted
        stored_meta = stored_account.meta_data
        self.assertNotEqual(stored_meta["access_token"], raw_access, "Stored access token must NOT be plain text")
        self.assertTrue(stored_meta["access_token"].startswith("gAAAA"), "Stored access token should look like Fernet")

    def test_retrieval_decryption(self):
        """
        Scenario: Simulate 'data_sync_service.py' retrieving and using the token.
        Verify we can get the original secrets back.
        """
        raw_refresh = "my_refresh_token"
        raw_access = "my_access_token"
        
        # Pre-seed DB with encrypted data
        user = SystemUser(email="read_test@example.com")
        self.db.add(user)
        self.db.commit()
        
        account = PlatformAccount(
            system_user_id=user.id,
            platform_name="spotify",
            platform_user_id="spotify_user_read",
            refresh_token=encrypt_token(raw_refresh),
            meta_data={
                "access_token": encrypt_token(raw_access),
                "expires_at": "2025-01-01T00:00:00+00:00"
            }
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        
        # --- SIMULATE USAGE ---
        # Logic mirroring `get_valid_spotify_access_token` reading part
        
        # 1. Access Token Retrieval
        stored_meta = account.meta_data
        decrypted_access = decrypt_token(stored_meta["access_token"])
        self.assertEqual(decrypted_access, raw_access, "Decrypted access token should match original")
        
        # 2. Refresh Token Retrieval (for rotation flows)
        decrypted_refresh = decrypt_token(account.refresh_token)
        self.assertEqual(decrypted_refresh, raw_refresh, "Decrypted refresh token should match original")

    def test_mixed_legacy_data(self):
        """
        Scenario: Verify backward compatibility logic.
        If DB has plain text (legacy), decrypt_token should return it as-is without crashing.
        """
        legacy_refresh = "legacy_refresh_token"
        legacy_access = "legacy_access_token"
        
        user = SystemUser(email="legacy@example.com")
        self.db.add(user)
        self.db.commit()
        
        account = PlatformAccount(
            system_user_id=user.id,
            platform_name="spotify",
            platform_user_id="legacy_user",
            refresh_token=legacy_refresh, # Stored PLAIN
            meta_data={
                "access_token": legacy_access # Stored PLAIN
            }
        )
        self.db.add(account)
        self.db.commit()
        
        # Retrieve
        retrieved = self.db.query(PlatformAccount).filter_by(platform_user_id="legacy_user").first()
        
        # Decrypt should return original plain text if it fails to look like a fernet token or fails decryption
        result_refresh = decrypt_token(retrieved.refresh_token)
        result_access = decrypt_token(retrieved.meta_data["access_token"])
        
        self.assertEqual(result_refresh, legacy_refresh)
        self.assertEqual(result_access, legacy_access)

if __name__ == '__main__':
    unittest.main()
