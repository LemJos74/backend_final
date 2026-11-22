from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import AfterValidator

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    UltimoAdministradorActivoError,
    UsuarioAutodesactivacionError,
    UsuarioConsultaInvalidaError,
    UsuarioDatosInvalidosError,
    UsuarioNoAutorizadoError,
    UsuarioNoConfiguradoError,
    UsuarioNoEncontradoError,
)
from backend.schemas.usuarios import (
    UsuarioAdminEstadoRequest,
    UsuarioAdminEstadoResponse,
    UsuarioAdminItem,
    UsuarioPerfilResponse,
)
from backend.services import usuarios as servicio

router = APIRouter(prefix="/api/admin/usuarios", tags=["admin-usuarios"])


def _rechazar_nulo_busqueda(valor: str | None) -> str | None:
    """Reject NUL characters in the optional search parameter."""
    if valor is not None and "\x00" in valor:
        raise ValueError("La búsqueda contiene caracteres no permitidos")
    return valor


@router.get(
    "",
    response_model=list[UsuarioAdminItem],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        422: {"description": "Parámetros de consulta inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def listar_usuarios_admin(
    busqueda: Annotated[
        str | None,
        Query(max_length=254, description="Busca por nombre o correo"),
        AfterValidator(_rechazar_nulo_busqueda),
    ] = None,
    rol: Annotated[
        Literal["Ciudadano", "Administrador"] | None,
        Query(description="Filtra por rol"),
    ] = None,
    activo: Annotated[
        bool | None,
        Query(description="Filtra por estado activo o inactivo"),
    ] = None,
    limite: Annotated[
        int,
        Query(ge=1, le=100, description="Cantidad máxima de usuarios"),
    ] = 20,
    desplazamiento: Annotated[
        int,
        Query(
            ge=0,
            le=2**31 - 1,  # máximo de INTEGER en PostgreSQL
            description="Cantidad de usuarios a omitir",
        ),
    ] = 0,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Administrador")),
) -> list[UsuarioAdminItem]:
    """List every user; administrator role required."""
    try:
        return servicio.listar_admin(
            admin_id=usuario.id,
            busqueda=busqueda,
            rol=rol,
            activo=activo,
            limite=limite,
            desplazamiento=desplazamiento,
        )
    except UsuarioNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except UsuarioConsultaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parámetros de consulta inválidos",
        ) from None
    except UsuarioNoConfiguradoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None


@router.patch(
    "/{usuario_id}/estado",
    response_model=UsuarioAdminEstadoResponse,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        404: {"description": "Usuario no encontrado"},
        409: {
            "description": (
                "No se puede desactivar al último administrador activo"
            )
        },
        422: {"description": "Datos del cambio de estado inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def cambiar_estado_usuario(
    datos: UsuarioAdminEstadoRequest,
    usuario_id: Annotated[
        int,
        Path(
            gt=0,
            le=2**63 - 1,
            description="Identificador del usuario",
        ),
    ],
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Administrador")),
) -> UsuarioAdminEstadoResponse:
    """Activate or deactivate one user; administrator role required."""
    try:
        return servicio.cambiar_estado_admin(
            admin_id=usuario.id,
            usuario_id=usuario_id,
            activo=datos.activo,
        )
    except UsuarioNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        ) from None
    except UsuarioAutodesactivacionError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No puede desactivar su propia cuenta",
        ) from None
    except UltimoAdministradorActivoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede desactivar al último administrador activo",
        ) from None
    except UsuarioDatosInvalidosError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Datos del cambio de estado inválidos",
        ) from None
    except UsuarioNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except UsuarioNoConfiguradoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
