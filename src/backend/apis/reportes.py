from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from pydantic import ValidationError
from python_multipart.exceptions import MultipartParseError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.requests import ClientDisconnect

from backend.apis.dependencies import requiere_rol
from backend.core.exceptions import (
    EstadoReporteNoConfiguradoError,
    ReporteConflictoError,
    ReporteConsultaInvalidaError,
    ReporteConsultaNoConfiguradaError,
    ReporteDatosInvalidosError,
    ReporteFotografiaAlmacenamientoError,
    ReporteFotografiaDemasiadoGrandeError,
    ReporteFotografiaInvalidaError,
    ReporteFotografiaNoEncontradaError,
    ReporteNoAutorizadoError,
    ReporteReferenciaInvalidaError,
)
from backend.core.fotografias import MAX_BYTES_FOTOGRAFIA
from backend.schemas.reportes import (
    ReporteDetalleItem,
    ReporteMioItem,
    ReporteRegistroRequest,
    ReporteRegistroResponse,
)
from backend.schemas.usuarios import UsuarioPerfilResponse
from backend.services import reportes as servicio

router = APIRouter(prefix="/api/reportes", tags=["reportes"])
_MAX_CUERPO_MULTIPART = MAX_BYTES_FOTOGRAFIA + 64 * 1024


class _CargaDemasiadoGrande(MultiPartException):
    pass


async def _multipart_acotado(request: Request):
    recibidos = 0
    try:
        async for bloque in request.stream():
            recibidos += len(bloque)
            if recibidos > _MAX_CUERPO_MULTIPART:
                raise _CargaDemasiadoGrande("La solicitud supera el tamaño permitido")
            yield bloque
    except ClientDisconnect as error:
        raise MultiPartException("Carga interrumpida") from error


@router.post(
    "",
    response_model=ReporteRegistroResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        409: {"description": "No se pudo registrar el reporte"},
        422: {"description": "Datos del reporte inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def registrar_reporte(
    datos: ReporteRegistroRequest,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano")),
) -> ReporteRegistroResponse:
    """Register a report for the authenticated citizen."""
    return _registrar(usuario.id, datos)


def _registrar(
    usuario_id: int, datos: ReporteRegistroRequest, contenido: bytes | None = None
) -> ReporteRegistroResponse:
    try:
        if contenido is None:
            reporte_id = servicio.registrar_reporte(usuario_id, datos)
        else:
            reporte_id = servicio.registrar_con_fotografia(usuario_id, datos, contenido)
    except ReporteReferenciaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El distrito o el tipo de reporte no existe",
        ) from None
    except ReporteDatosInvalidosError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Datos del reporte inválidos",
        ) from None
    except ReporteNoAutorizadoError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado",
        ) from None
    except (EstadoReporteNoConfiguradoError, ReporteFotografiaAlmacenamientoError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None
    except ReporteConflictoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar el reporte",
        ) from None

    return ReporteRegistroResponse(id=reporte_id)


