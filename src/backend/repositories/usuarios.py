from typing import Any

import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row

from backend.core.database import get_connection
from backend.core.exceptions import (
    EmailDuplicadoError,
    UltimoAdministradorActivoError,
    UsuarioAutodesactivacionError,
    UsuarioConsultaInvalidaError,
    UsuarioDatosInvalidosError,
    UsuarioNoAutorizadoError,
    UsuarioNoConfiguradoError,
    UsuarioNoEncontradoError,
)

_SQL_REGISTRAR = "CALL public.sp_usuario_registrar(%s, %s, %s, %s)"
_SQL_ACTUALIZAR_PERFIL = "CALL public.sp_usuario_actualizar_perfil(%s, %s)"
_SQL_OBTENER_POR_ID = "SELECT * FROM public.fn_usuario_obtener_por_id(%s)"
_SQL_LISTAR_ADMIN = (
    "SELECT * FROM public.fn_usuario_listar_admin("
    "%s::bigint, %s::text, %s::varchar, %s::boolean, %s::integer, %s::integer)"
)
_SQL_CAMBIAR_ESTADO_ADMIN = (
    "CALL public.sp_usuario_cambiar_estado_admin("
    "%s::bigint, %s::bigint, %s::boolean, NULL, NULL, NULL)"
)
_CONSTRAINT_EMAIL = "ux_usuarios_email_normalizado"
_CODIGOS_DATOS_INVALIDOS = frozenset({"22001", "22023", "23514"})
_CODIGOS_NO_CONFIGURADO = frozenset({"42501", "42883"})


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
            cursor.execute(_SQL_OBTENER_POR_ID, (usuario_id,))
            return cursor.fetchone()


def actualizar_perfil(
    usuario_id: int,
    nombre: str,
) -> dict[str, Any] | None:
    """Update the name and read the updated profile in one transaction."""
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        _SQL_ACTUALIZAR_PERFIL,
                        (usuario_id, nombre),
                    )
                    cursor.execute(_SQL_OBTENER_POR_ID, (usuario_id,))
                    return cursor.fetchone()
    except psycopg.Error as error:
        if error.sqlstate in _CODIGOS_DATOS_INVALIDOS:
            raise UsuarioDatosInvalidosError from error
        if error.sqlstate == "P0002":
            raise UsuarioNoAutorizadoError from error
        if error.sqlstate in _CODIGOS_NO_CONFIGURADO:
            raise UsuarioNoConfiguradoError from error
        raise


def listar_admin(
    admin_id: int,
    busqueda: str | None,
    rol: str | None,
    activo: bool | None,
    limite: int,
    desplazamiento: int,
) -> list[dict[str, Any]]:
    """List users through the administrative stored function."""
    try:
        with get_connection() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    _SQL_LISTAR_ADMIN,
                    (
                        admin_id,
                        busqueda,
                        rol,
                        activo,
                        limite,
                        desplazamiento,
                    ),
                )
                return cursor.fetchall()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise UsuarioConsultaInvalidaError from error
        if error.sqlstate == "42501":
            raise UsuarioNoAutorizadoError from error
        if error.sqlstate == "42883":
            raise UsuarioNoConfiguradoError from error
        raise


def cambiar_estado_admin(
    admin_id: int,
    usuario_id: int,
    activo: bool,
) -> dict[str, Any]:
    """Change a user's state through the administrative procedure."""
    try:
        with get_connection() as connection:
            with connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        _SQL_CAMBIAR_ESTADO_ADMIN,
                        (admin_id, usuario_id, activo),
                    )
                    fila = cursor.fetchone()
    except psycopg.Error as error:
        if error.sqlstate == "22023":
            raise UsuarioDatosInvalidosError from error
        if error.sqlstate == "23514":
            raise UsuarioAutodesactivacionError from error
        if error.sqlstate == "55000":
            raise UltimoAdministradorActivoError from error
        if error.sqlstate == "P0002":
            raise UsuarioNoEncontradoError from error
        if error.sqlstate == "42501":
            raise UsuarioNoAutorizadoError from error
        if error.sqlstate == "42883":
            raise UsuarioNoConfiguradoError from error
        raise

    if fila is None:
        raise RuntimeError(
            "El procedimiento no devolvió el estado actualizado del usuario"
        )
    return fila
