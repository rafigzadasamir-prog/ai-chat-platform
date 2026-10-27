"""Password hashing and JWT access tokens.

Uses passlib's ``pbkdf2_sha256`` scheme rather than bcrypt: it is pure
hashlib under the hood (no compiled extension / version-pinning headaches)
while still being a slow, salted, industry-standard KDF suitable for
password storage.
"""

import datetime as dt
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire_delta = dt.timedelta(
        minutes=expires_minutes
        if expires_minutes is not None
        else settings.access_token_expire_minutes
    )
    now = dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": now + expire_delta}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> str:
    """Return the subject (user id as string) encoded in a valid token.

    Raises InvalidTokenError for anything expired, malformed or tampered.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc
    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token missing subject claim")
    return subject
