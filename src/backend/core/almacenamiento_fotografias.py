"""Almacenamiento desacoplado de las fotografías de reportes.

La interfaz ``AlmacenFotografias`` permite sustituir el proveedor local por
otro, por ejemplo Supabase Storage, sin cambiar la lógica de negocio. La base
de datos solo guarda la clave relativa devuelta por ``guardar``.

Consistencia: el servicio guarda primero la imagen y después registra el
reporte. Si la operación SQL falla, el servicio elimina la imagen. Una caída
inesperada del proceso entre ambos pasos puede dejar un archivo huérfano; no
se ejecuta ninguna limpieza automática.
"""

import logging
import os
import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

from backend.core.config import settings
from backend.core.exceptions import (
    ReporteFotografiaAlmacenamientoError,
    ReporteFotografiaNoEncontradaError,
)

logger = logging.getLogger(__name__)

_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
_EXTENSIONES_PERMITIDAS = frozenset({"jpg"})


class AlmacenFotografias(ABC):
    """Contrato mínimo para guardar, leer y eliminar fotografías."""

    @abstractmethod
    def guardar(self, contenido: bytes, extension: str = "jpg") -> str:
        """Store the content and return a relative, non-guessable key."""

    @abstractmethod
    def leer(self, clave: str) -> bytes:
        """Return the content associated with a relative key."""

    @abstractmethod
    def eliminar(self, clave: str) -> None:
        """Delete the content associated with a relative key, if present."""


class AlmacenLocalFotografias(AlmacenFotografias):
    """Local filesystem provider used by the initial implementation."""

    def __init__(self, directorio: str | Path) -> None:
        ruta = Path(directorio)
        if not ruta.is_absolute():
            ruta = _RAIZ_PROYECTO / ruta
        self._directorio = ruta.resolve()

    def guardar(self, contenido: bytes, extension: str = "jpg") -> str:
        if extension not in _EXTENSIONES_PERMITIDAS:
            raise ValueError("Extensión de fotografía no permitida")

        clave = f"{uuid4().hex}.{extension}"
        temporal: str | None = None

        try:
            self._directorio.mkdir(parents=True, exist_ok=True)
            destino = self._ruta_segura(clave)
            descriptor, temporal = tempfile.mkstemp(
                dir=self._directorio,
                prefix=".tmp-",
                suffix=".part",
            )
            with os.fdopen(descriptor, "wb") as archivo:
                archivo.write(contenido)
                archivo.flush()
                os.fsync(archivo.fileno())

            os.replace(temporal, destino)
            temporal = None
            return clave
        except (OSError, ValueError) as error:
            raise ReporteFotografiaAlmacenamientoError from error
        finally:
            if temporal is not None:
                try:
                    Path(temporal).unlink(missing_ok=True)
                except OSError:
                    logger.warning(
                        "No se pudo eliminar el archivo temporal de fotografía"
                    )

    def leer(self, clave: str) -> bytes:
        try:
            ruta = self._ruta_segura(clave)
        except ValueError as error:
            raise ReporteFotografiaNoEncontradaError from error

        try:
            return ruta.read_bytes()
        except FileNotFoundError as error:
            raise ReporteFotografiaNoEncontradaError from error
        except OSError as error:
            raise ReporteFotografiaAlmacenamientoError from error

    def eliminar(self, clave: str) -> None:
        try:
            ruta = self._ruta_segura(clave)
        except ValueError:
            logger.warning("Se intentó eliminar una clave de fotografía inválida")
            return

        try:
            ruta.unlink(missing_ok=True)
        except OSError:
            logger.warning("No se pudo eliminar una fotografía almacenada")

    def _ruta_segura(self, clave: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}\.jpg", clave):
            raise ValueError("Clave de fotografía inválida")

        ruta = (self._directorio / clave).resolve()
        if ruta.parent != self._directorio:
            raise ValueError("Clave de fotografía fuera del directorio")
        return ruta


def obtener_almacen() -> AlmacenFotografias:
    """Return the configured provider; only the local one is implemented."""
    return AlmacenLocalFotografias(settings.reportes_fotos_dir)
