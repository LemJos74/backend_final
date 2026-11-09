from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "LimpiaHuancayo API"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
