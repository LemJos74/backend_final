from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from backend.core.database import get_connection
from backend.core.exceptions import (
    EstadoReporteNoConfiguradoError,
    ReporteConflictoError,
    ReporteConsultaInvalidaError,
    ReporteConsultaNoConfiguradaError,
    ReporteDatosInvalidosError,
    ReporteJustificacionRequeridaError,
    ReporteNoAutorizadoError,
    ReporteNoEncontradoError,
    ReporteReferenciaInvalidaError,
    ReporteTransicionInvalidaError,
)

_SQL_REGISTRAR = (
    "CALL public.sp_reporte_registrar(%s, %s, %s, %s, %s, %s, %s, %s)"
)
_SQL_REGISTRAR_CON_FOTOGRAFIA = (
    "CALL public.sp_reporte_registrar_con_fotografia(%s, %s, %s, %s, %s, %s, %s, %s, %s)"
)
_SQL_LISTAR_MIOS = (
    "SELECT * FROM public.fn_reporte_listar_mios(%s, %s, %s)"
)
_SQL_OBTENER = "SELECT * FROM public.fn_reporte_obtener(%s, %s)"
_SQL_LISTAR_ADMIN = (
    "SELECT * FROM public.fn_reporte_listar_admin("
    "%s::bigint, %s::bigint, %s::bigint, %s::bigint, %s::integer, %s::integer)"
)
# PostgreSQL exige argumentos para los cuatro parametros OUT del procedimiento.
# No se evaluan: se envian como NULL y los valores reales vuelven en la fila.
_SQL_CAMBIAR_ESTADO = (
    "CALL public.sp_reporte_cambiar_estado("
    "%s, %s, %s, %s, NULL, NULL, NULL, NULL)"
)
_CODIGOS_DATOS_INVALIDOS = frozenset({"22001", "22003", "22023", "23502", "23514"})
_CODIGOS_CONSULTA_NO_CONFIGURADA = frozenset({"42501", "42883"})


def registrar_reporte(
    usuario_id: int,
    distrito_id: int,
    tipo_id: int,
    descripcion: str,
    ubicacion: str,
    latitud: Decimal,
    longitud: Decimal,
    imagen_path: str | None = None,
) -> int:
    """Register a report through sp_reporte_registrar and return its id."""
    consulta = _SQL_REGISTRAR
    parametros = (usuario_id, distrito_id, tipo_id, descripcion, ubicacion, latitud, longitud)
    if imagen_path is not None:
        consulta = _SQL_REGISTRAR_CON_FOTOGRAFIA
        parametros += (imagen_path,)
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(consulta, (*parametros, None))
                    fila = cursor.fetchone()
    except psycopg.Error as error:
        sqlstate = error.sqlstate

        if sqlstate == "23503":
            raise ReporteReferenciaInvalidaError from error
        if sqlstate in _CODIGOS_DATOS_INVALIDOS:
            raise ReporteDatosInvalidosError from error
        if sqlstate == "42501":
            raise ReporteNoAutorizadoError from error
        if sqlstate == "P0002":
            raise EstadoReporteNoConfiguradoError from error
        if sqlstate == "23505":
            raise ReporteConflictoError from error
        raise

    if fila is None or fila[0] is None:
        raise RuntimeError(
            "El procedimiento no devolvió el identificador del reporte"
        )
    return int(fila[0])


def listar_mios(
    usuario_id: int,
    limite: int,
    desplazamiento: int,
) -> list[dict[str, Any]]:
    """List the authenticated citizen's reports through the stored function."""
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    _SQL_LISTAR_MIOS,
                    (usuario_id, limite, desplazamiento),
                )
                return cursor.fetchall()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise ReporteConsultaInvalidaError from error
        if error.sqlstate in _CODIGOS_CONSULTA_NO_CONFIGURADA:
            raise ReporteConsultaNoConfiguradaError from error
        raise


def obtener_reporte(
    reporte_id: int,
    usuario_id: int,
) -> dict[str, Any] | None:
    """Get one report through the stored function."""
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(_SQL_OBTENER, (reporte_id, usuario_id))
                return cursor.fetchone()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise ReporteConsultaInvalidaError from error
        if error.sqlstate in _CODIGOS_CONSULTA_NO_CONFIGURADA:
            raise ReporteConsultaNoConfiguradaError from error
        raise


def listar_admin(
    admin_id: int,
    distrito_id: int | None,
    tipo_id: int | None,
    estado_id: int | None,
    limite: int,
    desplazamiento: int,
) -> list[dict[str, Any]]:
    """List every report through fn_reporte_listar_admin (admin only)."""
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    _SQL_LISTAR_ADMIN,
                    (
                        admin_id,
                        distrito_id,
                        tipo_id,
                        estado_id,
                        limite,
                        desplazamiento,
                    ),
                )
                return cursor.fetchall()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise ReporteConsultaInvalidaError from error
        if error.sqlstate == "42501":
            raise ReporteNoAutorizadoError from error
        if error.sqlstate == "42883":
            raise ReporteConsultaNoConfiguradaError from error
        raise


def cambiar_estado(
    admin_id: int,
    reporte_id: int,
    estado_id: int,
    justificacion: str | None,
) -> dict[str, Any]:
    """Change a report state through sp_reporte_cambiar_estado."""
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        _SQL_CAMBIAR_ESTADO,
                        (admin_id, reporte_id, estado_id, justificacion),
                    )
                    fila = cursor.fetchone()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise ReporteDatosInvalidosError from error
        if error.sqlstate == "23502":
            raise ReporteJustificacionRequeridaError from error
        if error.sqlstate == "55000":
            raise ReporteTransicionInvalidaError from error
        if error.sqlstate == "P0002":
            raise ReporteNoEncontradoError from error
        if error.sqlstate == "42501":
            raise ReporteNoAutorizadoError from error
        if error.sqlstate == "42883":
            raise ReporteConsultaNoConfiguradaError from error
        raise

    if fila is None:
        raise RuntimeError(
            "El procedimiento no devolvió el estado actualizado del reporte"
        )
    return fila

