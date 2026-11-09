from backend.repositories import catalogos as repositorio
from backend.schemas.catalogos import Distrito, EstadoReporte, TipoReporte


def listar_distritos() -> list[Distrito]:
    return [
        Distrito(id=fila[0], nombre=fila[1])
        for fila in repositorio.listar_distritos()
    ]


def listar_tipos_reporte() -> list[TipoReporte]:
    return [
        TipoReporte(id=fila[0], nombre=fila[1], descripcion=fila[2])
        for fila in repositorio.listar_tipos_reporte()
    ]


def listar_estados_reporte() -> list[EstadoReporte]:
    return [
        EstadoReporte(id=fila[0], nombre=fila[1])
        for fila in repositorio.listar_estados_reporte()
    ]
