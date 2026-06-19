#!/usr/bin/env python3
"""
Módulo 5:
1) modal: zona del juego + zona OCR + ruta con flechas → Iniciar
2) leer coordenadas → ejecutar cada paso → comprobar cambios con OCR
"""

from __future__ import annotations

import argparse
import os
import sys
import time
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
from common.editor_ruta import formatear_ruta, token_a_etiqueta
from common.menu_calibracion_doble import aplicar_zona_ocr_en_config
from common.zona_pantalla import aplicar_zona_en_config, describir_zona
from lector_ocr import (
    capturar_recorte_ocr,
    extraer_coordenadas,
    leer_texto,
    tesseract_instalado,
)
from menu_calibracion_navegacion import mostrar_menu_calibracion_navegacion
from navegacion import arrastrar_paso, click_centro_juego, esperar_cambio_coordenadas
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


def iniciar_panel() -> None:
    global _OVERLAY
    if not config.PANEL_ACTIVO:
        return
    if _OVERLAY is not None and _OVERLAY.root is not None:
        return

    from common.overlay import GameLogOverlay

    _OVERLAY = GameLogOverlay(
        title="Módulo 5",
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


def leer_coordenadas_actuales() -> tuple[int, int] | None:
    ruta = None
    if getattr(config, "GUARDAR_RECORTE_OCR", False):
        ruta = os.path.join(config.CARPETA_SALIDA, "recorte_coordenadas.png")

    img = capturar_recorte_ocr(ruta)
    if img is None:
        return None
    if not tesseract_instalado():
        decir("Falta Tesseract OCR — mira el README (igual que módulo 4).")
        return None
    texto = leer_texto(img)
    decir_debug(f"OCR: {texto!r}")
    return extraer_coordenadas(texto)


def ejecutar_ruta(
    pasos: list[str],
    gestor: GestorVentana | None = None,
) -> bool:
    if not tesseract_instalado():
        decir("Instala Tesseract (ver README módulo 4).")
        return False

    decir("Posición antes del recorrido:")
    posicion = leer_coordenadas_actuales()
    if posicion is None:
        decir("No pude leer coordenadas — revisa la zona OCR.")
        return False
    decir(f"   {posicion[0]} , {posicion[1]}")
    decir(f"Ruta: {formatear_ruta(pasos)}")
    decir("")

    total = len(pasos)
    for i, paso in enumerate(pasos, 1):
        etiqueta = token_a_etiqueta(paso)
        decir(f"Paso {i}/{total} — {etiqueta}")

        if paso == "click":
            click_centro_juego(gestor=gestor, log=decir)
            decir("")
            continue

        decir(f"  Desde: {posicion[0]} , {posicion[1]}")
        try:
            arrastrar_paso(paso, gestor=gestor, log=decir)
        except KeyError as e:
            decir(f"  ✗ Dirección no válida: {e}")
            return False

        decir("  Esperando cambio de coordenadas…")
        nueva = esperar_cambio_coordenadas(posicion, leer_coordenadas_actuales, log=decir)
        if nueva is None:
            decir("  Revisa zona OCR o sube OCR_ESPERA_MAXIMA en config.py")
            return False
        posicion = nueva
        decir("")

    decir("Posición después del recorrido:")
    decir(f"   {posicion[0]} , {posicion[1]}")
    decir("")
    decir("✓ Recorrido completado.")
    return True


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


def procesar_argumentos() -> None:
    parser = argparse.ArgumentParser(description="Módulo 5 — navegación + ruta manual")
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
        calibracion = mostrar_menu_calibracion_navegacion(
            titulo="Módulo 5 — Calibración",
            subtitulo="Marca las zonas y arma tu ruta con las flechas",
            ruta_zona_juego=base / config.RUTA_ZONA_JSON,
            ruta_zona_ocr=base / config.RUTA_ZONA_OCR_JSON,
            ruta_ejemplo=config.RUTA_EJEMPLO,
        )
        if calibracion.cancelado or not calibracion.zona_juego or not calibracion.zona_ocr:
            print("Cancelado. Vuelve a ejecutar cuando quieras.")
            return 0
        if not calibracion.pasos:
            print("Falta la ruta. Vuelve a ejecutar.")
            return 0

        aplicar_zona_en_config(config, calibracion.zona_juego)
        aplicar_zona_ocr_en_config(config, calibracion.zona_ocr)
        decir_debug(describir_zona(calibracion.zona_juego))
        print("✓ Zonas listas. Empieza el programa…")

        gestor = GestorVentana(log=decir, log_debug=decir_debug)
        gestor.buscar_ventana_juego(silencioso=True)
        gestor.activar_ventana()
        time.sleep(config.PAUSA_TRAS_ACTIVAR_VENTANA)

        iniciar_panel()

        n = getattr(config, "SEGUNDOS_CUENTA_ATRAS", 5)
        decir("Prepárate…")
        for i in range(n, 0, -1):
            decir(f"  {i}…")
            time.sleep(1)
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        if not ejecutar_ruta(calibracion.pasos, gestor=gestor):
            decir("Demo incompleta — revisa OCR o DRAG_PIXELES.")
            return 1

        decir("Módulo 5 completado.")
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
