#!/usr/bin/env python3
"""
Módulo 2:
1) marcar zona del juego (igual que módulo 1)
2) datos de la ventana y coordenadas relativas/absolutas
3) tres fotos recortadas del juego
4) clics de prueba
"""

from __future__ import annotations

import argparse
import os
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

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from common.zona_pantalla import (
    aplicar_zona_en_config,
    calibrar_zona_al_inicio,
    describir_zona,
)
from window_manager import GestorVentana

_OVERLAY = None
_ALPHA_PANEL = 0.88


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
    os.makedirs(config.CARPETA_SALIDA, exist_ok=True)


def iniciar_panel() -> None:
    global _OVERLAY
    if not config.PANEL_ACTIVO:
        return
    if _OVERLAY is not None and _OVERLAY.root is not None:
        return

    from common.overlay import GameLogOverlay

    _OVERLAY = GameLogOverlay(
        title="Módulo 2",
        rel_x=config.PANEL_POS_X,
        rel_y=config.PANEL_POS_Y,
        rel_w=config.PANEL_ANCHO_FRAC,
        rel_h=config.PANEL_ALTO_FRAC,
    )
    _OVERLAY.start(persist=True)
    time.sleep(config.PAUSA_PANEL_LAYOUT)
    _OVERLAY.reposition_on_region(
        config.ZONA_IZQUIERDA,
        config.ZONA_SUPERIOR,
        config.ZONA_ANCHO,
        config.ZONA_ALTO,
    )


def _panel_discreto(discreto: bool) -> None:
    """Baja la opacidad del panel sin cerrarlo (no parpadea)."""
    if _OVERLAY is None:
        return
    _OVERLAY.set_alpha(0.03 if discreto else _ALPHA_PANEL)


def demo_info_ventana(gestor: GestorVentana) -> None:
    decir("Revisando la ventana…")
    gestor.obtener_info_ventana()


def demo_tres_fotos(gestor: GestorVentana) -> None:
    if not gestor.info_ventana:
        return

    decir("Guardando 3 recortes del juego…")
    ancho, alto = gestor.info_ventana["size"]
    regiones = [
        (int(ancho * 0.05), int(alto * 0.05), int(ancho * 0.3), int(alto * 0.25), "zona_superior_izquierda"),
        (int(ancho * 0.35), int(alto * 0.35), int(ancho * 0.3), int(alto * 0.25), "zona_central"),
        (int(ancho * 0.05), int(alto * 0.65), int(ancho * 0.4), int(alto * 0.25), "zona_inferior_izquierda"),
    ]

    _panel_discreto(True)
    try:
        ok = 0
        for x, y, w, h, nombre in regiones:
            ruta = os.path.join(config.CARPETA_SALIDA, f"region_{nombre}.png")
            if gestor.capturar_region_ventana(x, y, w, h, ruta_guardar=ruta):
                ok += 1
            time.sleep(config.PAUSA_ENTRE_REGIONES)
        decir(f"✓ {ok} fotos en la carpeta output")
    finally:
        _panel_discreto(False)


