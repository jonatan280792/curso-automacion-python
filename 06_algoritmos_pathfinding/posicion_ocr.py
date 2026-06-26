"""Re-export posición OCR — implementación en common.posicion_ocr."""

from __future__ import annotations

from collections.abc import Callable

import config
from common.posicion_ocr import (
    aplicar_zona_ocr as _aplicar_zona,
    crear_lector_rapido as _crear_lector,
    ejecutar_preflight as _preflight,
    leer_con_votacion as _leer_votacion,
    leer_una_lectura as _leer_una,
)


def _validar_grafo_si_activo() -> Callable[[tuple[int, int]], bool] | None:
    if not getattr(config, "OCR_VALIDAR_EN_GRAFO", True):
        return None
    from buscador_rutas import BuscadorRutas

    grafo: set[tuple[int, int]] | None = None

    def validar(pos: tuple[int, int]) -> bool:
        nonlocal grafo
        if grafo is None:
            grafo = BuscadorRutas.cargar_grafo()
        return pos in grafo

    return validar


def aplicar_zona_ocr(rect: tuple[int, int, int, int]) -> None:
    _aplicar_zona(config, rect)


def leer_una_lectura(
    *,
    guardar_recorte: bool = False,
    log_debug: Callable[[str], None] | None = None,
) -> tuple[int, int] | None:
    return _leer_una(config, guardar_recorte=guardar_recorte, log_debug=log_debug)


def leer_con_votacion(
    *,
    log: Callable[[str], None] | None = None,
    log_debug: Callable[[str], None] | None = None,
    validar_en_grafo: bool = False,
) -> tuple[int, int] | None:
    validar = _validar_grafo_si_activo() if validar_en_grafo else None
    return _leer_votacion(
        config,
        log=log,
        log_debug=log_debug,
        validar_coords=validar,
    )


def ejecutar_preflight(
    *,
    log: Callable[[str], None] | None = None,
    log_debug: Callable[[str], None] | None = None,
) -> tuple[int, int] | None:
    return _preflight(
        config,
        log=log,
        log_debug=log_debug,
        validar_coords=_validar_grafo_si_activo(),
    )


def crear_lector_rapido(
    log_debug: Callable[[str], None] | None = None,
) -> Callable[[], tuple[int, int] | None]:
    return _crear_lector(config, log_debug=log_debug)


__all__ = [
    "aplicar_zona_ocr",
    "crear_lector_rapido",
    "ejecutar_preflight",
    "leer_con_votacion",
    "leer_una_lectura",
]
