from fastapi import APIRouter, Depends, HTTPException, status

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    EstadoReporteNoConfiguradoError,
    ReporteConflictoError,
    ReporteDatosInvalidosError,
    ReporteNoAutorizadoError,
    ReporteReferenciaInvalidaError,
)
from backend.schemas.reportes import (
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
