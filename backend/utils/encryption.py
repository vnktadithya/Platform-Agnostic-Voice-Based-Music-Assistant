import os
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_fernet() -> Fernet | None:
    """
    Returns a Fernet instance using the ENCRYPTION_KEY from environment variables.
    
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception as e:
        logger.error(f"Invalid ENCRYPTION_KEY: {e}")
        return None

def encrypt_token(token: str) -> str:
    """
    Encrypts a plain text token. 
    Returns the original token if encryption is not configured or fails, 
    logging an error in that case.
    """
    if not token:
        return token
        
    fernet = get_fernet()
    if not fernet:
        logger.critical("ENCRYPTION_KEY not set! Storing token in PLAIN TEXT.")
        return token

    try:
        encrypted = fernet.encrypt(token.encode()).decode()
        return encrypted
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return token

def decrypt_token(token: str) -> str:
    """
    Decrypts an encrypted token.
    Returns the original token if decryption fails (assuming it might be plain text)
    or if encryption is not configured.
    """
    if not token:
        return token
        
    fernet = get_fernet()
    if not fernet:
        # If no key, we assume we can't decrypt, but maybe it's plain text?
        # Use simple heuristic: encrypted tokens usually start with gAAAA
        if token.startswith("gAAAA"):
            logger.critical("ENCRYPTION_KEY missing but token appears encrypted. Cannot decrypt.")
        return token

    try:
        decrypted = fernet.decrypt(token.encode()).decode()
        return decrypted
    except Exception:
        # It's likely not encrypted (legacy plain text)
        return token
