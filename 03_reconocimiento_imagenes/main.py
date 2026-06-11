#!/usr/bin/env python3
"""
Módulo 3:
1) buscar la ventana del juego y ponerla al frente
2) marcar zona del juego (con el juego ya visible)
3) buscar plantillas PNG dentro de la zona (iconos de interfaz)
4) demo en secuencia: inventario → cerrar → características (con pausas en el log)
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
from buscador_imagen import BuscadorImagen
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
    os.makedirs(config.CARPETA_PLANTILLAS, exist_ok=True)


def iniciar_panel() -> None:
    global _OVERLAY
    if not config.PANEL_ACTIVO:
        return
    if _OVERLAY is not None and _OVERLAY.root is not None:
        return

    from common.overlay import GameLogOverlay

    _OVERLAY = GameLogOverlay(
        title="Módulo 3",
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
    if _OVERLAY is None:
        return
    _OVERLAY.set_alpha(0.03 if discreto else _ALPHA_PANEL)


def explicar_plantillas() -> None:
    decir("Plantillas = fotos pequeñas (iconos) en:")
    decir(f"  {config.CARPETA_PLANTILLAS}/")
    decir("El demo usa 3 PNG que ya vienen con el curso (ver LEEME.md).")


def verificar_plantillas(buscador: BuscadorImagen) -> bool:
    decir("")
    decir("Plantillas del demo:")
    ok = True
    for nombre, descripcion in config.DEMO_SECUENCIA:
        ruta = buscador.ruta_plantilla(nombre)
        if os.path.isfile(ruta):
            decir(f"  ✓ {nombre}.png — {descripcion}")
        else:
            decir(f"  ✗ Falta {nombre}.png — {descripcion}")
            ok = False
    if not ok:
        decir("")
        decir("Añade los PNG en images/plantillas/ antes de grabar.")
    return ok


def _esperar_entre_pasos(segundos: float) -> None:
    seg = max(0.0, float(segundos))
    if seg <= 0:
        return
    entero = int(seg)
    if getattr(config, "CUENTA_ATRAS_ENTRE_PASOS", True) and entero >= 1:
        decir(f"  Esperando {entero} s…")
        for i in range(entero, 0, -1):
            decir(f"    {i}…")
            time.sleep(1)
        resto = seg - entero
        if resto > 0.01:
            time.sleep(resto)
    else:
        decir(f"  Esperando {seg:g} s…")
        time.sleep(seg)


def _mensaje_no_encontrado(buscador: BuscadorImagen, nombre: str) -> None:
    sim = buscador.ultima_confianza
    if sim is not None:
        decir(f"  ✗ No encontrado (parecido {sim:.0%})")
        decir(f"    Revisa {nombre}.png o baja CONFIANZA_BUSQUEDA en config.py")
    else:
        decir(f"  ✗ No encontrado — revisa {nombre}.png o la zona marcada")


def demo_secuencia_iconos(
    gestor: GestorVentana,
    buscador: BuscadorImagen,
) -> bool:
    region = buscador.region_busqueda(gestor)
    if region is None:
        decir("No hay zona de búsqueda válida.")
        return False

    pasos = config.DEMO_SECUENCIA
    total = len(pasos)
    pausa = float(getattr(config, "PAUSA_ENTRE_PASOS_DEMO", 5.0))
    modo = getattr(config, "BUSCAR_EN", "zona")

    decir("")
    decir("Demo en secuencia (buscar → clic → pausa)…")
    decir(f"  Región: {modo} · confianza {config.CONFIANZA_BUSQUEDA}")
    decir(f"  Pausa entre pasos: {pausa:g} s")
    decir("")

    for i, (nombre, descripcion) in enumerate(pasos, 1):
        ruta = buscador.ruta_plantilla(nombre)
        if not os.path.isfile(ruta):
            decir(f"Paso {i}/{total} — {descripcion}")
            decir(f"  ✗ Falta {nombre}.png")
            return False

        decir(f"Paso {i}/{total} — {descripcion}")
        decir(f"  Buscando {nombre}.png…")

        pos = buscador.buscar(ruta, region)
        if pos is None:
            _mensaje_no_encontrado(buscador, nombre)
            return False

        decir(f"  ✓ Encontrado en ({pos[0]}, {pos[1]})")
        decir("  Clic…")
        if not buscador.clic_en(pos):
            decir("  ✗ Clic fallido")
            return False
        decir("  ✓ Clic hecho")

        if i < total:
            decir("")
            _esperar_entre_pasos(pausa)
            decir("")

    decir("✓ Secuencia completada.")
    return True


def demo_confianza_debug(
    buscador: BuscadorImagen,
    region: tuple[int, int, int, int],
) -> None:
    nombre, _ = config.DEMO_SECUENCIA[0]
    ruta = buscador.ruta_plantilla(nombre)
    if not os.path.isfile(ruta):
        return

    decir_debug("comparando confianza 0.95 vs 0.65…")
    for conf in (0.95, 0.65):
        pos = buscador.buscar(ruta, region, confianza=conf)
        decir_debug(f"  conf={conf} → {pos}")


def abrir_carpeta_plantillas() -> None:
    if not getattr(config, "ABRIR_CARPETA_AL_FINAL", False):
        return
    carpeta = os.path.abspath(config.CARPETA_PLANTILLAS)
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
    parser = argparse.ArgumentParser(description="Módulo 3 — buscar iconos en el juego")
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

        gestor = GestorVentana(log=decir, log_debug=decir_debug)

        if not gestor.buscar_ventana_juego():
            decir("Abre Dofus Touch (puede estar minimizado) y vuelve a ejecutar.")
            return 1

        time.sleep(config.PAUSA_TRAS_BUSCAR_VENTANA)
        if not gestor.activar_ventana():
            return 1
        time.sleep(config.PAUSA_TRAS_ACTIVAR_VENTANA)

        pausa_inicio = float(getattr(config, "PAUSA_ANTES_CALIBRAR_ZONA", 0))
        if pausa_inicio > 0:
            seg = int(pausa_inicio) if pausa_inicio == int(pausa_inicio) else pausa_inicio
            print(f"Juego al frente. En {seg} s marca la zona del juego…")
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

        gestor.obtener_info_ventana()
        iniciar_panel()

        explicar_plantillas()
        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        buscador = BuscadorImagen(log=decir, log_debug=decir_debug)

        if not verificar_plantillas(buscador):
            return 1

        time.sleep(config.PAUSA_ENTRE_BLOQUES)

        if config.LOG_DEPURACION:
            region = buscador.region_busqueda(gestor)
            if region:
                demo_confianza_debug(buscador, region)

        if not demo_secuencia_iconos(gestor, buscador):
            decir("Demo incompleta — revisa plantillas, zona o confianza.")
            return 1

        decir("Módulo 3 completado.")
        esperar_cierre_panel_con_esc()
        abrir_carpeta_plantillas()
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
