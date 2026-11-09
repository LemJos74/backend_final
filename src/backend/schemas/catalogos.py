from pydantic import BaseModel


class Distrito(BaseModel):
    id: int
    nombre: str


class TipoReporte(BaseModel):
    id: int
    nombre: str
    descripcion: str | None


class EstadoReporte(BaseModel):
    id: int
    nombre: str
