from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.apis.catalogos import router as catalogos_router
from backend.apis.usuarios import router as usuarios_router
from backend.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(catalogos_router)
app.include_router(usuarios_router)


@app.exception_handler(RequestValidationError)
async def manejar_error_validacion(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return validation errors without echoing submitted values."""
    detalles = [
        {
            clave: valor
            for clave, valor in error.items()
            if clave not in ("input", "ctx")
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalles})


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
