"""Arrastre del mapa: centro → click sostenido → arrastre lento (pydirectinput)."""

from __future__ import annotations

import time

import pydirectinput as mouse

# Español (módulo 5) e inglés (módulo 6) → up/down/left/right
_DIR = {
    "arriba": "up",
    "abajo": "down",
    "izquierda": "left",
    "derecha": "right",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
}


def arrastrar_mapa(
    cx: int,
    cy: int,
    direccion: str,
    *,
    pixeles: int,
    duracion: float,
    pausa_posicionar: float = 0.3,
    pausa_agarrar: float = 0.2,
) -> None:
    """Arrastra el mapa desde (cx, cy) hacia el lado opuesto al movimiento."""
    d = _DIR[direccion.strip().lower()]
    px = int(pixeles)

    if d == "up":
        dx, dy = cx, cy + px
    elif d == "down":
        dx, dy = cx, cy - px
    elif d == "left":
        dx, dy = cx + px, cy
    else:
        dx, dy = cx - px, cy

    mouse.PAUSE = 0
    mouse.moveTo(cx, cy)
    time.sleep(pausa_posicionar)
    mouse.mouseDown()
    time.sleep(pausa_agarrar)

    pasos = max(12, int(duracion * 25))
    for i in range(1, pasos + 1):
        t = i / pasos
        mouse.moveTo(int(cx + (dx - cx) * t), int(cy + (dy - cy) * t))
        time.sleep(duracion / pasos)

    mouse.mouseUp()
