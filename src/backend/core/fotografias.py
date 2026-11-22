"""Validación y normalización de las fotografías de reportes.

La imagen recibida nunca se guarda tal como llega: se verifica con Pillow,
se corrige su orientación, se eliminan metadatos y se vuelve a codificar como
JPEG. De este modo el nombre y el MIME declarados por el cliente no influyen
en el tipo real del archivo almacenado.
"""

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from backend.core.exceptions import (
    ReporteFotografiaDemasiadoGrandeError,
    ReporteFotografiaInvalidaError,
)

MAX_BYTES_FOTOGRAFIA = 5 * 1024 * 1024
MAX_LADO_FOTOGRAFIA = 1920
MAX_PIXELES_ENTRADA = 24_000_000
_CALIDADES_JPEG = (85, 75, 65)
_LADOS_REDUCCION = (1600, 1280, 1024, 800)
_FORMATOS_PERMITIDOS = frozenset({"JPEG", "PNG", "WEBP"})


def procesar_fotografia(contenido: bytes) -> bytes:
    """Validate an uploaded image and return a clean JPEG within the limit."""
    if not contenido:
        raise ReporteFotografiaInvalidaError

    if len(contenido) > MAX_BYTES_FOTOGRAFIA:
        raise ReporteFotografiaDemasiadoGrandeError

    try:
        with Image.open(BytesIO(contenido)) as original:
            if original.format not in _FORMATOS_PERMITIDOS:
                raise ReporteFotografiaInvalidaError

            if getattr(original, "is_animated", False):
                raise ReporteFotografiaInvalidaError

            if getattr(original, "n_frames", 1) > 1:
                raise ReporteFotografiaInvalidaError

            ancho, alto = original.size
            if ancho <= 0 or alto <= 0 or ancho * alto > MAX_PIXELES_ENTRADA:
                raise ReporteFotografiaInvalidaError

            # verify() detecta archivos truncados o con estructura inválida.
            original.verify()

        with Image.open(BytesIO(contenido)) as original:
            original.load()
            imagen = ImageOps.exif_transpose(original)
            imagen = _convertir_a_rgb(imagen)
            imagen.thumbnail(
                (MAX_LADO_FOTOGRAFIA, MAX_LADO_FOTOGRAFIA),
                Image.Resampling.LANCZOS,
            )

            # Una imagen nueva descarta EXIF, ICC y cualquier otro metadato.
            limpia = Image.new("RGB", imagen.size)
            limpia.paste(imagen)

            for calidad in _CALIDADES_JPEG:
                salida = _codificar_jpeg(limpia, calidad)
                if len(salida) <= MAX_BYTES_FOTOGRAFIA:
                    return salida

            for lado in _LADOS_REDUCCION:
                reducida = limpia.copy()
                reducida.thumbnail(
                    (lado, lado),
                    Image.Resampling.LANCZOS,
                )
                salida = _codificar_jpeg(reducida, 75)
                if len(salida) <= MAX_BYTES_FOTOGRAFIA:
                    return salida

            raise ReporteFotografiaInvalidaError
    except ReporteFotografiaInvalidaError:
        raise
    except ReporteFotografiaDemasiadoGrandeError:
        raise
    except (
        Image.DecompressionBombError,
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        ValueError,
    ) as error:
        raise ReporteFotografiaInvalidaError from error


def _convertir_a_rgb(imagen: Image.Image) -> Image.Image:
    """Flatten transparency over white and return an RGB image."""
    if imagen.mode in ("RGBA", "LA") or (
        imagen.mode == "P" and "transparency" in imagen.info
    ):
        con_alpha = imagen.convert("RGBA")
        fondo = Image.new("RGB", con_alpha.size, (255, 255, 255))
        fondo.paste(con_alpha, mask=con_alpha.getchannel("A"))
        return fondo

    return imagen.convert("RGB")


def _codificar_jpeg(imagen: Image.Image, calidad: int) -> bytes:
    salida = BytesIO()
    imagen.save(
        salida,
        format="JPEG",
        quality=calidad,
        optimize=True,
        progressive=True,
    )
    return salida.getvalue()
