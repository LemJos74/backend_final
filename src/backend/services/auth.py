from backend.core.config import settings
from backend.core.exceptions import CredencialesInvalidasError
from backend.core.security import (
    crear_token_acceso,
    verificar_password,
    verificar_password_dummy,
)
from backend.repositories import usuarios as repositorio
from backend.schemas.auth import LoginRequest, TokenAccesoResponse


def iniciar_sesion(datos: LoginRequest) -> TokenAccesoResponse:
    """Validate credentials and return a signed access token."""
    password = datos.password.get_secret_value()
    credenciales = repositorio.obtener_credenciales_por_email(str(datos.email))

    if credenciales is None:
        verificar_password_dummy(password)
        raise CredencialesInvalidasError

    if not verificar_password(credenciales["password_hash"], password):
        raise CredencialesInvalidasError

    if not credenciales["activo"]:
        raise CredencialesInvalidasError

    token = crear_token_acceso(int(credenciales["id"]))
    return TokenAccesoResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )
