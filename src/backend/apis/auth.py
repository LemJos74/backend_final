from fastapi import APIRouter, Depends, HTTPException, status

from backend.apis.dependencies import obtener_usuario_actual
from backend.core.exceptions import CredencialesInvalidasError
from backend.schemas.auth import LoginRequest, TokenAccesoResponse
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import auth as servicio_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/login",
    response_model=TokenAccesoResponse,
    responses={401: {"description": "Credenciales inválidas"}},
)
def iniciar_sesion(datos: LoginRequest) -> TokenAccesoResponse:
    """Authenticate a user and return a Bearer access token."""
    try:
        return servicio_auth.iniciar_sesion(datos)
    except CredencialesInvalidasError:
        raise _credenciales_invalidas() from None


@router.get(
    "/me",
    response_model=UsuarioPerfilResponse,
    responses={401: {"description": "No autenticado"}},
)
def obtener_me(
    usuario: UsuarioPerfilResponse = Depends(obtener_usuario_actual),
) -> UsuarioPerfilResponse:
    """Return the profile of the authenticated user."""
    return usuario
