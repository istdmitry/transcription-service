import os
import sys

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.crypto import encrypt_data, decrypt_data

def test_crypto():
    original = '{"key": "secret_value"}'
    print(f"Original: {original}")
    
    encrypted = encrypt_data(original)
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert original == decrypted
    print("✅ Crypto verification successful!")

if __name__ == "__main__":
    test_crypto()
