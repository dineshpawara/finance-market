"""
Cryptographic Encryption & Key Derivation Utilities
===================================================
Provides symmetric encryption (Fernet) for protecting sensitive at-rest secrets,
such as TOTP base32 seeds and two-factor credentials in PostgreSQL.
Derives keys deterministically from the application SECRET_KEY via HKDF-SHA256.
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from core.security import _get_secret_key

# Deterministic HKDF Salt and Context Info for 2FA Seed Encryption
TOTP_KDF_SALT: bytes = b"finance_market_totp_salt_v1"
TOTP_KDF_INFO: bytes = b"totp_fernet_key_derivation"


def _derive_fernet_key(master_secret: str) -> bytes:
    """
    Derives a cryptographically strong 32-byte URL-safe base64 key
    from the application SECRET_KEY using HKDF with SHA-256.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=TOTP_KDF_SALT,
        info=TOTP_KDF_INFO,
    )
    derived = hkdf.derive(master_secret.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


def _get_fernet_cipher() -> Fernet:
    """Returns an initialized Fernet symmetric cipher instance."""
    secret = _get_secret_key()
    fernet_key = _derive_fernet_key(secret)
    return Fernet(fernet_key)


def encrypt_totp_secret(secret_plaintext: str) -> str:
    """
    Encrypts a plaintext base32 TOTP secret string with Fernet symmetric encryption.
    Returns ciphertext string for secure persistence in database.
    """
    if not secret_plaintext or not secret_plaintext.strip():
        raise ValueError("Cannot encrypt an empty TOTP secret.")

    cipher = _get_fernet_cipher()
    encrypted_bytes = cipher.encrypt(secret_plaintext.strip().encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_totp_secret(ciphertext: str) -> str:
    """
    Decrypts a Fernet ciphertext string back to the plaintext base32 TOTP secret.
    Raises InvalidToken if ciphertext has been tampered with or key is invalid.
    """
    if not ciphertext or not ciphertext.strip():
        raise ValueError("Cannot decrypt an empty TOTP ciphertext.")

    cipher = _get_fernet_cipher()
    decrypted_bytes = cipher.decrypt(ciphertext.strip().encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
