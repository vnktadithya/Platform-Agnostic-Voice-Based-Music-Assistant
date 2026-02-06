
import unittest
import os
from unittest.mock import MagicMock, patch
from backend.utils.encryption import encrypt_token, decrypt_token, get_fernet

# Mock environment variable for key
os.environ["ENCRYPTION_KEY"] = "2uaPEDqVoqcR3u37nxEgoDoUx1SD5oznv87XKVQOctE="

class TestEncryption(unittest.TestCase):
    def test_key_validity(self):
        fernet = get_fernet()
        self.assertIsNotNone(fernet, "Fernet instance should be created with valid key")

    def test_encryption_decryption_flow(self):
        original_token = "my_super_secret_token_123"
        encrypted = encrypt_token(original_token)
        
        self.assertNotEqual(original_token, encrypted, "Encrypted token should use Fernet")
        self.assertIn("gAAAA", encrypted, "Fernet tokens typically start with gAAAA")
        
        decrypted = decrypt_token(encrypted)
        self.assertEqual(original_token, decrypted, "Decryption should return original token")

    def test_decrypt_plain_text_fallback(self):
        # Existing tokens in DB are plain text, so decrypt should return them as-is (unless they happen to look like fernet tokens)
        plain = "plain_text_access_token"
        result = decrypt_token(plain)
        self.assertEqual(plain, result, "Should return plain text if decryption fails or not encrypted")

    def test_missing_key_behavior(self):
        # We need to temporarily unset the key
        original_key = os.environ.get("ENCRYPTION_KEY")
        del os.environ["ENCRYPTION_KEY"]
        
        # encrypt should return plain text if no key
        token = "secret"
        self.assertEqual(encrypt_token(token), token)
        
        # Restore key
        if original_key:
            os.environ["ENCRYPTION_KEY"] = original_key

if __name__ == '__main__':
    unittest.main()
