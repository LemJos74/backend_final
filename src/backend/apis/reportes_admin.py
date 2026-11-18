from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    ReporteConsultaInvalidaError,
    ReporteConsultaNoConfiguradaError,
    ReporteDatosInvalidosError,
    ReporteJustificacionRequeridaError,
    ReporteNoAutorizadoError,
    ReporteNoEncontradoError,
    ReporteTransicionInvalidaError,
)
from backend.schemas.reportes import (
    ReporteAdminItem,
    ReporteCambioEstadoRequest,
    ReporteCambioEstadoResponse,
)
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


@router.patch(
    "/{reporte_id}/estado",
    response_model=ReporteCambioEstadoResponse,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        404: {"description": "Reporte no encontrado"},
        409: {"description": "Transición de estado no permitida"},
        422: {"description": "Datos del cambio de estado inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def cambiar_estado_reporte(
    datos: ReporteCambioEstadoRequest,
    reporte_id: Annotated[
        int,
        Path(gt=0, description="Identificador del reporte"),
    ],
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Administrador")),
) -> ReporteCambioEstadoResponse:
    """Change the state of one report; administrator role required."""
    try:
        return servicio.cambiar_estado(
            admin_id=usuario.id,
            reporte_id=reporte_id,
            estado_id=datos.estado_id,
            justificacion=datos.justificacion,
        )
    except ReporteNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        ) from None
    except ReporteTransicionInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transición de estado no permitida",
        ) from None
    except ReporteJustificacionRequeridaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La justificación es obligatoria al rechazar un reporte",
        ) from None
    except ReporteDatosInvalidosError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Datos del cambio de estado inválidos",
        ) from None
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
