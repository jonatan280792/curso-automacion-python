"""Lectura fiable de posición: votación, preflight y lector rápido para la ruta."""

from __future__ import annotations

import os
import time
from collections import Counter
from collections.abc import Callable
from types import ModuleType

from common.lector_coordenadas import (
    capturar_recorte_ocr,
    extraer_coordenadas,
    leer_texto,
    tesseract_instalado,
)


def aplicar_zona_ocr(config: ModuleType, rect: tuple[int, int, int, int]) -> None:
    config.OCR_IZQUIERDA, config.OCR_SUPERIOR, config.OCR_ANCHO, config.OCR_ALTO = rect


def leer_una_lectura(
    config: ModuleType,
    *,
    guardar_recorte: bool = False,
    log_debug: Callable[[str], None] | None = None,
) -> tuple[int, int] | None:
    if not tesseract_instalado(config):
        return None
    ruta = None
    if guardar_recorte and getattr(config, "GUARDAR_RECORTE_OCR", False):
        ruta = os.path.join(config.CARPETA_SALIDA, "recorte_coordenadas.png")
    img = capturar_recorte_ocr(config, ruta)
    if img is None:
        return None
    texto = leer_texto(config, img)
    if log_debug:
        log_debug(f"OCR: {texto!r}")
    return extraer_coordenadas(texto)


def leer_con_votacion(
    config: ModuleType,
    *,
    log: Callable[[str], None] | None = None,
    log_debug: Callable[[str], None] | None = None,
    validar_coords: Callable[[tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    """Tres lecturas; acepta si al menos dos coinciden."""
    if not tesseract_instalado(config):
        return None

    n = int(getattr(config, "OCR_VOTOS_LECTURAS", 3))
    minimo = int(getattr(config, "OCR_VOTOS_MINIMO", 2))
    pausa = float(getattr(config, "OCR_VOTOS_INTERVALO", 0.25))
    votos: list[tuple[int, int]] = []

    for i in range(n):
        if i:
            time.sleep(pausa)
        coords = leer_una_lectura(config, guardar_recorte=(i == n - 1), log_debug=log_debug)
        if coords is None:
            if log:
                log(f"  Lectura {i + 1}/{n}: sin resultado")
            continue
        votos.append(coords)
        if log:
            log(f"  Lectura {i + 1}/{n}: {coords[0]} , {coords[1]}")

    if not votos:
        return None

    mejor, cuenta = Counter(votos).most_common(1)[0]
    if cuenta < minimo:
        if log:
            log(f"  Lecturas no coinciden ({cuenta}/{minimo}) — revisa la zona OCR.")
        return None

    if validar_coords is not None and not validar_coords(mejor):
        if log:
            log(f"  {mejor[0]} , {mejor[1]} no es una posición válida.")
        return None

    return mejor


def ejecutar_preflight(
    config: ModuleType,
    *,
    log: Callable[[str], None] | None = None,
    log_debug: Callable[[str], None] | None = None,
    validar_coords: Callable[[tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    if not getattr(config, "OCR_PREFLIGHT_ACTIVO", False):
        return leer_con_votacion(
            config, log=log, log_debug=log_debug, validar_coords=validar_coords
        )
    if log:
        log(f"Comprobando zona OCR ({getattr(config, 'OCR_VOTOS_LECTURAS', 3)} lecturas)…")
    coords = leer_con_votacion(
        config, log=log, log_debug=log_debug, validar_coords=validar_coords
    )
    if log:
        if coords:
            log(f"✓ Posición estable: {coords[0]} , {coords[1]}")
        else:
            log("✗ Zona OCR no fiable — revisa output/recorte_coordenadas.png")
    return coords


def crear_lector_rapido(
    config: ModuleType,
    log_debug: Callable[[str], None] | None = None,
) -> Callable[[], tuple[int, int] | None]:
    return lambda: leer_una_lectura(config, log_debug=log_debug)
