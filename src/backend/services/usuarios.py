from typing import Any

from backend.core.exceptions import UsuarioNoAutorizadoError
from backend.core.security import hash_password
from backend.repositories import usuarios as repositorio
from backend.schemas.usuarios import (
    UsuarioAdminEstadoResponse,
    UsuarioAdminItem,
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


def _usuario_admin_desde_fila(fila: dict[str, Any]) -> UsuarioAdminItem:
    """Map an administrative user row to the API schema."""
    return UsuarioAdminItem(
        id=int(fila["id"]),
        nombre=fila["nombre"],
        email=fila["email"],
        rol_id=int(fila["rol_id"]),
        rol=fila["rol_nombre"],
        activo=fila["activo"],
        created_at=fila["created_at"],
    )


def listar_admin(
    admin_id: int,
    busqueda: str | None,
    rol: str | None,
    activo: bool | None,
    limite: int,
    desplazamiento: int,
) -> list[UsuarioAdminItem]:
    """Return every user for an authenticated administrator."""
    filas = repositorio.listar_admin(
        admin_id=admin_id,
        busqueda=busqueda,
        rol=rol,
        activo=activo,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return [_usuario_admin_desde_fila(fila) for fila in filas]


def cambiar_estado_admin(
    admin_id: int,
    usuario_id: int,
    activo: bool,
) -> UsuarioAdminEstadoResponse:
    """Change a user's state and return the resulting state summary."""
    fila = repositorio.cambiar_estado_admin(
        admin_id=admin_id,
        usuario_id=usuario_id,
        activo=activo,
    )
    return UsuarioAdminEstadoResponse(
        id=int(fila["p_id"]),
        activo=fila["p_activo_resultado"],
        updated_at=fila["p_updated_at"],
    )
