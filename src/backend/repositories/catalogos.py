from backend.core.database import get_connection


def listar_distritos() -> list[tuple[int, str]]:
    """Read the district catalog through fn_distrito_listar()."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM public.fn_distrito_listar()")
            return cursor.fetchall()


def listar_tipos_reporte() -> list[tuple[int, str, str | None]]:
    """Read the report type catalog through fn_tipo_reporte_listar()."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM public.fn_tipo_reporte_listar()")
            return cursor.fetchall()


def listar_estados_reporte() -> list[tuple[int, str]]:
    """Read the report state catalog through fn_estado_reporte_listar()."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM public.fn_estado_reporte_listar()")
            return cursor.fetchall()
