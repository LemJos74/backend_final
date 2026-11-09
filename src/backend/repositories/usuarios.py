from typing import Any

from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from backend.core.database import get_connection
from backend.core.exceptions import EmailDuplicadoError

_SQL_REGISTRAR = "CALL public.sp_usuario_registrar(%s, %s, %s, %s)"
_CONSTRAINT_EMAIL = "ux_usuarios_email_normalizado"


def registrar_usuario(nombre: str, email: str, password_hash: str) -> int:
    """Register a user through sp_usuario_registrar and return its id."""
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        _SQL_REGISTRAR,
                        (nombre, email, password_hash, None),
                    )
                    fila = cursor.fetchone()
    except UniqueViolation as error:
        if error.diag.constraint_name == _CONSTRAINT_EMAIL:
            raise EmailDuplicadoError from error
        raise

    if fila is None or fila[0] is None:
        raise RuntimeError(
            "El procedimiento no devolvió el identificador del usuario"
        )
    return int(fila[0])


def obtener_credenciales_por_email(email: str) -> dict[str, Any] | None:
    """Read login credentials through fn_usuario_obtener_por_email()."""
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM public.fn_usuario_obtener_por_email(%s)",
                (email,),
            )
            return cursor.fetchone()


def obtener_por_id(usuario_id: int) -> dict[str, Any] | None:
    """Read a user profile through fn_usuario_obtener_por_id()."""
    with get_connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM public.fn_usuario_obtener_por_id(%s)",
                (usuario_id,),
            )
            return cursor.fetchone()
