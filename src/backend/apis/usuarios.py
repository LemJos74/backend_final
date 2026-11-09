from fastapi import APIRouter, HTTPException, status

from backend.core.exceptions import EmailDuplicadoError
from backend.schemas.usuarios import (
    UsuarioRegistroRequest,
    UsuarioRegistroResponse,
)
from backend.services import usuarios as servicio

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.post(
    "/registro",
    response_model=UsuarioRegistroResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    datos: UsuarioRegistroRequest,
) -> UsuarioRegistroResponse:
    """Register a citizen; the database procedure assigns the role."""
    try:
        usuario_id = servicio.registrar_usuario(datos)
    except EmailDuplicadoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado",
        ) from None
    return UsuarioRegistroResponse(id=usuario_id)
