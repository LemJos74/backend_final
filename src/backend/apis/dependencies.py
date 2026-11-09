from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.exceptions import TokenInvalidoError, UsuarioNoAutorizadoError
from backend.core.security import decodificar_token
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import usuarios as servicio

_bearer = HTTPBearer(auto_error=False)


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UsuarioPerfilResponse:
    """Resolve the current active user from a Bearer access token."""
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise _no_autenticado()

    try:
        usuario_id = decodificar_token(credenciales.credentials)
        return servicio.obtener_perfil_activo(usuario_id)
    except (TokenInvalidoError, UsuarioNoAutorizadoError):
        raise _no_autenticado() from None
