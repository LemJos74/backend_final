from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.apis.auth import router as auth_router
from backend.apis.catalogos import router as catalogos_router
from backend.apis.dashboard import router as dashboard_router
from backend.apis.reportes import router as reportes_router
from backend.apis.reportes_admin import router as reportes_admin_router
from backend.apis.usuarios import router as usuarios_router
from backend.apis.usuarios_admin import router as usuarios_admin_router
from backend.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
app.include_router(auth_router)
app.include_router(catalogos_router)
app.include_router(dashboard_router)
app.include_router(reportes_router)
app.include_router(reportes_admin_router)
app.include_router(usuarios_router)
app.include_router(usuarios_admin_router)


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
