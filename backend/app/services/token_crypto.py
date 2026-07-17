"""Symmetric encryption for tokens at rest (Google Classroom refresh/access
tokens).

This derives a Fernet key from `settings.SECRET_KEY` so no new secret needs
provisioning to get a working increment. That is a reasonable default, not
the final answer: Role 4 owns "secure token storage" per the blueprint (6.4
— "Support Role 2 with ... secure token storage"), and should replace this
with a dedicated, rotated `GOOGLE_TOKEN_ENCRYPTION_KEY` from a secrets
manager. Swapping it in is a one-line change in `_get_fernet()` below.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    raw_key = settings.GOOGLE_TOKEN_ENCRYPTION_KEY
    if raw_key:
        key = raw_key.encode()
    else:
        # Derive a stable 32-byte key from the app's existing SECRET_KEY so
        # nothing new has to be provisioned for this increment to work.
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_token(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
