"""Esperar cambio de coordenadas tras un arrastre (OCR estable — Phone Link)."""

from __future__ import annotations

import time
from collections.abc import Callable


def esperar_cambio_coordenadas(
    posicion_anterior: tuple[int, int],
    leer_coords: Callable[[], tuple[int, int] | None],
    *,
    log: Callable[[str], None] | None = None,
    pausa_inicial: float,
    intervalo: float,
    max_espera: float,
    lecturas_estables: int = 2,
    pausa_confirmacion: float = 1.0,
) -> tuple[int, int] | None:
    """
    Tras un arrastre, relee OCR hasta que las coords cambian y se mantienen estables.
    Con Phone Link el mapa tarda: primero puede verse borroso o seguir el número viejo.
    """
    if pausa_inicial > 0:
        time.sleep(pausa_inicial)

    inicio = time.monotonic()
    candidato: tuple[int, int] | None = None
    aciertos = 0
    necesarias = max(1, lecturas_estables)

    while time.monotonic() - inicio < max_espera:
        actual = leer_coords()

        if actual is None:
            candidato = None
            aciertos = 0
            time.sleep(intervalo)
            continue

        if actual == posicion_anterior:
            candidato = None
            aciertos = 0
            time.sleep(intervalo)
            continue

        if actual == candidato:
            aciertos += 1
        else:
            candidato = actual
            aciertos = 1
            if log:
                log(f"  Detectado {actual[0]} , {actual[1]} — confirmando…")

        if aciertos >= necesarias:
            if pausa_confirmacion > 0:
                if log:
                    log(f"  Esperando mapa ({pausa_confirmacion:g} s)…")
                time.sleep(pausa_confirmacion)
                confirmada = leer_coords()
                if confirmada == candidato:
                    if log:
                        log(f"  ✓ Coordenadas: {candidato[0]} , {candidato[1]}")
                    return candidato
                candidato = None
                aciertos = 0
                if log:
                    log("  Aún cargando — sigo leyendo…")
            else:
                if log:
                    log(f"  ✓ Coordenadas: {candidato[0]} , {candidato[1]}")
                return candidato

        time.sleep(intervalo)

    if log:
        log(
            f"  ✗ Sin cambio estable tras {max_espera:g} s "
            f"(seguían {posicion_anterior[0]} , {posicion_anterior[1]})."
        )
    return None
