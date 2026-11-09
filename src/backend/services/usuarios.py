from argon2 import PasswordHasher, Type

from backend.repositories import usuarios as repositorio
from backend.schemas.usuarios import UsuarioRegistroRequest

_hasher = PasswordHasher(type=Type.ID)


def registrar_usuario(datos: UsuarioRegistroRequest) -> int:
    """Hash the password and register the citizen through the procedure."""
    password_hash = _hasher.hash(datos.password.get_secret_value())
    return repositorio.registrar_usuario(
        nombre=datos.nombre,
        email=str(datos.email),
        password_hash=password_hash,
    )
