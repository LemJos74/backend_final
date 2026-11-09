from psycopg.errors import UniqueViolation

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
