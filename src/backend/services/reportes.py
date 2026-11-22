from backend.core.almacenamiento_fotografias import obtener_almacen
from backend.core.exceptions import (
    EstadoReporteNoConfiguradoError,
    ReporteConflictoError,
    ReporteDatosInvalidosError,
    ReporteFotografiaNoEncontradaError,
    ReporteNoAutorizadoError,
)
from backend.core.fotografias import procesar_fotografia
from backend.repositories import reportes as repositorio
from backend.schemas.reportes import (
    ReporteAdminItem,
    ReporteCambioEstadoResponse,
    ReporteDetalleItem,
    ReporteMioItem,
    ReporteRegistroRequest,
)


def registrar_reporte(
    usuario_id: int, datos: ReporteRegistroRequest, imagen_path: str | None = None
) -> int:
    """Register a report for the authenticated citizen."""
    return repositorio.registrar_reporte(
        usuario_id=usuario_id,
        distrito_id=datos.distrito_id,
        tipo_id=datos.tipo_id,
        descripcion=datos.descripcion,
        ubicacion=datos.ubicacion,
        latitud=datos.latitud,
        longitud=datos.longitud,
        imagen_path=imagen_path,
    )


def registrar_con_fotografia(
    usuario_id: int, datos: ReporteRegistroRequest, contenido: bytes
) -> int:
    jpeg = procesar_fotografia(contenido)
    almacen = obtener_almacen()
    clave = almacen.guardar(jpeg)
    try:
        return registrar_reporte(usuario_id, datos, clave)
    except (
        EstadoReporteNoConfiguradoError,
        ReporteConflictoError,
        ReporteDatosInvalidosError,
        ReporteNoAutorizadoError,
    ):
        almacen.eliminar(clave)
        raise


def obtener_fotografia(reporte_id: int, usuario_id: int) -> bytes:
    fila = repositorio.obtener_reporte(reporte_id, usuario_id)
    if fila is None or fila["imagen_path"] is None:
        raise ReporteFotografiaNoEncontradaError
    return obtener_almacen().leer(fila["imagen_path"])


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
        tiene_fotografia=fila["imagen_path"] is not None,
        fotografia_url=(
            f"/api/reportes/{reporte_id}/fotografia"
            if fila["imagen_path"] is not None
            else None
        ),
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


def cambiar_estado(
    admin_id: int,
    reporte_id: int,
    estado_id: int,
    justificacion: str | None,
) -> ReporteCambioEstadoResponse:
    """Change a report state and return the resulting state summary."""
    fila = repositorio.cambiar_estado(
        admin_id=admin_id,
        reporte_id=reporte_id,
        estado_id=estado_id,
        justificacion=justificacion,
    )
    return ReporteCambioEstadoResponse(
        id=reporte_id,
        estado_id=int(fila["p_estado_id"]),
        estado_nombre=fila["p_estado_nombre"],
        observacion_admin=fila["p_observacion_admin"],
        updated_at=fila["p_updated_at"],
    )
