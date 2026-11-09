import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# src/backend/core/config.py -> repository root
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "LimpiaHuancayo API")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "limpiahuancayo")
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")


settings = Settings()
