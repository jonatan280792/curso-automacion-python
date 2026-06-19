#!/usr/bin/env python3
"""Leer coordenadas del mapa (igual que módulo 4)."""

from __future__ import annotations

import os
import re

import pytesseract
from PIL import Image, ImageOps

import config
from common.zona_pantalla import capturar_pantalla_en_zona


def _configurar_tesseract() -> None:
    ruta = getattr(config, "RUTA_TESSERACT", None)
    if ruta and os.path.isfile(ruta):
        pytesseract.pytesseract.tesseract_cmd = ruta


def recorte_ocr_en_pantalla() -> tuple[int, int, int, int] | None:
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


def capturar_recorte_ocr(ruta_guardar: str | None = None) -> Image.Image | None:
    rect = recorte_ocr_en_pantalla()
    if rect is None:
        return None
    izq, sup, ancho, alto = rect
    img = capturar_pantalla_en_zona(izq, sup, ancho, alto)
    if ruta_guardar:
        os.makedirs(os.path.dirname(ruta_guardar) or ".", exist_ok=True)
        img.save(ruta_guardar)
    return img


def preparar_para_ocr(img: Image.Image) -> Image.Image:
    gris = ImageOps.grayscale(img)
    gris = ImageOps.autocontrast(gris)
    gris = ImageOps.invert(gris)
    w, h = gris.size
    nw = max(w * 3, 120)
    nh = max(h * 3, 40)
    gris = gris.resize((nw, nh), Image.Resampling.LANCZOS)
    return gris.point(lambda p: 255 if p > 130 else 0)


def tesseract_instalado() -> bool:
    try:
        _configurar_tesseract()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def leer_texto(img: Image.Image) -> str:
    _configurar_tesseract()
    lista = preparar_para_ocr(img)
    texto = pytesseract.image_to_string(
        lista,
        config=config.TESSERACT_CONFIG,
        timeout=5,
    )
    return " ".join(texto.split())


def extraer_coordenadas(texto: str) -> tuple[int, int] | None:
    if not texto:
        return None
    par = re.search(r"(-?\d+)\s*,\s*(-?\d+)", texto)
    if par:
        return int(par.group(1)), int(par.group(2))
    numeros = re.findall(r"-?\d+", texto)
    if len(numeros) >= 2:
        return int(numeros[0]), int(numeros[1])
    return None
