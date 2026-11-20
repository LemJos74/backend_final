from fastapi import APIRouter, Depends, HTTPException, status

from backend.apis.dependencies import obtener_usuario_actual
from backend.core.exceptions import (
    CredencialesInvalidasError,
    UsuarioDatosInvalidosError,
    UsuarioNoAutorizadoError,
    UsuarioNoConfiguradoError,
)
from backend.schemas.auth import LoginRequest, TokenAccesoResponse
from backend.schemas.usuarios import (
    UsuarioPerfilResponse,
    UsuarioPerfilUpdateRequest,
)
from backend.services import auth as servicio_auth
from backend.services import usuarios as servicio_usuarios

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _credenciales_invalidas() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
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


@router.patch(
    "/me",
    response_model=UsuarioPerfilResponse,
    responses={
        401: {"description": "No autenticado"},
        422: {"description": "Datos del perfil inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def actualizar_me(
    datos: UsuarioPerfilUpdateRequest,
    usuario: UsuarioPerfilResponse = Depends(obtener_usuario_actual),
) -> UsuarioPerfilResponse:
    """Update the name of the authenticated user."""
    try:
        return servicio_usuarios.actualizar_perfil(usuario.id, datos)
    except UsuarioDatosInvalidosError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Datos del perfil inválidos",
        ) from None
    except UsuarioNoAutorizadoError:
        raise _no_autenticado() from None
    except UsuarioNoConfiguradoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
