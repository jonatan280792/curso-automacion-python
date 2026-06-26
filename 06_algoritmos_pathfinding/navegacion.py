"""Navegación en el mapa — re-export desde common.navegacion_mapa."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import config
from common.navegacion_mapa import (
    arrastrar_mapa as _arrastrar,
    ejecutar_paso_arrastre as _ejecutar_paso,
    esperar_cambio_coordenadas as _esperar,
    origenes_arrastre_abanico as _origenes,
    validar_vecino_paso,
)

if TYPE_CHECKING:
    from window_manager import GestorVentana


def centro_zona_juego() -> tuple[int, int]:
    from common.navegacion_mapa import centro_zona_juego as _centro

    return _centro(config)


def origenes_arrastre_abanico(direccion: str) -> list[tuple[int, int, str]]:
    return _origenes(config, direccion)


def arrastrar_mapa(
    direccion: str,
    *,
    gestor: GestorVentana | None = None,
    log: Callable[[str], None] | None = None,
    origen: tuple[int, int] | None = None,
    etiqueta_origen: str = "centro",
    pausa_previa: bool = True,
) -> None:
    _arrastrar(
        config,
        direccion,
        gestor=gestor,
        log=log,
        origen=origen,
        etiqueta_origen=etiqueta_origen,
        pausa_previa=pausa_previa,
    )


def esperar_cambio_coordenadas(
    posicion_anterior: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    *,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
    max_espera: float | None = None,
    lecturas_iguales_abort: int = 0,
) -> tuple[int, int] | None:
    return _esperar(
        posicion_anterior,
        leer_coords,
        config,
        log=log,
        validar=validar,
        max_espera=max_espera,
        lecturas_iguales_abort=lecturas_iguales_abort,
    )


def ejecutar_paso_arrastre(
    direccion: str,
    posicion_actual: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    *,
    gestor: GestorVentana | None = None,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    return _ejecutar_paso(
        config,
        direccion,
        posicion_actual,
        leer_coords,
        gestor=gestor,
        log=log,
        validar=validar,
    )


__all__ = [
    "arrastrar_mapa",
    "ejecutar_paso_arrastre",
    "esperar_cambio_coordenadas",
    "origenes_arrastre_abanico",
    "validar_vecino_paso",
]
