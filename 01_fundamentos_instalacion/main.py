#!/usr/bin/env python3
"""
Modulo 1 (esencial):
1) marcar zona del juego en pantalla
2) encontrar ventana del juego y activarla
3) hacer 4 clics aleatorios dentro de la zona
4) guardar captura de esa misma zona
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
import webbrowser
from pathlib import Path

if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import pyautogui as pg
import pygetwindow as gw

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from common.zona_pantalla import (
    aplicar_zona_en_config,
    calibrar_zona_al_inicio,
    capturar_pantalla_en_zona,
    describir_zona,
)

_OVERLAY = None


def decir(msg: str = "") -> None:
    print(msg)
    if _OVERLAY is not None:
        _OVERLAY.log(msg)


def decir_debug(msg: str) -> None:
    if not getattr(config, "LOG_DEPURACION", False):
        return
    line = f"[DEBUG] {msg}"
    print(line)
    if _OVERLAY is not None:
        _OVERLAY.log(line)


def configurar_entorno() -> None:
    pg.PAUSE = config.PAUSA_ENTRE_ACCIONES
    pg.FAILSAFE = config.SEGURIDAD_ESQUINA
    for carpeta in (config.CARPETA_TEMP, config.CARPETA_IMAGENES, config.CARPETA_SALIDA):
        os.makedirs(carpeta, exist_ok=True)


def _es_fantasma(w) -> bool:
    if getattr(w, "isMinimized", False):
        return False
    return w.left <= config.UMBRAL_FUERA_PANTALLA or w.top <= config.UMBRAL_FUERA_PANTALLA


def _tamano_ok(w, min_ancho: int, min_alto: int) -> bool:
    if w.width < config.VENTANA_DIMINUTA_ANCHO or w.height < config.VENTANA_DIMINUTA_ALTO:
        return False
    return w.width >= min_ancho and w.height >= min_alto


def _recolectar_por_tokens(tokens: tuple[str, ...]) -> list:
    out: list = []
    vistos: set[tuple[str, int, int, int, int]] = set()
    for token in tokens:
        for w in gw.getWindowsWithTitle(token):
            key = (w.title, w.left, w.top, w.width, w.height)
            if key in vistos:
                continue
            vistos.add(key)
            if _es_fantasma(w):
                decir_debug(f"descartada: {w.title!r}")
                continue
            out.append(w)
    return out


def _elegir_por_tamano(todas: list):
    minimizadas = [w for w in todas if getattr(w, "isMinimized", False)]
    if minimizadas:
        return minimizadas[0]

    candidatos: list = []
    for min_ancho, min_alto in (
        (config.VENTANA_MIN_ANCHO, config.VENTANA_MIN_ALTO),
        (config.VENTANA_MIN_ANCHO_RELAX, config.VENTANA_MIN_ALTO_RELAX),
    ):
        candidatos = [w for w in todas if _tamano_ok(w, min_ancho, min_alto)]
        if candidatos:
            decir_debug(f"tamaño ≥{min_ancho}x{min_alto} → {len(candidatos)} ventana(s)")
            break
    if not candidatos:
        return None
    elegida = max(candidatos, key=lambda x: x.width * x.height)
    decir_debug(f"elegida: {elegida.title!r}")
    return elegida


def buscar_ventana_juego():
    prioridad = getattr(config, "TITULOS_VENTANA_PRIORIDAD", ())

    if prioridad:
        todas_prio = _recolectar_por_tokens(prioridad)
        elegida = _elegir_por_tamano(todas_prio)
        if elegida is not None:
            return elegida

    todas = _recolectar_por_tokens(config.TITULOS_VENTANA)
    return _elegir_por_tamano(todas)


def activar_ventana_juego(ventana) -> None:
    if getattr(ventana, "isMinimized", False):
        decir("Restaurando ventana minimizada…")
        ventana.restore()
        time.sleep(0.4)
        nueva = buscar_ventana_juego()
        if nueva is not None:
            ventana = nueva
    ventana.activate()
    time.sleep(0.25)


def iniciar_panel() -> None:
    global _OVERLAY
    if not config.PANEL_ACTIVO:
        return

    from common.overlay import GameLogOverlay

    _OVERLAY = GameLogOverlay(
        rel_x=config.PANEL_POS_X,
        rel_y=config.PANEL_POS_Y,
        rel_w=config.PANEL_ANCHO_FRAC,
        rel_h=config.PANEL_ALTO_FRAC,
    )
    _OVERLAY.start(persist=True)
    time.sleep(0.15)
    _OVERLAY.reposition_on_region(
        config.ZONA_IZQUIERDA,
        config.ZONA_SUPERIOR,
        config.ZONA_ANCHO,
        config.ZONA_ALTO,
    )


def rect_clic_en_zona():
    zi, zs, za, zal = (
        config.ZONA_IZQUIERDA,
        config.ZONA_SUPERIOR,
        config.ZONA_ANCHO,
        config.ZONA_ALTO,
    )
    izq = zi + int(za * config.CLIC_MARGEN_IZQ)
    der = zi + int(za * config.CLIC_MARGEN_DER)
    arr = zs + int(zal * config.CLIC_MARGEN_ARRIBA)
    abj = zs + int(zal * config.CLIC_MARGEN_ABAJO)
    if der <= izq:
        der = izq + 40
    if abj <= arr:
        abj = arr + 40
    decir_debug(f"clics: ({izq},{arr}) — ({der},{abj})")
    return izq, der, arr, abj


def demo_clics_aleatorios(total: int = 4) -> None:
    izq, der, arr, abj = rect_clic_en_zona()

    decir(f"Haré {total} clics en tu zona…")
    for i in range(1, total + 1):
        x = random.randint(izq, der)
        y = random.randint(arr, abj)
        mover = round(random.uniform(0.45, 0.9), 2)
        espera = round(random.uniform(0.35, 0.8), 2)
        decir(f"  Clic {i} de {total}")
        decir_debug(f"  → ({x}, {y})")
        pg.moveTo(x, y, duration=mover)
        pg.click()
        time.sleep(espera)


def _panel_discreto(discreto: bool) -> None:
    if _OVERLAY is None:
        return
    _OVERLAY.set_alpha(0.03 if discreto else 0.88)


def guardar_captura() -> str:
    time.sleep(config.PAUSA_ANTES_CAPTURA)
    ruta = os.path.join(config.CARPETA_SALIDA, config.ARCHIVO_CAPTURA)
    izq, sup = config.ZONA_IZQUIERDA, config.ZONA_SUPERIOR
    ancho, alto = config.ZONA_ANCHO, config.ZONA_ALTO

    decir("Guardando foto…")
    decir_debug(describir_zona((izq, sup, ancho, alto)))

    _panel_discreto(True)
    try:
        img = capturar_pantalla_en_zona(izq, sup, ancho, alto)
    finally:
        _panel_discreto(False)

    img.save(ruta)
    decir(f"✓ Foto guardada: {config.ARCHIVO_CAPTURA}")
    decir_debug(os.path.abspath(ruta))
    return ruta


def abrir_carpeta_salida(ruta: str) -> None:
    if not getattr(config, "ABRIR_CARPETA_AL_FINAL", False):
        return
    carpeta = os.path.dirname(os.path.abspath(ruta))
    try:
        if sys.platform == "win32":
            os.startfile(carpeta)  # type: ignore[attr-defined]
        else:
            webbrowser.open(f"file://{carpeta}")
    except Exception as e:
        decir_debug(f"no pude abrir carpeta: {e}")


def procesar_argumentos() -> None:
    parser = argparse.ArgumentParser(description="Modulo 1 esencial")
    parser.add_argument("--overlay", action="store_true", help="Panel flotante de mensajes")
    parser.add_argument("--debug-temp", action="store_true", help="Detalles técnicos en consola")
    args = parser.parse_args()
    if args.overlay:
        config.PANEL_ACTIVO = True
    if args.debug_temp:
        config.LOG_DEPURACION = True


def main() -> int:
    procesar_argumentos()
    configurar_entorno()

    ruta_zona = Path(__file__).resolve().parent / config.RUTA_ZONA_JSON

    pausa_inicio = float(getattr(config, "PAUSA_ANTES_CALIBRAR_ZONA", 0))
    if pausa_inicio > 0:
        seg = int(pausa_inicio) if pausa_inicio == int(pausa_inicio) else pausa_inicio
        print(f"En {seg} s marca la zona del juego — minimiza el IDE y deja Dofus visible…")
        time.sleep(pausa_inicio)

    zona = calibrar_zona_al_inicio(ruta_zona)
    if zona is None:
        print("Cancelado. Vuelve a ejecutar cuando quieras.")
        return 0

    aplicar_zona_en_config(config, zona)
    decir_debug(describir_zona(zona))

    n = getattr(config, "SEGUNDOS_CUENTA_ATRAS", 3)
    decir("Prepárate…")
    for i in range(n, 0, -1):
        decir(f"  {i}…")
        time.sleep(1)

    ventana = buscar_ventana_juego()
    if ventana is None:
        decir("No encontré el juego abierto.")
        decir("Abre Dofus Touch y vuelve a ejecutar el programa.")
        decir_debug("revisa TITULOS_VENTANA en config.py")
        return 1

    decir("✓ Juego encontrado")
    decir_debug(f"ventana: {ventana.title!r}")
    activar_ventana_juego(ventana)
    decir("✓ Juego al frente")

    iniciar_panel()
    demo_clics_aleatorios(total=4)
    ruta = guardar_captura()
    abrir_carpeta_salida(ruta)

    decir("Módulo 1 completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
