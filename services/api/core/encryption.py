"""AES-256 encryption for user photos at rest (local storage)."""

import base64
import os

from cryptography.fernet import Fernet

from services.api.core.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    key_material = settings.app_secret_key.encode("utf-8")
    key = base64.urlsafe_b64encode(key_material.ljust(32)[:32])
    return Fernet(key)


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet().decrypt(token)
