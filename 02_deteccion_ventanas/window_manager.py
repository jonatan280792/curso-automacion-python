#!/usr/bin/env python3
"""Ventana del juego: buscar, coordenadas relativas/absolutas, recortes y clics."""

from __future__ import annotations

import os
import time
from collections.abc import Callable

import pyautogui as pg
import pygetwindow as gw

import config
from common.zona_pantalla import capturar_pantalla_en_zona


class GestorVentana:
    """Encuentra la ventana del juego y opera en coordenadas relativas a ella."""

    def __init__(
        self,
        log: Callable[[str], None] | None = None,
        log_debug: Callable[[str], None] | None = None,
    ) -> None:
        self.ventana_juego = None
        self.info_ventana = None
        self._log = log or print
        self._log_debug = log_debug or (lambda _m: None)

    def _es_fantasma(self, w) -> bool:
        if getattr(w, "isMinimized", False):
            return False
        return w.left <= config.UMBRAL_FUERA_PANTALLA or w.top <= config.UMBRAL_FUERA_PANTALLA

    def _esta_minimizada(self, w) -> bool:
        return bool(getattr(w, "isMinimized", False))

    def _tamano_ok(self, w, min_ancho: int, min_alto: int) -> bool:
        if w.width < config.VENTANA_DIMINUTA_ANCHO or w.height < config.VENTANA_DIMINUTA_ALTO:
            return False
        return w.width >= min_ancho and w.height >= min_alto

    def _recolectar(self, tokens: tuple[str, ...]) -> list:
        resultado = []
        vistos: set[tuple[str, int, int, int, int]] = set()
        for token in tokens:
            for w in gw.getWindowsWithTitle(token):
                clave = (w.title, w.left, w.top, w.width, w.height)
                if clave in vistos:
                    continue
                vistos.add(clave)
                if self._es_fantasma(w):
                    self._log_debug(
                        f"descartada: {w.title!r} @({w.left},{w.top}) {w.width}x{w.height}"
                    )
                    continue
                resultado.append(w)
        return resultado

    def _elegir_por_tamano(self, todas: list):
        minimizadas = [w for w in todas if self._esta_minimizada(w)]
        if minimizadas:
            return minimizadas[0]

        candidatos: list = []
        for min_ancho, min_alto in (
            (config.VENTANA_MIN_ANCHO, config.VENTANA_MIN_ALTO),
            (config.VENTANA_MIN_ANCHO_RELAX, config.VENTANA_MIN_ALTO_RELAX),
        ):
            candidatos = [w for w in todas if self._tamano_ok(w, min_ancho, min_alto)]
            if candidatos:
                break
        if not candidatos:
            return None
        return max(candidatos, key=lambda x: x.width * x.height)

    def _listar_candidatos_crudos(self, tokens: tuple[str, ...]) -> None:
        self._log_debug("--- ventanas con título (sin filtrar) ---")
        for token in tokens:
            for w in gw.getWindowsWithTitle(token):
                self._log_debug(
                    f"  · {w.title!r} @({w.left},{w.top}) {w.width}x{w.height} "
                    f"min={self._esta_minimizada(w)}"
                )

    def _asignar_ventana(self, w, *, silencioso: bool) -> None:
        self.ventana_juego = w
        if silencioso:
            self._log_debug(f"ventana: {w.title!r} {w.width}x{w.height}")
            return
        if self._esta_minimizada(w):
            self._log("✓ Juego encontrado (en la barra, minimizado)")
        else:
            self._log("✓ Juego encontrado")

    def buscar_ventana_juego(self, *, silencioso: bool = False):
        prioridad = getattr(config, "TITULOS_VENTANA_PRIORIDAD", ())

        if prioridad:
            elegida = self._elegir_por_tamano(self._recolectar(prioridad))
            if elegida is not None:
                self._asignar_ventana(elegida, silencioso=silencioso)
                return elegida

        elegida = self._elegir_por_tamano(self._recolectar(config.TITULOS_VENTANA))
        if elegida is None:
            if not silencioso:
                self._log("No encontré el juego abierto.")
                self._log("Déjalo en la barra de tareas (puede estar minimizado).")
                self._listar_candidatos_crudos(
                    prioridad + config.TITULOS_VENTANA if prioridad else config.TITULOS_VENTANA
                )
            return None

        self._asignar_ventana(elegida, silencioso=silencioso)
        return elegida

    def _actualizar_tras_restore(self) -> bool:
        """Tras restore(), pygetwindow a veces deja datos viejos; busca de nuevo sin ruido."""
        titulo = ""
        if self.ventana_juego:
            titulo = self.ventana_juego.title or ""
        tokens = (titulo,) if titulo else getattr(config, "TITULOS_VENTANA_PRIORIDAD", ())
        for token in tokens:
            if not token:
                continue
            for w in gw.getWindowsWithTitle(token):
                if self._esta_minimizada(w):
                    continue
                if self._es_fantasma(w):
                    continue
                if self._tamano_ok(
                    w, config.VENTANA_MIN_ANCHO_RELAX, config.VENTANA_MIN_ALTO_RELAX
                ):
                    self.ventana_juego = w
                    self._log_debug(f"tras restore: {w.width}x{w.height} @({w.left},{w.top})")
                    return True
        return self.buscar_ventana_juego(silencioso=True) is not None

    def obtener_info_ventana(self):
        if not self.ventana_juego and not self.buscar_ventana_juego():
            return None

        w = self.ventana_juego
        info = {
            "title": w.title,
            "position": (w.left, w.top),
            "size": (w.width, w.height),
            "center": (w.left + w.width // 2, w.top + w.height // 2),
            "is_active": w.isActive,
            "is_minimized": w.isMinimized,
            "is_maximized": w.isMaximized,
        }
        self.info_ventana = info

        px, py = info["position"]
        ancho, alto = info["size"]
        self._log(f"Ventana: posición ({px}, {py}), tamaño {ancho}×{alto}")
        self._log_debug(f"centro {info['center']} activa={info['is_active']}")

        return info

    def activar_ventana(self) -> bool:
        if not self.ventana_juego and not self.buscar_ventana_juego():
            return False

        try:
            w = self.ventana_juego
            if self._esta_minimizada(w):
                self._log("Levanto el juego…")
                w.restore()
                time.sleep(config.PAUSA_TRAS_RESTAURAR)
                if not self._actualizar_tras_restore():
                    return False
                w = self.ventana_juego
            w.activate()
            time.sleep(config.PAUSA_TRAS_ACTIVAR)
            self._log("✓ Juego al frente")
            return True
        except Exception as e:
            self._log("No pude poner el juego al frente.")
            self._log_debug(str(e))
            return False

    def capturar_region_ventana(
        self,
        x: int,
        y: int,
        ancho: int,
        alto: int,
        ruta_guardar: str | None = None,
    ):
        if not self.ventana_juego and not self.buscar_ventana_juego():
            return None

        try:
            abs_x = int(self.ventana_juego.left) + x
            abs_y = int(self.ventana_juego.top) + y
            ancho = max(1, int(ancho))
            alto = max(1, int(alto))

            img = capturar_pantalla_en_zona(abs_x, abs_y, ancho, alto)

            if ruta_guardar:
                carpeta = os.path.dirname(ruta_guardar)
                if carpeta:
                    os.makedirs(carpeta, exist_ok=True)
                img.save(ruta_guardar)
                self._log_debug(f"guardado {os.path.basename(ruta_guardar)}")

            return img

        except Exception as e:
            self._log_debug(f"fallo captura región: {e}")
            return None

    def coordenadas_relativas(self, abs_x: int, abs_y: int):
        if not self.ventana_juego:
            return None
        w = self.ventana_juego
        rel_x, rel_y = abs_x - w.left, abs_y - w.top
        self._log_debug(f"pantalla ({abs_x},{abs_y}) → juego ({rel_x},{rel_y})")
        return rel_x, rel_y

    def coordenadas_absolutas(self, rel_x: int, rel_y: int):
        if not self.ventana_juego:
            return None
        w = self.ventana_juego
        abs_x, abs_y = w.left + rel_x, w.top + rel_y
        self._log_debug(f"juego ({rel_x},{rel_y}) → pantalla ({abs_x},{abs_y})")
        return abs_x, abs_y

    def clic_en_ventana(self, rel_x: int, rel_y: int) -> bool:
        if not self.ventana_juego:
            return False

        try:
            w = self.ventana_juego
            if self._esta_minimizada(w):
                w.restore()
                time.sleep(config.PAUSA_TRAS_RESTAURAR)
                self._actualizar_tras_restore()
                w = self.ventana_juego
            if w and not getattr(w, "isActive", True):
                w.activate()
                time.sleep(config.PAUSA_TRAS_ACTIVAR)
            time.sleep(config.PAUSA_ANTES_CLIC)
            pg.click(w.left + rel_x, w.top + rel_y)
            return True
        except Exception as e:
            self._log_debug(f"clic fallido: {e}")
            return False


WindowManager = GestorVentana
