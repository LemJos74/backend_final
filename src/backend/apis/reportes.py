from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    EstadoReporteNoConfiguradoError,
    ReporteConflictoError,
    ReporteConsultaInvalidaError,
    ReporteConsultaNoConfiguradaError,
    ReporteDatosInvalidosError,
    ReporteNoAutorizadoError,
    ReporteReferenciaInvalidaError,
)
from backend.schemas.reportes import (
    ReporteMioItem,
    ReporteRegistroRequest,
    ReporteRegistroResponse,
)
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import reportes as servicio

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


@router.post(
    "",
    response_model=ReporteRegistroResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        409: {"description": "No se pudo registrar el reporte"},
        422: {"description": "Datos del reporte inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def registrar_reporte(
    datos: ReporteRegistroRequest,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano")),
) -> ReporteRegistroResponse:
    """Register a report for the authenticated citizen."""
    try:
        reporte_id = servicio.registrar_reporte(usuario.id, datos)
    except ReporteReferenciaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El distrito o el tipo de reporte no existe",
        ) from None
    except ReporteDatosInvalidosError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Datos del reporte inválidos",
        ) from None
    except ReporteNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except EstadoReporteNoConfiguradoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
    except ReporteConflictoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar el reporte",
        ) from None

    return ReporteRegistroResponse(id=reporte_id)


@router.get(
    "/mios",
    response_model=list[ReporteMioItem],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        422: {"description": "Parámetros de consulta inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def listar_mis_reportes(
    limite: Annotated[
        int,
        Query(ge=1, le=100, description="Cantidad máxima de reportes"),
    ] = 20,
    desplazamiento: Annotated[
        int,
        Query(ge=0, description="Cantidad de reportes a omitir"),
    ] = 0,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano")),
) -> list[ReporteMioItem]:
    """Return only the authenticated citizen's reports."""
    try:
        return servicio.listar_mios(usuario.id, limite, desplazamiento)
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