@router.post(
    "/con-fotografia",
    response_model=ReporteRegistroResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        409: {"description": "No se pudo registrar el reporte"},
        413: {"description": "Carga demasiado grande"},
        415: {"description": "Se requiere multipart/form-data"},
        422: {"description": "Datos o fotografía inválidos"},
        500: {"description": "No se pudo registrar el reporte"},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        **ReporteRegistroRequest.model_json_schema(),
                        "properties": {
                            **ReporteRegistroRequest.model_json_schema()["properties"],
                            "fotografia": {"type": "string", "format": "binary"},
                        },
                        "required": [*ReporteRegistroRequest.model_fields, "fotografia"],
                    }
                }
            },
        }
    },
)
async def registrar_con_fotografia(
    request: Request,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano")),
) -> ReporteRegistroResponse:
    tipo = request.headers.get("content-type", "").partition(";")[0].strip().lower()
    if tipo != "multipart/form-data":
        raise HTTPException(415, "Se requiere multipart/form-data")

    try:
        formulario = await MultiPartParser(
            request.headers,
            _multipart_acotado(request),
            max_files=1,
            max_fields=len(ReporteRegistroRequest.model_fields),
            max_part_size=16 * 1024,
        ).parse()
        try:
            campos = dict(formulario)
            fotografia = campos.pop("fotografia", None)
            if not isinstance(fotografia, UploadFile) or len(campos) + 1 != len(
                formulario.multi_items()
            ):
                raise ReporteFotografiaInvalidaError
            datos = ReporteRegistroRequest.model_validate(campos)
            contenido = await fotografia.read(MAX_BYTES_FOTOGRAFIA + 1)
        finally:
            await formulario.close()

        return await run_in_threadpool(_registrar, usuario.id, datos, contenido)
    except (_CargaDemasiadoGrande, ReporteFotografiaDemasiadoGrandeError):
        raise HTTPException(413, "La fotografía o la solicitud supera el tamaño permitido") from None
    except (MultiPartException, MultipartParseError, ValidationError, ReporteFotografiaInvalidaError):
        raise HTTPException(422, "Los datos del reporte o la fotografía no son válidos") from None


@router.get(
    "/mios",
    response_model=list[ReporteMioItem],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        422: {"description": "Parámetros de consulta inválidos"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def listar_mis_reportes(
    limite: Annotated[
        int,
        Query(ge=1, le=100, description="Cantidad máxima de reportes"),
    ] = 20,
    desplazamiento: Annotated[
        int,
        Query(ge=0, description="Cantidad de reportes a omitir"),
    ] = 0,
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano")),
) -> list[ReporteMioItem]:
    """Return only the authenticated citizen's reports."""
    try:
        return servicio.listar_mios(usuario.id, limite, desplazamiento)
    except ReporteConsultaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parámetros de consulta inválidos",
        ) from None
    except ReporteConsultaNoConfiguradaError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None


@router.get(
    "/{reporte_id}",
    response_model=ReporteDetalleItem,
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        404: {"description": "Reporte no encontrado"},
        422: {"description": "Identificador de reporte inválido"},
        500: {"description": "Error de configuración del servidor"},
    },
)
def obtener_reporte(
    reporte_id: Annotated[
        int,
        Path(gt=0, description="Identificador del reporte"),
    ],
    usuario: UsuarioPerfilResponse = Depends(
        requiere_rol("Ciudadano", "Administrador")
    ),
) -> ReporteDetalleItem:
    """Return one report allowed for the authenticated user."""
    try:
        reporte = servicio.obtener_reporte(reporte_id, usuario.id)
    except ReporteConsultaInvalidaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Identificador de reporte inválido",
        ) from None
    except ReporteConsultaNoConfiguradaError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración del servidor",
        ) from None

    if reporte is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporte no encontrado",
        )

    return reporte


@router.get(
    "/{reporte_id}/fotografia",
    response_class=Response,
    responses={
        200: {"content": {"image/jpeg": {}}},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado"},
        404: {"description": "Fotografía no encontrada"},
        500: {"description": "No se pudo leer la fotografía"},
    },
)
def obtener_fotografia(
    reporte_id: Annotated[int, Path(gt=0, description="Identificador del reporte")],
    usuario: UsuarioPerfilResponse = Depends(requiere_rol("Ciudadano", "Administrador")),
) -> Response:
    try:
        contenido = servicio.obtener_fotografia(reporte_id, usuario.id)
    except ReporteFotografiaNoEncontradaError:
        raise HTTPException(404, "Fotografía no encontrada") from None
    except ReporteConsultaInvalidaError:
        raise HTTPException(422, "Identificador de reporte inválido") from None
    except (ReporteConsultaNoConfiguradaError, ReporteFotografiaAlmacenamientoError):
        raise HTTPException(500, "No se pudo leer la fotografía") from None

    return Response(
        contenido,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Cross-Origin-Resource-Policy": "same-site",
        },
    )
