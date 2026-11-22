from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StrictBool,
    StringConstraints,
)


def normalizar_email(valor: Any) -> Any:
    if isinstance(valor, str):
        return valor.strip().lower()
    return valor


def rechazar_caracter_nulo(valor: str) -> str:
    if "\x00" in valor:
        raise ValueError("El nombre contiene caracteres no permitidos")
    return valor


class UsuarioRegistroRequest(BaseModel):
    nombre: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
    ]
    email: Annotated[EmailStr, BeforeValidator(normalizar_email)]
    password: Annotated[
        SecretStr,
        Field(min_length=8, description="Mínimo 8 caracteres"),
    ]


class UsuarioRegistroResponse(BaseModel):
    id: int


class UsuarioPerfilUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
        AfterValidator(rechazar_caracter_nulo),
    ]


class UsuarioAdminItem(BaseModel):
    id: int
    nombre: str
    email: str
    rol_id: int
    rol: str
    activo: bool
    created_at: datetime


class UsuarioAdminEstadoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activo: StrictBool


class UsuarioAdminEstadoResponse(BaseModel):
    id: int
    activo: bool
    updated_at: datetime


class UsuarioPerfilResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    created_at: datetime
