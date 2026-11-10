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
    ReporteNoAutorizadoError,
    ReporteReferenciaInvalidaError,
)

_SQL_REGISTRAR = (
    "CALL public.sp_reporte_registrar(%s, %s, %s, %s, %s, %s, %s, %s)"
)
_SQL_LISTAR_MIOS = (
    "SELECT * FROM public.fn_reporte_listar_mios(%s, %s, %s)"
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
) -> int:
    """Register a report through sp_reporte_registrar and return its id."""
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        _SQL_REGISTRAR,
                        (
                            usuario_id,
                            distrito_id,
                            tipo_id,
                            descripcion,
                            ubicacion,
                            latitud,
                            longitud,
                            None,
                        ),
                    )
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
