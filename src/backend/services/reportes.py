from backend.repositories import reportes as repositorio
from backend.schemas.reportes import ReporteRegistroRequest


def registrar_reporte(usuario_id: int, datos: ReporteRegistroRequest) -> int:
    """Register a report for the authenticated citizen."""
    return repositorio.registrar_reporte(
        usuario_id=usuario_id,
        distrito_id=datos.distrito_id,
        tipo_id=datos.tipo_id,
        descripcion=datos.descripcion,
        ubicacion=datos.ubicacion,
        latitud=datos.latitud,
        longitud=datos.longitud,
    )
