from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
)


def normalizar_email(valor: Any) -> Any:
    if isinstance(valor, str):
        return valor.strip().lower()
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


class UsuarioPerfilResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    created_at: datetime
