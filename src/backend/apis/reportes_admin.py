from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    ReporteConsultaInvalidaError,
    ReporteConsultaNoConfiguradaError,
    ReporteNoAutorizadoError,
)
from backend.schemas.reportes import ReporteAdminItem
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import reportes as servicio

router = APIRouter(prefix="/api/admin/reportes", tags=["admin-reportes"])


@router.get(
    "",
    response_model=list[ReporteAdminItem],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        422: {"description": "Parámetros de consulta inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def listar_reportes_admin(
    limite: Annotated[
        int,
        Query(ge=1, le=100, description="Cantidad máxima de reportes"),
    ] = 20,
    desplazamiento: Annotated[
        int,
        Query(ge=0, description="Cantidad de reportes a omitir"),
    ] = 0,
    distrito_id: Annotated[
        int | None,
        Query(ge=1, description="Filtra por distrito"),
    ] = None,
    tipo_id: Annotated[
        int | None,
        Query(ge=1, description="Filtra por tipo de reporte"),
    ] = None,
    estado_id: Annotated[
        int | None,
        Query(ge=1, description="Filtra por estado"),
    ] = None,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Administrador")),
) -> list[ReporteAdminItem]:
    """List every report; administrator role required."""
    try:
        return servicio.listar_admin(
            admin_id=usuario.id,
            distrito_id=distrito_id,
            tipo_id=tipo_id,
            estado_id=estado_id,
            limite=limite,
            desplazamiento=desplazamiento,
        )
    except ReporteNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except ReporteConsultaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parámetros de consulta inválidos",
        ) from None
    except ReporteConsultaNoConfiguradaError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
