from backend.repositories import dashboard as repositorio
from backend.schemas.dashboard import (
    DashboardGrupoItem,
    DashboardResponse,
)


def obtener_dashboard(admin_id: int) -> DashboardResponse:
    """Group the stored function rows into the dashboard response."""
    filas = repositorio.obtener_estadisticas(admin_id)

    total_reportes: int | None = None
    distribuciones: dict[str, list[DashboardGrupoItem]] = {
        "estado": [],
        "distrito": [],
        "categoria": [],
    }

    for fila in filas:
        seccion = fila["seccion"]

        if seccion == "resumen":
            total_reportes = int(fila["total"])
            continue

        if seccion not in distribuciones:
            raise RuntimeError(
                f"Sección de estadísticas desconocida: {seccion}"
            )

        distribuciones[seccion].append(
            DashboardGrupoItem(
                id=int(fila["clave_id"]),
                nombre=fila["clave_nombre"],
                total=int(fila["total"]),
            )
        )

    if total_reportes is None:
        raise RuntimeError(
            "La función de estadísticas no devolvió el resumen"
        )

    return DashboardResponse(
        total_reportes=total_reportes,
        por_estado=distribuciones["estado"],
        por_distrito=distribuciones["distrito"],
        por_categoria=distribuciones["categoria"],
    )
