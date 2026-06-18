#!/usr/bin/env python3
"""
Módulo 4:
1) modal: zona del juego + zona de coordenadas → Iniciar
2) leer coordenadas del mapa (Tesseract)
3) pausa para cambiar de mapa a mano → segunda lectura y comparación
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
from common.menu_calibracion_doble import (
    aplicar_zona_ocr_en_config,
    mostrar_menu_calibracion_doble,
)
from common.zona_pantalla import aplicar_zona_en_config, describir_zona
from lector_ocr import (
    capturar_recorte_ocr,
    extraer_coordenadas,
    leer_texto,
    tesseract_instalado,
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


def preparar_juego_al_frente() -> GestorVentana | None:
    """Antes del modal: el juego visible para poder dibujar las zonas."""
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
        title="Módulo 4",
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


def _ruta_recorte_ocr(segunda: bool = False) -> str | None:
    if not getattr(config, "GUARDAR_RECORTE_OCR", True):
        return None
    nombre = (
        getattr(config, "ARCHIVO_RECORTE_OCR_2", "recorte_coordenadas_2.png")
        if segunda
        else config.ARCHIVO_RECORTE_OCR
    )
    return os.path.join(config.CARPETA_SALIDA, nombre)


def leer_coordenadas_mapa(
    *,
    etiqueta: str = "",
    segunda_lectura: bool = False,
) -> tuple[int, int] | None:
    if etiqueta:
        decir(f"{etiqueta} — leyendo coordenadas…")
    else:
        decir("Leyendo coordenadas del mapa…")

    img = capturar_recorte_ocr(_ruta_recorte_ocr(segunda=segunda_lectura))
    if img is None:
        decir("No pude capturar. Vuelve a marcar la zona de coordenadas.")
        return None

    if not tesseract_instalado():
        decir("Falta Tesseract OCR — mira el README del módulo 4.")
        return None

    texto = leer_texto(img)
    decir_debug(f"OCR: {texto!r}")
    archivo = (
        getattr(config, "ARCHIVO_RECORTE_OCR_2", "recorte_coordenadas_2.png")
        if segunda_lectura
        else config.ARCHIVO_RECORTE_OCR
    )
    decir_debug(f"Recorte: output/{archivo}")

    coords = extraer_coordenadas(texto)
    if coords:
        return coords

    decir("No pude leer X e Y — marca la zona más ajustada a los números.")
    return None


def mostrar_coordenadas(etiqueta: str, x: int, y: int) -> None:
    decir("")
    decir(f"✓ {etiqueta}")
    decir(f"   {x} , {y}")
    decir("")


def esperar_cambio_mapa_manual() -> None:
    seg = float(getattr(config, "PAUSA_MANUAL_CAMBIO_MAPA", 5.0))
    if seg <= 0:
        return

    decir("")
    decir("Ahora mueve el mapa a mano (arrastra con el ratón).")
    entero = int(seg)
    if getattr(config, "CUENTA_ATRAS_CAMBIO_MAPA", True) and entero >= 1:
        decir(f"  Tienes {entero} s…")
        for i in range(entero, 0, -1):
            decir(f"    {i}…")
            time.sleep(1)
        resto = seg - entero
        if resto > 0.01:
            time.sleep(resto)
    else:
        decir(f"  Esperando {seg:g} s…")
        time.sleep(seg)
    decir("")


def comparar_lecturas(
    coords1: tuple[int, int],
    coords2: tuple[int, int],
) -> None:
    x1, y1 = coords1
    x2, y2 = coords2
    decir("Comparación:")
    decir(f"   1.ª lectura: {x1} , {y1}")
    decir(f"   2.ª lectura: {x2} , {y2}")
    if (x1, y1) == (x2, y2):
        decir("  ⚠ Sin cambio — arrastra más el mapa en la demo.")
    else:
        decir("  ✓ Coordenadas distintas — el OCR detectó el movimiento.")
    decir("")


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
    parser = argparse.ArgumentParser(description="Módulo 4 — leer coordenadas en la zona")
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
        calibracion = mostrar_menu_calibracion_doble(
            titulo="Módulo 4 — Calibración",
            subtitulo="Marca el juego y la franja de coordenadas",
            ruta_zona_juego=base / config.RUTA_ZONA_JSON,
            ruta_zona_ocr=base / config.RUTA_ZONA_OCR_JSON,
            log_debug=decir_debug,
        )
        if calibracion.cancelado or not calibracion.zona_juego or not calibracion.zona_ocr:
            print("Cancelado. Vuelve a ejecutar cuando quieras.")
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

        coords1 = leer_coordenadas_mapa(etiqueta="1.ª lectura")
        if not coords1:
            decir("Demo incompleta — revisa Tesseract o la zona de coordenadas.")
            return 1
        mostrar_coordenadas("Coordenadas del mapa", coords1[0], coords1[1])

        esperar_cambio_mapa_manual()

        coords2 = leer_coordenadas_mapa(etiqueta="2.ª lectura", segunda_lectura=True)
        if not coords2:
            decir("No pude leer tras mover el mapa — revisa la zona OCR.")
            return 1
        mostrar_coordenadas("Coordenadas del mapa", coords2[0], coords2[1])

        comparar_lecturas(coords1, coords2)

        decir("Módulo 4 completado.")
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
