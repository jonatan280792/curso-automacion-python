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
    validar: Callable[[tuple[int, int], tuple[int, int]], bool] | None = None,
    log_estado_cada: float = 0.0,
    lecturas_iguales_abort: int = 0,
    max_rechazos_invalidos: int = 0,
) -> tuple[int, int] | None:
    """
    Tras un arrastre, relee OCR hasta que las coords cambian y se mantienen estables.
    Con Phone Link el mapa tarda: primero puede verse borroso o seguir el número viejo.
    """
    if pausa_inicial > 0:
        time.sleep(pausa_inicial)

    inicio = time.monotonic()
    ultimo_log_estado = inicio
    candidato: tuple[int, int] | None = None
    aciertos = 0
    iguales = 0
    rechazos_invalidos = 0
    necesarias = max(1, lecturas_estables)

    def encaja_con_paso(pos: tuple[int, int]) -> bool:
        return validar is None or validar(posicion_anterior, pos)

    def aceptar(pos: tuple[int, int]) -> tuple[int, int] | None:
        if not encaja_con_paso(pos):
            if log:
                log(f"  Lectura {pos[0]} , {pos[1]} no encaja con el paso — sigo esperando…")
            return None
        if log:
            log(f"  ✓ Coordenadas: {pos[0]} , {pos[1]}")
        return pos

    while time.monotonic() - inicio < max_espera:
        ahora = time.monotonic()
        if (
            log
            and log_estado_cada > 0
            and ahora - ultimo_log_estado >= log_estado_cada
        ):
            actual_dbg = leer_coords()
            if actual_dbg is not None:
                log(f"  Sigo leyendo {actual_dbg[0]} , {actual_dbg[1]}…")
            else:
                log("  Sigo leyendo (OCR sin resultado)…")
            ultimo_log_estado = ahora

        actual = leer_coords()

        if actual is None:
            candidato = None
            aciertos = 0
            iguales = 0
            time.sleep(intervalo)
            continue

        if actual == posicion_anterior:
            candidato = None
            aciertos = 0
            iguales += 1
            if lecturas_iguales_abort > 0 and iguales >= lecturas_iguales_abort:
                return None
            time.sleep(intervalo)
            continue

        iguales = 0

        if not encaja_con_paso(actual):
            rechazos_invalidos += 1
            if log and rechazos_invalidos == 1:
                log(f"  Lectura {actual[0]} , {actual[1]} no encaja — sigo esperando…")
            if max_rechazos_invalidos > 0 and rechazos_invalidos >= max_rechazos_invalidos:
                return None
            time.sleep(intervalo)
            continue

        rechazos_invalidos = 0
        if actual == candidato:
            aciertos += 1
        else:
            candidato = actual
            aciertos = 1
            if log:
                log(f"  Detectado {actual[0]} , {actual[1]} — confirmando…")

        if aciertos >= necesarias and candidato is not None:
            if pausa_confirmacion > 0:
                if log:
                    log(f"  Esperando mapa ({pausa_confirmacion:g} s)…")
                time.sleep(pausa_confirmacion)
                confirmada = leer_coords()
                if confirmada == candidato:
                    aceptada = aceptar(candidato)
                    if aceptada is not None:
                        return aceptada
                if candidato and encaja_con_paso(candidato) and (
                    confirmada is None or not encaja_con_paso(confirmada)
                ):
                    aceptada = aceptar(candidato)
                    if aceptada is not None:
                        return aceptada
                candidato = None
                aciertos = 0
                if log:
                    log("  Aún cargando — sigo leyendo…")
            else:
                aceptada = aceptar(candidato)
                if aceptada is not None:
                    return aceptada
                candidato = None
                aciertos = 0

        time.sleep(intervalo)

    if log:
        log(
            f"  ✗ Sin cambio estable tras {max_espera:g} s "
            f"(seguían {posicion_anterior[0]} , {posicion_anterior[1]})."
        )
    return None
