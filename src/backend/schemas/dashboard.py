from pydantic import BaseModel


class DashboardGrupoItem(BaseModel):
    """Conteo de reportes para un valor de una distribucion."""

    id: int
    nombre: str
    total: int


class DashboardResponse(BaseModel):
    """Indicadores generales de reportes para el panel administrativo."""

    total_reportes: int
    por_estado: list[DashboardGrupoItem]
    por_distrito: list[DashboardGrupoItem]
    por_categoria: list[DashboardGrupoItem]
