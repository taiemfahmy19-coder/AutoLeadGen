"""AutoLeadGen V3 — Core Security: Argon2 Hashing, JWT Auth, Fernet Secret Encryption, and RBAC."""
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from cryptography.fernet import Fernet, InvalidToken

from config.settings import DATA_DIR

_MASTER_KEY_FILE = os.path.join(DATA_DIR, ".master.key")
_JWT_SECRET_FILE = os.path.join(DATA_DIR, ".jwt_secret")
_ENC_PREFIX = "enc:v1:"

# Argon2id configuration (OWASP recommended parameters)
_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

# Role-based access permissions
ROLE_PERMISSIONS = {
    "admin": {
        "leads:read", "leads:write", "leads:delete",
        "discovery:run", "discovery:stop",
        "email:compose", "email:approve", "email:send",
        "settings:read", "settings:write",
        "users:manage", "db:backup", "db:wipe",
        "tasks:manage", "ai:run",
    },
    "operator": {
        "leads:read", "leads:write",
        "discovery:run", "discovery:stop",
        "email:compose", "email:send",
        "settings:read",
        "tasks:manage", "ai:run",
    },
    "viewer": {
        "leads:read",
        "settings:read",
    },
}


def _load_or_create_secret(path: str, is_fernet: bool = False) -> bytes:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read().strip()
            if data:
                return data
    raw = Fernet.generate_key() if is_fernet else secrets.token_urlsafe(48).encode("utf-8")
    with open(path, "wb") as f:
        f.write(raw)
    return raw


def get_fernet() -> Fernet:
    key = _load_or_create_secret(_MASTER_KEY_FILE, is_fernet=True)
    return Fernet(key)


def get_jwt_secret() -> str:
    env_secret = os.environ.get("AUTOLEADGEN_JWT_SECRET", "").strip()
    if env_secret:
        return env_secret
    return _load_or_create_secret(_JWT_SECRET_FILE, is_fernet=False).decode("utf-8")


def encrypt_secret(plaintext: str) -> str:
    """Encrypt sensitive secret (e.g. SMTP/IMAP password) with Fernet before disk storage."""
    if not plaintext:
        return ""
    if plaintext.startswith(_ENC_PREFIX):
        return plaintext
    token = get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{_ENC_PREFIX}{token}"


def decrypt_secret(stored_value: str) -> str:
    """Decrypt Fernet-encrypted secret; gracefully passes through legacy plaintext for migration."""
    if not stored_value:
        return ""
    if not stored_value.startswith(_ENC_PREFIX):
        return stored_value
    token = stored_value[len(_ENC_PREFIX):]
    try:
        return get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def hash_password(plain_password: str) -> str:
    """Hash a user password using Argon2id."""
    if not plain_password or len(plain_password) < 4:
        raise ValueError("Password must be at least 4 characters.")
    return _ph.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2id hash."""
    if not plain_password or not password_hash:
        return False
    try:
        return _ph.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(
    user_id: int,
    username: str,
    role: str = "operator",
    expires_hours: int = 24,
) -> str:
    """Create a signed HS256 JWT token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token. Returns payload dict or None if invalid/expired."""
    if not token:
        return None
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def has_permission(role: str, permission: str) -> bool:
    """Check if role grants the specified permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return permission in perms
