from fastapi import APIRouter, Depends, HTTPException, status

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    ReporteConsultaNoConfiguradaError,
    ReporteNoAutorizadoError,
)
from backend.schemas.dashboard import DashboardResponse
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import dashboard as servicio

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


@router.get(
    "",
    response_model=DashboardResponse,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def obtener_dashboard(
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Administrador")),
) -> DashboardResponse:
    """Return report statistics; administrator role required."""
    try:
        return servicio.obtener_dashboard(usuario.id)
    except ReporteNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except ReporteConsultaNoConfiguradaError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