def demo_conversiones(gestor: GestorVentana) -> None:
    decir("Ejemplos pantalla ↔ juego (sin memorizar números)…")

    wobj = gestor.ventana_juego
    if config.EJEMPLOS_DENTRO_DE_VENTANA and wobj is not None:
        w, h = wobj.width, wobj.height
        izq, sup = wobj.left, wobj.top
        puntos_pantalla = [
            (izq + w // 2, sup + h // 4),
            (izq + int(w * 0.25), sup + int(h * 0.55)),
            (izq + int(w * 0.72), sup + int(h * 0.62)),
        ]
        puntos_dentro = [
            (int(w * 0.2), int(h * 0.2)),
            (w // 2, h // 2),
            (int(w * 0.65), int(h * 0.35)),
        ]
    else:
        puntos_pantalla = [(500, 300), (800, 400), (1000, 500)]
        puntos_dentro = [(200, 150), (400, 250), (600, 350)]

    for ax, ay in puntos_pantalla:
        gestor.coordenadas_relativas(ax, ay)
        time.sleep(config.PAUSA_ENTRE_CONVERSIONES)

    for rx, ry in puntos_dentro:
        gestor.coordenadas_absolutas(rx, ry)
        time.sleep(config.PAUSA_ENTRE_CONVERSIONES)

    decir("✓ Ejemplos listos")


def demo_clics(gestor: GestorVentana) -> None:
    if not gestor.info_ventana:
        return

    decir(f"Clics de prueba (en {int(config.PAUSA_ANTES_CLICS_DEMO)} s)…")
    time.sleep(config.PAUSA_ANTES_CLICS_DEMO)

    wv, hv = gestor.info_ventana["size"]
    cx, cy = wv // 2, hv // 2
    puntos = [
        (cx, int(hv * 0.25)),
        (int(wv * 0.35), int(hv * 0.72)),
        (cx, cy),
    ]

    for i, (rx, ry) in enumerate(puntos, 1):
        decir(f"  Clic {i}/3")
        gestor.clic_en_ventana(rx, ry)
        time.sleep(config.PAUSA_ENTRE_CLICS)


def abrir_carpeta_salida() -> None:
    if not getattr(config, "ABRIR_CARPETA_AL_FINAL", False):
        return
    carpeta = os.path.abspath(config.CARPETA_SALIDA)
    try:
        if sys.platform == "win32":
            os.startfile(carpeta)  # type: ignore[attr-defined]
        else:
            webbrowser.open(f"file://{carpeta}")
    except Exception as e:
        decir_debug(str(e))


def esperar_cierre_panel_con_esc() -> None:
    """El overlay sigue hasta que pulses Esc (grabación del resultado)."""
    global _OVERLAY
    if _OVERLAY is None or not config.PANEL_ACTIVO:
        return
    decir("Pulsa Esc en el panel para cerrar.")
    hilo = _OVERLAY._thread
    if hilo is not None and hilo.is_alive():
        hilo.join()
    _OVERLAY = None


def cerrar_panel() -> None:
    global _OVERLAY
    if _OVERLAY is None:
        return
    hilo = _OVERLAY._thread
    _OVERLAY.stop()
    if hilo is not None and hilo.is_alive():
        hilo.join(timeout=3.0)
    _OVERLAY = None


def procesar_argumentos() -> None:
    parser = argparse.ArgumentParser(description="Módulo 2 — ventanas y coordenadas")
    parser.add_argument("--overlay", action="store_true", help="Panel flotante de mensajes")
    parser.add_argument("--debug-temp", action="store_true", help="Detalles técnicos")
    args = parser.parse_args()
    if args.overlay:
        config.PANEL_ACTIVO = True
    if args.debug_temp:
        config.LOG_DEPURACION = True


def main() -> int:
    procesar_argumentos()
    configurar_entorno()

    try:
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

        n = getattr(config, "SEGUNDOS_CUENTA_ATRAS", 5)
        decir("Prepárate…")
        for i in range(n, 0, -1):
            decir(f"  {i}…")
            time.sleep(1)

        gestor = GestorVentana(log=decir, log_debug=decir_debug)

        if not gestor.buscar_ventana_juego():
            decir("Abre Dofus Touch (puede estar minimizado) y vuelve a ejecutar.")
            return 1

        time.sleep(config.PAUSA_TRAS_BUSCAR_VENTANA)
        if not gestor.activar_ventana():
            return 1
        time.sleep(config.PAUSA_TRAS_ACTIVAR_VENTANA)

        iniciar_panel()

        demo_info_ventana(gestor)
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        demo_tres_fotos(gestor)
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        demo_conversiones(gestor)
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        demo_clics(gestor)

        decir("Módulo 2 completado.")
        esperar_cierre_panel_con_esc()
        abrir_carpeta_salida()
        return 0
    finally:
        cerrar_panel()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        cerrar_panel()
        raise SystemExit(1)
