"""
Paso de navegación: arrastre + espera OCR (base compartida módulos 5, 6+).

Phone Link / lag: lecturas estables, confirmación, reintentos y re-arrastre.
Delega en common.navegacion_mapa (misma lógica que el módulo 6).
"""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType
from typing import Any

from common.navegacion_mapa import (
    arrastrar_mapa as _arrastrar_mapa,
    ejecutar_paso_arrastre as _ejecutar_paso,
    esperar_cambio_coordenadas as _esperar_cambio,
)


def esperar_cambio_coordenadas(
    posicion_anterior: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    config: ModuleType,
    *,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    return _esperar_cambio(
        posicion_anterior,
        leer_coords,
        config,
        log=log,
        validar=validar,
    )


def ejecutar_paso_arrastre(
    direccion: str,
    posicion_actual: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    arrastrar_fn: Callable[..., None],
    config: ModuleType,
    *,
    gestor: Any = None,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
    **kwargs_arrastre: Any,
) -> tuple[int, int] | None:
    """Compatibilidad módulo 5: arrastrar_fn se ignora (usa navegacion_mapa)."""
    del arrastrar_fn, kwargs_arrastre
    return _ejecutar_paso(
        config,
        direccion,
        posicion_actual,
        leer_coords,
        gestor=gestor,
        log=log,
        validar=validar,
    )


def arrastrar_mapa_compat(
    config: ModuleType,
    direccion: str,
    *,
    gestor: Any = None,
    log: Callable[[str], None] | None = None,
) -> None:
    _arrastrar_mapa(config, direccion, gestor=gestor, log=log)
