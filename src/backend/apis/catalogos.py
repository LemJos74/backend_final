from fastapi import APIRouter

from backend.schemas.catalogos import Distrito, EstadoReporte, TipoReporte
from backend.services import catalogos as servicio

router = APIRouter(prefix="/api/catalogos", tags=["catalogos"])


@router.get("/distritos", response_model=list[Distrito])
def listar_distritos() -> list[Distrito]:
    """Return the district catalog."""
    return servicio.listar_distritos()


@router.get("/tipos-reporte", response_model=list[TipoReporte])
def listar_tipos_reporte() -> list[TipoReporte]:
    """Return the report type catalog."""
    return servicio.listar_tipos_reporte()


@router.get("/estados-reporte", response_model=list[EstadoReporte])
def listar_estados_reporte() -> list[EstadoReporte]:
    """Return the report state catalog."""
    return servicio.listar_estados_reporte()
