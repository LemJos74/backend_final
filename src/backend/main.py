from fastapi import FastAPI

from backend.apis.catalogos import router as catalogos_router
from backend.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(catalogos_router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "message": "API en funcionamiento",
    }


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness check: only confirms the HTTP server responds."""
    return {"status": "ok"}
