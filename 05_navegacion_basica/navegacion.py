#!/usr/bin/env python3
"""Arrastre del mapa, click y espera por OCR."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pydirectinput as mouse

import config
from common.arrastre_mapa import arrastrar_mapa as ejecutar_arrastre
from common.editor_ruta import token_a_etiqueta
from common.espera_coordenadas import esperar_cambio_coordenadas as _esperar_cambio

if TYPE_CHECKING:
    from window_manager import GestorVentana


def centro_zona_juego() -> tuple[int, int]:
    return (
        int(config.ZONA_IZQUIERDA + config.ZONA_ANCHO / 2),
        int(config.ZONA_SUPERIOR + config.ZONA_ALTO / 2),
    )


def arrastrar_paso(
    direccion: str,
    *,
    gestor: GestorVentana | None = None,
    log: Callable[[str], None] | None = None,
) -> None:
    cx, cy = centro_zona_juego()
    etiqueta = token_a_etiqueta(direccion)

    if gestor is not None:
        gestor.activar_ventana(silencioso=True)

    if config.PAUSA_ANTES_ARRASTRE > 0:
        if log:
            log(f"  Preparando arrastre ({config.PAUSA_ANTES_ARRASTRE:g} s)…")
        time.sleep(config.PAUSA_ANTES_ARRASTRE)

    if log:
        log(f"  Movimiento: arrastre hacia {etiqueta}")

    ejecutar_arrastre(
        cx,
        cy,
        direccion,
        pixeles=config.DRAG_PIXELES,
        duracion=config.DRAG_DURACION,
        pausa_posicionar=config.PAUSA_TRAS_POSICIONAR_RATON,
        pausa_agarrar=config.PAUSA_TRAS_MOUSE_DOWN,
    )


def click_centro_juego(
    *,
    gestor: GestorVentana | None = None,
    log: Callable[[str], None] | None = None,
) -> None:
    cx, cy = centro_zona_juego()

    if gestor is not None:
        gestor.activar_ventana(silencioso=True)

    if log:
        log("  Click en el centro del mapa")

    mouse.PAUSE = 0
    mouse.click(cx, cy)
    time.sleep(config.PAUSA_TRAS_CLICK)


def esperar_cambio_coordenadas(
    posicion_anterior: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    *,
    log: Callable[[str], None] | None = None,
) -> tuple[int, int] | None:
    reintentos = max(1, int(getattr(config, "OCR_REINTENTOS_ESPERA", 1)))

    for intento in range(1, reintentos + 1):
        if intento > 1 and log:
            pausa = float(getattr(config, "OCR_PAUSA_ENTRE_REINTENTOS", 2.0))
            log(f"  Reintento {intento}/{reintentos} (Phone Link puede ir lento)…")
            time.sleep(pausa)

        resultado = _esperar_cambio(
            posicion_anterior,
            leer_coords,
            log=log,
            pausa_inicial=float(config.PAUSA_MINIMA_TRAS_ARRASTRE),
            intervalo=float(config.OCR_INTERVALO_ESPERA),
            max_espera=float(config.OCR_ESPERA_MAXIMA),
            lecturas_estables=int(getattr(config, "OCR_LECTURAS_ESTABLES", 2)),
            pausa_confirmacion=float(getattr(config, "OCR_PAUSA_TRAS_CAMBIO", 1.0)),
        )
        if resultado is not None:
            return resultado

    return None
