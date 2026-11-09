from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, EmailStr, SecretStr

from backend.schemas.usuarios import normalizar_email


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, BeforeValidator(normalizar_email)]
    password: SecretStr


class TokenAccesoResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
