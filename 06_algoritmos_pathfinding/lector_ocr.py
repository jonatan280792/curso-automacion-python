"""Re-export OCR — implementación en common.lector_coordenadas."""

from __future__ import annotations

import config
from common.lector_coordenadas import (
    capturar_recorte_ocr as _capturar,
    extraer_coordenadas,
    leer_texto as _leer_texto,
    tesseract_instalado as _tesseract_instalado,
)


def tesseract_instalado() -> bool:
    return _tesseract_instalado(config)


def capturar_recorte_ocr(ruta_guardar: str | None = None):
    return _capturar(config, ruta_guardar)


def leer_texto(img):
    return _leer_texto(config, img)


__all__ = [
    "capturar_recorte_ocr",
    "extraer_coordenadas",
    "leer_texto",
    "tesseract_instalado",
]
