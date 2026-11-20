from typing import Any

from backend.core.exceptions import UsuarioNoAutorizadoError
from backend.core.security import hash_password
from backend.repositories import usuarios as repositorio
from backend.schemas.usuarios import (
    UsuarioPerfilResponse,
    UsuarioPerfilUpdateRequest,
    UsuarioRegistroRequest,
)


def _perfil_desde_fila(fila: dict[str, Any]) -> UsuarioPerfilResponse:
    """Map a profile row returned by PostgreSQL to the API schema."""
    return UsuarioPerfilResponse(
        id=int(fila["id"]),
        nombre=fila["nombre"],
        email=fila["email"],
        rol=fila["rol_nombre"],
        created_at=fila["created_at"],
    )


def registrar_usuario(datos: UsuarioRegistroRequest) -> int:
    """Hash the password and register the citizen through the procedure."""
    password_hash = hash_password(datos.password.get_secret_value())
    return repositorio.registrar_usuario(
        nombre=datos.nombre,
        email=str(datos.email),
        password_hash=password_hash,
    )


def obtener_perfil_activo(usuario_id: int) -> UsuarioPerfilResponse:
    """Return the current profile, rejecting missing or inactive users."""
    fila = repositorio.obtener_por_id(usuario_id)
    if fila is None or not fila["activo"]:
        raise UsuarioNoAutorizadoError
    return _perfil_desde_fila(fila)


def actualizar_perfil(
    usuario_id: int,
    datos: UsuarioPerfilUpdateRequest,
) -> UsuarioPerfilResponse:
    """Update the name and return the profile read in the same transaction."""
    fila = repositorio.actualizar_perfil(usuario_id, datos.nombre)
    if fila is None or not fila["activo"]:
        raise UsuarioNoAutorizadoError
    return _perfil_desde_fila(fila)
