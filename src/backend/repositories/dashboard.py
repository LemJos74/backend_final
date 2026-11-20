from typing import Any

import psycopg
from psycopg.rows import dict_row

from backend.core.database import get_connection
from backend.core.exceptions import (
    ReporteConsultaNoConfiguradaError,
    ReporteNoAutorizadoError,
)

_SQL_ESTADISTICAS = (
    "SELECT * FROM public.fn_reporte_estadisticas_admin(%s::bigint)"
)


def obtener_estadisticas(admin_id: int) -> list[dict[str, Any]]:
    """Read the dashboard indicators through the stored function."""
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(_SQL_ESTADISTICAS, (admin_id,))
                return cursor.fetchall()
    except psycopg.Error as error:
        if error.sqlstate == "42501":
            raise ReporteNoAutorizadoError from error
        if error.sqlstate == "42883":
            raise ReporteConsultaNoConfiguradaError from error
        raise
