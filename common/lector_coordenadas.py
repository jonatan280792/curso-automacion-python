"""Captura y OCR de coordenadas del mapa (Tesseract + zona OCR)."""

from __future__ import annotations

import os
import re
from types import ModuleType

import pytesseract
from PIL import Image, ImageOps

from common.zona_pantalla import capturar_pantalla_en_zona


def _tesseract_listo(config: ModuleType) -> None:
    ruta = getattr(config, "RUTA_TESSERACT", None)
    if ruta and os.path.isfile(ruta):
        pytesseract.pytesseract.tesseract_cmd = ruta


def tesseract_instalado(config: ModuleType) -> bool:
    try:
        _tesseract_listo(config)
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def recorte_ocr_en_pantalla(config: ModuleType) -> tuple[int, int, int, int] | None:
    ancho = int(config.OCR_ANCHO)
    alto = int(config.OCR_ALTO)
    if ancho < 4 or alto < 4:
        return None
    return (
        int(config.OCR_IZQUIERDA),
        int(config.OCR_SUPERIOR),
        ancho,
        alto,
    )


def capturar_recorte_ocr(
    config: ModuleType,
    ruta_guardar: str | None = None,
) -> Image.Image | None:
    rect = recorte_ocr_en_pantalla(config)
    if rect is None:
        return None
    izq, sup, ancho, alto = rect
    img = capturar_pantalla_en_zona(izq, sup, ancho, alto)
    if ruta_guardar:
        os.makedirs(os.path.dirname(ruta_guardar) or ".", exist_ok=True)
        img.save(ruta_guardar)
    return img


def preparar_para_ocr(
    img: Image.Image,
    *,
    invertir: bool = True,
    umbral: int = 130,
) -> Image.Image:
    gris = ImageOps.grayscale(img)
    gris = ImageOps.autocontrast(gris)
    if invertir:
        gris = ImageOps.invert(gris)
    w, h = gris.size
    gris = gris.resize((max(w * 3, 120), max(h * 3, 40)), Image.Resampling.LANCZOS)
    return gris.point(lambda p: 255 if p > umbral else 0)


def extraer_coordenadas(texto: str) -> tuple[int, int] | None:
    if not texto:
        return None
    par = re.search(r"(-?\d+)\s*,\s*(-?\d+)", texto)
    if par:
        return int(par.group(1)), int(par.group(2))
    nums = re.findall(r"-?\d+", texto)
    return (int(nums[0]), int(nums[1])) if len(nums) >= 2 else None


def leer_texto(config: ModuleType, img: Image.Image) -> str:
    """Prueba varias formas de leer la imagen hasta sacar X,Y."""
    _tesseract_listo(config)
    cfgs = (
        getattr(config, "TESSERACT_CONFIG", r"--psm 6 -c tessedit_char_whitelist=-0123456789,"),
        r"--psm 7 -c tessedit_char_whitelist=-0123456789,",
    )
    imgs = (
        preparar_para_ocr(img),
        preparar_para_ocr(img, invertir=False, umbral=100),
        img,
    )
    ultimo = ""
    for lista in imgs:
        for cfg in cfgs:
            try:
                t = pytesseract.image_to_string(lista, config=cfg, timeout=5)
            except Exception:
                continue
            texto = " ".join(t.split())
            if texto:
                ultimo = texto
            if extraer_coordenadas(texto):
                return texto
    return ultimo
