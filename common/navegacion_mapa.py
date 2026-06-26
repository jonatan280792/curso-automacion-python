"""
Navegación en el mapa: arrastre, espera OCR y abanico en salidas estrechas.
Base compartida módulos 5, 6+.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from types import ModuleType
from typing import Any

from common.arrastre_mapa import arrastrar_mapa as ejecutar_arrastre
from common.espera_coordenadas import esperar_cambio_coordenadas as _esperar_estable

_VECINO = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}


def _cfg(config: ModuleType, nombre: str, default: Any) -> Any:
    return getattr(config, nombre, default)


def centro_zona_juego(config: ModuleType) -> tuple[int, int]:
    return (
        int(config.ZONA_IZQUIERDA + config.ZONA_ANCHO / 2),
        int(config.ZONA_SUPERIOR + config.ZONA_ALTO / 2),
    )


def origenes_arrastre_abanico(
    config: ModuleType,
    direccion: str,
) -> list[tuple[int, int, str]]:
    """Centro + dos esquinas del borde de salida (salidas estrechas)."""
    cx, cy = centro_zona_juego(config)
    izq, sup = int(config.ZONA_IZQUIERDA), int(config.ZONA_SUPERIOR)
    ancho, alto = int(config.ZONA_ANCHO), int(config.ZONA_ALTO)
    centro = (cx, cy, "centro")

    if ancho < 8 or alto < 8 or not _cfg(config, "ARRASTRE_ABANICO_ACTIVO", False):
        return [centro]

    fr = max(0.05, min(0.35, float(_cfg(config, "ARRASTRE_ABANICO_MARGEN_FRACC", 0.15))))
    mx, my = max(8, int(ancho * fr)), max(8, int(alto * fr))
    d = direccion.strip().lower()

    if d == "down":
        y = sup + alto - my
        return [
            centro,
            (izq + mx, y, "borde inferior izquierda"),
            (izq + ancho - mx, y, "borde inferior derecha"),
        ]
    if d == "up":
        y = sup + my
        return [
            centro,
            (izq + mx, y, "borde superior izquierda"),
            (izq + ancho - mx, y, "borde superior derecha"),
        ]
    if d == "left":
        x = izq + mx
        return [
            centro,
            (x, sup + my, "borde izquierdo arriba"),
            (x, sup + alto - my, "borde izquierdo abajo"),
        ]
    if d == "right":
        x = izq + ancho - mx
        return [
            centro,
            (x, sup + my, "borde derecho arriba"),
            (x, sup + alto - my, "borde derecho abajo"),
        ]
    return [centro]


def validar_vecino_paso(
    anterior: tuple[int, int],
    nueva: tuple[int, int],
    direccion: str,
) -> bool:
    delta = _VECINO.get(direccion)
    if not delta:
        return False
    esperada = (anterior[0] + delta[0], anterior[1] + delta[1])
    return nueva == esperada


def _etiqueta_direccion(config: ModuleType, direccion: str) -> str:
    etiquetas = getattr(config, "ETIQUETAS_DIRECCION", None)
    if isinstance(etiquetas, dict):
        return etiquetas.get(direccion, direccion)
    from common.editor_ruta import token_a_etiqueta

    return token_a_etiqueta(direccion)


def arrastrar_mapa(
    config: ModuleType,
    direccion: str,
    *,
    gestor: Any = None,
    log: Callable[[str], None] | None = None,
    origen: tuple[int, int] | None = None,
    etiqueta_origen: str = "centro",
    pausa_previa: bool = True,
) -> None:
    cx, cy = origen or centro_zona_juego(config)
    if gestor is not None:
        gestor.activar_ventana(silencioso=True)
    if pausa_previa and float(_cfg(config, "PAUSA_ANTES_ARRASTRE", 1.0)) > 0:
        pausa = float(_cfg(config, "PAUSA_ANTES_ARRASTRE", 1.0))
        if log:
            log(f"  Preparando arrastre ({pausa:g} s)…")
        time.sleep(pausa)
    if log:
        etiq = _etiqueta_direccion(config, direccion)
        extra = f" (desde {etiqueta_origen})" if etiqueta_origen != "centro" else ""
        log(f"  Movimiento: arrastre hacia {etiq}{extra}")
    ejecutar_arrastre(
        cx,
        cy,
        direccion,
        pixeles=int(_cfg(config, "DRAG_PIXELES", 280)),
        duracion=float(_cfg(config, "DRAG_DURACION", 0.75)),
        pausa_posicionar=float(_cfg(config, "PAUSA_TRAS_POSICIONAR_RATON", 0.3)),
        pausa_agarrar=float(_cfg(config, "PAUSA_TRAS_MOUSE_DOWN", 0.2)),
    )


def esperar_cambio_coordenadas(
    posicion_anterior: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    config: ModuleType,
    *,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
    max_espera: float | None = None,
    lecturas_iguales_abort: int = 0,
) -> tuple[int, int] | None:
    limite = max_espera if max_espera is not None else float(_cfg(config, "OCR_ESPERA_MAXIMA", 45.0))
    max_total = float(_cfg(config, "OCR_ESPERA_MAXIMA", 45.0))
    reintentos = (
        1
        if max_espera is not None and max_espera < max_total
        else max(1, int(_cfg(config, "OCR_REINTENTOS_ESPERA", 2)))
    )

    for intento in range(1, reintentos + 1):
        if intento > 1:
            if log:
                log(f"  Reintento lectura {intento}/{reintentos}…")
            time.sleep(float(_cfg(config, "OCR_PAUSA_ENTRE_REINTENTOS", 2.0)))

        resultado = _esperar_estable(
            posicion_anterior,
            leer_coords,
            log=log,
            pausa_inicial=float(_cfg(config, "PAUSA_MINIMA_TRAS_ARRASTRE", 1.5)),
            intervalo=float(_cfg(config, "OCR_INTERVALO_ESPERA", 0.5)),
            max_espera=limite,
            lecturas_estables=int(_cfg(config, "OCR_LECTURAS_ESTABLES", 2)),
            pausa_confirmacion=float(_cfg(config, "OCR_PAUSA_TRAS_CAMBIO", 1.2)),
            validar=validar,
            log_estado_cada=float(_cfg(config, "OCR_LOG_ESTADO_CADA", 8.0)),
            lecturas_iguales_abort=lecturas_iguales_abort,
            max_rechazos_invalidos=int(_cfg(config, "OCR_LECTURAS_INVALIDAS_ABORT", 0)),
        )
        if resultado is not None:
            return resultado
    return None


def ejecutar_paso_arrastre(
    config: ModuleType,
    direccion: str,
    posicion_actual: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    *,
    gestor: Any = None,
    log: Callable[[str], None] | None = None,
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
) -> tuple[int, int] | None:
    origenes = origenes_arrastre_abanico(config, direccion)
    rondas = max(1, int(_cfg(config, "OCR_REINTENTOS_ARRASTRE", 2)))

    for ronda in range(1, rondas + 1):
        if ronda > 1:
            if log:
                log(f"  Reintento arrastre {ronda}/{rondas}…")
            time.sleep(float(_cfg(config, "OCR_PAUSA_ENTRE_REINTENTOS", 2.0)))

        for idx, (ox, oy, nombre) in enumerate(origenes):
            if idx > 0 and log:
                log(f"  Sin cambio de mapa — probando {nombre}…")
            arrastrar_mapa(
                config,
                direccion,
                gestor=gestor,
                log=log,
                origen=(ox, oy),
                etiqueta_origen=nombre,
                pausa_previa=(idx == 0 and ronda == 1),
            )
            if log:
                log("  Esperando cambio de coordenadas…")

            hay_mas = idx < len(origenes) - 1 and _cfg(config, "ARRASTRE_ABANICO_ACTIVO", False)
            nueva = esperar_cambio_coordenadas(
                posicion_actual,
                leer_coords,
                config,
                log=log,
                validar=validar,
                max_espera=float(_cfg(config, "OCR_ESPERA_SIN_CAMBIO_ABANICO", 5.0))
                if hay_mas
                else None,
                lecturas_iguales_abort=int(_cfg(config, "OCR_LECTURAS_IGUALES_ABANICO", 4))
                if hay_mas
                else 0,
            )
            if nueva is not None:
                return nueva
    return None
