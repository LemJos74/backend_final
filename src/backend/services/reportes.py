from backend.repositories import reportes as repositorio
from backend.schemas.reportes import (
    ReporteAdminItem,
    ReporteDetalleItem,
    ReporteMioItem,
    ReporteRegistroRequest,
)


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


def obtener_reporte(
    reporte_id: int,
    usuario_id: int,
) -> ReporteDetalleItem | None:
    """Return one report allowed for the authenticated user."""
    fila = repositorio.obtener_reporte(reporte_id, usuario_id)
    if fila is None:
        return None

    return ReporteDetalleItem(
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
        imagen_path=fila["imagen_path"],
        observacion_admin=fila["observacion_admin"],
        created_at=fila["created_at"],
        updated_at=fila["updated_at"],
    )


def listar_admin(
    admin_id: int,
    distrito_id: int | None,
    tipo_id: int | None,
    estado_id: int | None,
    limite: int,
    desplazamiento: int,
) -> list[ReporteAdminItem]:
    """Return every report for an authenticated administrator."""
    filas = repositorio.listar_admin(
        admin_id=admin_id,
        distrito_id=distrito_id,
        tipo_id=tipo_id,
        estado_id=estado_id,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return [
        ReporteAdminItem(
            id=int(fila["id"]),
            usuario_id=int(fila["usuario_id"]),
            usuario_nombre=fila["usuario_nombre"],
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
            updated_at=fila["updated_at"],
        )
        for fila in filas
    ]
