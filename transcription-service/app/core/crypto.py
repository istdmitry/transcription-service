import os
from cryptography.fernet import Fernet

# The key should be a 32-byte string encoded in base64
# In production, set APP_ENCRYPTION_KEY in environment variables
# For local dev, we generate one if missing
_encryption_key = os.getenv("APP_ENCRYPTION_KEY")

if not _encryption_key:
    print("WARNING: APP_ENCRYPTION_KEY not found. Generating temporary key...")
    # Generate a key and suggest it to the user
    _encryption_key = Fernet.generate_key().decode()
    print(f"TEMP KEY: {_encryption_key}")
    print("Please set this as APP_ENCRYPTION_KEY in your environment!")

cipher_suite = Fernet(_encryption_key.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a base64 encoded token."""
    if not data:
        return None
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    """Decrypts a base64 encoded token back to string."""
    if not token:
        return None
    try:
        return cipher_suite.decrypt(token.encode()).decode()
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None
