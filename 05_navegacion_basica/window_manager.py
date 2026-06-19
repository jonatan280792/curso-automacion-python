#!/usr/bin/env python3
"""Ventana del juego: buscar y activar (igual que módulos 2–4)."""

from __future__ import annotations

import time
from collections.abc import Callable

import pygetwindow as gw

import config


class GestorVentana:
    """Encuentra la ventana del juego y la pone al frente."""

    def __init__(
        self,
        log: Callable[[str], None] | None = None,
        log_debug: Callable[[str], None] | None = None,
    ) -> None:
        self.ventana_juego = None
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
                    continue
                resultado.append(w)
        return resultado

    def _elegir_por_tamano(self, todas: list):
        minimizadas = [w for w in todas if self._esta_minimizada(w)]
        if minimizadas:
            return minimizadas[0]
        for min_ancho, min_alto in (
            (config.VENTANA_MIN_ANCHO, config.VENTANA_MIN_ALTO),
            (config.VENTANA_MIN_ANCHO_RELAX, config.VENTANA_MIN_ALTO_RELAX),
        ):
            candidatos = [w for w in todas if self._tamano_ok(w, min_ancho, min_alto)]
            if candidatos:
                return max(candidatos, key=lambda x: x.width * x.height)
        return None

    def _asignar_ventana(self, w, *, silencioso: bool) -> None:
        self.ventana_juego = w
        if silencioso:
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
        if elegida is None and not silencioso:
            self._log("No encontré el juego abierto.")
            self._log("Déjalo en la barra de tareas (puede estar minimizado).")
            return None
        if elegida is not None:
            self._asignar_ventana(elegida, silencioso=silencioso)
        return elegida

    def _actualizar_tras_restore(self) -> bool:
        titulo = (self.ventana_juego.title or "") if self.ventana_juego else ""
        tokens = (titulo,) if titulo else getattr(config, "TITULOS_VENTANA_PRIORIDAD", ())
        for token in tokens:
            if not token:
                continue
            for w in gw.getWindowsWithTitle(token):
                if self._esta_minimizada(w) or self._es_fantasma(w):
                    continue
                if self._tamano_ok(
                    w, config.VENTANA_MIN_ANCHO_RELAX, config.VENTANA_MIN_ALTO_RELAX
                ):
                    self.ventana_juego = w
                    return True
        return self.buscar_ventana_juego(silencioso=True) is not None

    def activar_ventana(self, *, silencioso: bool = False) -> bool:
        if not self.ventana_juego and not self.buscar_ventana_juego():
            return False
        try:
            w = self.ventana_juego
            if self._esta_minimizada(w):
                if not silencioso:
                    self._log("Levanto el juego…")
                w.restore()
                time.sleep(config.PAUSA_TRAS_RESTAURAR)
                if not self._actualizar_tras_restore():
                    return False
                w = self.ventana_juego
            w.activate()
            time.sleep(config.PAUSA_TRAS_ACTIVAR)
            if not silencioso:
                self._log("✓ Juego al frente")
            return True
        except Exception as e:
            self._log("No pude poner el juego al frente.")
            self._log_debug(str(e))
            return False
