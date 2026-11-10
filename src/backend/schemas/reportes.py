from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_serializer,
    field_validator,
)


class ReporteRegistroRequest(BaseModel):
    """Datos aceptados para registrar un reporte ciudadano."""

    model_config = ConfigDict(extra="forbid")

    distrito_id: Annotated[int, Field(gt=0, description="Distrito del reporte")]
    tipo_id: Annotated[int, Field(gt=0, description="Tipo de reporte")]
    descripcion: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]
    ubicacion: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=250),
    ]
    latitud: Annotated[
        Decimal,
        Field(ge=Decimal("-90"), le=Decimal("90"), description="Latitud WGS84"),
    ]
    longitud: Annotated[
        Decimal,
        Field(ge=Decimal("-180"), le=Decimal("180"), description="Longitud WGS84"),
    ]

    @field_validator("latitud", "longitud")
    @classmethod
    def validar_coordenada(cls, valor: Decimal) -> Decimal:
        """Reject non-finite coordinates and excessive decimal precision."""
        if not valor.is_finite():
            raise ValueError("La coordenada debe ser un número finito")

        exponente = valor.as_tuple().exponent
        if isinstance(exponente, int) and exponente < -8:
            raise ValueError("La coordenada admite como máximo 8 decimales")

        return valor


class ReporteRegistroResponse(BaseModel):
    id: int


class ReporteMioItem(BaseModel):
    id: int
    tipo_id: int
    tipo_nombre: str
    distrito_id: int
    distrito_nombre: str
    estado_id: int
    estado_nombre: str
    descripcion: str
    ubicacion: str
    latitud: Decimal
    longitud: Decimal
    created_at: datetime

    @field_serializer("latitud", "longitud", when_used="json")
    def serializar_coordenada(self, valor: Decimal) -> float:
        """Return coordinates as JSON numbers for map clients."""
        return float(valor)
