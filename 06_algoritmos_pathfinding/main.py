#!/usr/bin/env python3
"""
Módulo 6:
1) modal: zona del juego + zona OCR + destino X/Y → Iniciar
2) leer posición actual (OCR) → calcular ruta con BFS (data/mundo.json)
3) ejecutar cada paso: arrastrar mapa → esperar cambio de coords (OCR)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable
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
from buscador_rutas import BuscadorRutas
from menu_calibracion_ruta import mostrar_menu_calibracion_ruta
from common.zona_pantalla import aplicar_zona_en_config, describir_zona
from lector_ocr import tesseract_instalado
from posicion_ocr import (
    aplicar_zona_ocr,
    crear_lector_rapido,
    ejecutar_preflight,
    leer_con_votacion,
)
from navegacion import ejecutar_paso_arrastre, validar_vecino_paso
from window_manager import GestorVentana

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
    os.makedirs(config.CARPETA_SALIDA, exist_ok=True)


def preparar_juego_al_frente() -> GestorVentana | None:
    gestor = GestorVentana(log=print, log_debug=decir_debug)
    print("Buscando Dofus Touch…")
    if not gestor.buscar_ventana_juego():
        print("Abre el juego (puede estar minimizado) y vuelve a ejecutar.")
        return None
    time.sleep(config.PAUSA_TRAS_BUSCAR_VENTANA)
    if not gestor.activar_ventana():
        return None
    time.sleep(config.PAUSA_TRAS_ACTIVAR_VENTANA)
    print("✓ Juego al frente. Ahora el cuadro de calibración.")
    return gestor


def iniciar_panel(gestor: GestorVentana | None = None) -> None:
    global _OVERLAY
    if not config.PANEL_ACTIVO:
        return
    if _OVERLAY is not None and _OVERLAY.root is not None:
        return

    from common.overlay import GameLogOverlay, monitor_rect_en_punto

    _OVERLAY = GameLogOverlay(
        title="Módulo 6",
        rel_x=0.0,
        rel_y=config.PANEL_POS_Y,
        rel_w=config.PANEL_ANCHO_FRAC,
        rel_h=config.PANEL_ALTO_FRAC,
        max_lines=28,
    )
    _OVERLAY.start(persist=True)
    time.sleep(config.PAUSA_PANEL_LAYOUT)

    if getattr(config, "PANEL_ANCLAR_MONITOR", True) and gestor is not None:
        gestor.buscar_ventana_juego(silencioso=True)
        ventana = gestor.ventana_juego
        if ventana is not None:
            cx = int(ventana.left + ventana.width / 2)
            cy = int(ventana.top + ventana.height / 2)
            monitor = monitor_rect_en_punto(cx, cy)
            if monitor is not None:
                _OVERLAY.reposition_anchor_monitor_right(
                    *monitor,
                    margin_right_frac=float(
                        getattr(config, "PANEL_MARGEN_DERECHA_FRAC", 0.0)
                    ),
                )
                return

    _OVERLAY.reposition_on_region(
        config.ZONA_IZQUIERDA,
        config.ZONA_SUPERIOR,
        config.ZONA_ANCHO,
        config.ZONA_ALTO,
    )


def leer_origen_actual() -> tuple[int, int] | None:
    decir("Leyendo dónde estoy ahora (OCR)…")
    if not tesseract_instalado():
        decir("Falta Tesseract OCR — mira el README (igual que módulo 4).")
        return None
    coords = leer_con_votacion(log=decir, log_debug=decir_debug, validar_en_grafo=True)
    if coords is None:
        decir("No pude leer tu posición — revisa la zona OCR.")
        return None
    return coords


def calcular_ruta(
    origen: tuple[int, int],
    destino: tuple[int, int],
) -> list[str] | None:
    try:
        n_celdas, ruta_json = BuscadorRutas.info_grafo()
        decir(f"Grafo: {n_celdas} casillas ({ruta_json.name})")
    except FileNotFoundError as e:
        decir(f"✗ {e}")
        return None

    decir("Calculando ruta (BFS + bloqueos)…")
    pasos, error = BuscadorRutas.calcular_ruta(origen, destino)

    if error:
        decir(f"✗ {error}")
        return None
    if not pasos:
        decir("✓ Ya estás en el destino — no hay pasos que dar.")
        return []

    decir("")
    decir(f"✓ Ruta encontrada — {len(pasos)} paso(s):")
    for i, direccion in enumerate(pasos, 1):
        etiqueta = BuscadorRutas.direccion_a_espanol(direccion)
        decir(f"  {i}. {etiqueta}")
    decir("")
    return pasos


def ejecutar_ruta(
    pasos: list[str],
    posicion_actual: tuple[int, int],
    destino: tuple[int, int],
    gestor: GestorVentana | None = None,
) -> bool:
    total = len(pasos)
    if total == 0:
        decir(f"Destino: {destino[0]} , {destino[1]} — sin movimientos.")
        return True

    decir("Ejecutando ruta en el juego…")
    decir("(Tras cada arrastre espero a que el OCR vea coords nuevas.)")
    decir("")

    leer_coords = crear_lector_rapido(log_debug=decir_debug)

    for i, direccion in enumerate(pasos, 1):
        etiqueta = BuscadorRutas.direccion_a_espanol(direccion)
        decir(f"Paso {i}/{total} — {etiqueta}")
        decir(f"  Desde: {posicion_actual[0]} , {posicion_actual[1]}")

        validar = None
        if getattr(config, "VALIDAR_VECINO_PASO", True):
            validar = lambda a, n, d=direccion: validar_vecino_paso(a, n, d)

        try:
            nueva = ejecutar_paso_arrastre(
                direccion,
                posicion_actual,
                leer_coords,
                gestor=gestor,
                log=decir,
                validar=validar,
            )
        except ValueError as e:
            decir(f"  ✗ {e}")
            return False

        if nueva is None:
            decir("  Revisa zona OCR o tiempos OCR_* en config.py")
            return False

        posicion_actual = nueva

        if posicion_actual == destino:
            decir("  ✓ Casilla destino alcanzada.")
            break

        decir("")

    decir("Posición final:")
    decir(f"   {posicion_actual[0]} , {posicion_actual[1]}")
    if posicion_actual == destino:
        decir("✓ Llegaste al destino.")
        return True

    decir(
        f"✗ Destino era {destino[0]} , {destino[1]} — "
        "revisa OCR, DRAG_PIXELES o si el mapa cargó tras el último paso."
    )
    return False


def demo_pathfinding_completo(
    destino: tuple[int, int],
    gestor: GestorVentana | None = None,
) -> bool:
    if not tesseract_instalado():
        decir("Falta Tesseract OCR — mira el README del módulo 4.")
        return False

    origen = leer_origen_actual()
    if origen is None:
        return False
    decir(f"  Origen (ahora): {origen[0]} , {origen[1]}")
    decir(f"  Destino: {destino[0]} , {destino[1]}")
    decir("")

    pasos = calcular_ruta(origen, destino)
    if pasos is None:
        return False

    return ejecutar_ruta(pasos, origen, destino, gestor=gestor)


def esperar_cierre_panel_con_esc() -> None:
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


def intentar_leer_posicion_guardada(
    rect_ocr: tuple[int, int, int, int],
) -> tuple[int, int] | None:
    """Lee coords con la zona del modal (votación corta, sin realinear)."""
    aplicar_zona_ocr(rect_ocr)
    if not tesseract_instalado():
        return None
    return leer_con_votacion(validar_en_grafo=False)


def procesar_argumentos() -> None:
    parser = argparse.ArgumentParser(description="Módulo 6 — ruta por coords + ejecución")
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
        gestor = preparar_juego_al_frente()
        if gestor is None:
            return 1

        base = Path(__file__).resolve().parent

        calibracion = mostrar_menu_calibracion_ruta(
            titulo="Módulo 6 — Calibración",
            subtitulo="Marca las dos zonas, elige destino en el mapa y pulsa Iniciar",
            ruta_zona_juego=base / config.RUTA_ZONA_JSON,
            ruta_zona_ocr=base / config.RUTA_ZONA_OCR_JSON,
            ruta_mundo_json=base / config.RUTA_MUNDO_JSON,
            leer_posicion_ocr=intentar_leer_posicion_guardada,
        )
        if calibracion.cancelado or not calibracion.zona_juego or not calibracion.zona_ocr:
            print("Cancelado. Vuelve a ejecutar cuando quieras.")
            return 0
        if calibracion.destino_x is None or calibracion.destino_y is None:
            print("Falta el destino. Vuelve a ejecutar.")
            return 0

        destino = (calibracion.destino_x, calibracion.destino_y)

        aplicar_zona_en_config(config, calibracion.zona_juego)
        aplicar_zona_ocr(calibracion.zona_ocr)
        decir_debug(describir_zona(calibracion.zona_juego))
        print("✓ Zonas listas. Empieza el programa…")

        gestor = GestorVentana(log=decir, log_debug=decir_debug)
        gestor.buscar_ventana_juego(silencioso=True)
        gestor.activar_ventana()
        time.sleep(config.PAUSA_TRAS_ACTIVAR_VENTANA)

        if ejecutar_preflight(log=decir, log_debug=decir_debug) is None:
            decir("Demo cancelada — corrige la zona OCR y vuelve a ejecutar.")
            return 1

        iniciar_panel(gestor=gestor)

        n = getattr(config, "SEGUNDOS_CUENTA_ATRAS", 5)
        decir("Prepárate…")
        for i in range(n, 0, -1):
            decir(f"  {i}…")
            time.sleep(1)
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        if not demo_pathfinding_completo(destino, gestor=gestor):
            decir("Demo incompleta — revisa OCR, destino o DRAG_PIXELES.")
            return 1

        decir("Módulo 6 completado.")
        esperar_cierre_panel_con_esc()
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
