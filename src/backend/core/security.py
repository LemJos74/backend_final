from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from backend.core.config import settings
from backend.core.exceptions import TokenInvalidoError

_hasher = PasswordHasher(type=Type.ID)
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    """Return an Argon2id hash for the given password."""
    return _hasher.hash(password)


def verificar_password(password_hash: str, password: str) -> bool:
    """Check a password against its Argon2id hash without raising."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def verificar_password_dummy(password: str) -> None:
    """Spend time verifying a dummy hash when the user does not exist."""
    try:
        _hasher.verify(_DUMMY_HASH, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        pass


def crear_token_acceso(usuario_id: int) -> str:
    """Create a signed HS256 access token for a positive user id."""
    if usuario_id <= 0:
        raise ValueError("El identificador de usuario debe ser positivo")

    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decodificar_token(token: str) -> int:
    """Validate a token and return its positive integer user id."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "iat", "exp"]},
            leeway=0,
        )
        sub = payload["sub"]
        if not isinstance(sub, str) or not (sub.isascii() and sub.isdigit()):
            raise TokenInvalidoError
        usuario_id = int(sub)
        if usuario_id <= 0:
            raise TokenInvalidoError
    except TokenInvalidoError:
        raise
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise TokenInvalidoError from error

    return usuario_id
