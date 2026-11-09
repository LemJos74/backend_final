import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# src/backend/core/config.py -> repository root
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_FILE)


def _leer_minutos_expiracion() -> int:
    valor = os.getenv("JWT_EXPIRE_MINUTES", "30")
    try:
        return int(valor)
    except ValueError as error:
        raise RuntimeError(
            "JWT_EXPIRE_MINUTES debe ser un número entero"
        ) from error


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "LimpiaHuancayo API")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "limpiahuancayo")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    jwt_secret: str = field(
        default=os.getenv("JWT_SECRET", ""),
        repr=False,
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = _leer_minutos_expiracion()


settings = Settings()

if len(settings.jwt_secret) < 32:
    raise RuntimeError(
        "JWT_SECRET debe estar definido y tener al menos 32 caracteres"
    )
if settings.jwt_algorithm != "HS256":
    raise RuntimeError("JWT_ALGORITHM solo admite HS256")
if settings.jwt_expire_minutes <= 0:
    raise RuntimeError("JWT_EXPIRE_MINUTES debe ser mayor que cero")
