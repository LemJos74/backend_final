from backend.repositories import reportes as repositorio
from backend.schemas.reportes import ReporteMioItem, ReporteRegistroRequest


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


def listar_mios(
    usuario_id: int,
    limite: int,
    desplazamiento: int,
) -> list[ReporteMioItem]:
    """Return the authenticated citizen's reports."""
    filas = repositorio.listar_mios(usuario_id, limite, desplazamiento)
    return [
        ReporteMioItem(
            id=int(fila["id"]),
            tipo_id=int(fila["tipo_id"]),
            tipo_nombre=fila["tipo_nombre"],
            distrito_id=int(fila["distrito_id"]),
            distrito_nombre=fila["distrito_nombre"],
            estado_id=int(fila["estado_id"]),
            estado_nombre=fila["estado_nombre"],
            descripcion=fila["descripcion"],
            ubicacion=fila["ubicacion"],
            latitud=fila["latitud"],
            longitud=fila["longitud"],
            created_at=fila["created_at"],
        )
        for fila in filas
    ]
