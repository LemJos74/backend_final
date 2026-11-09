from backend.core.exceptions import UsuarioNoAutorizadoError
from backend.core.security import hash_password
from backend.repositories import usuarios as repositorio
from backend.schemas.usuarios import (
    UsuarioPerfilResponse,
    UsuarioRegistroRequest,
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
    return UsuarioPerfilResponse(
        id=int(fila["id"]),
        nombre=fila["nombre"],
        email=fila["email"],
        rol=fila["rol_nombre"],
        created_at=fila["created_at"],
    )
