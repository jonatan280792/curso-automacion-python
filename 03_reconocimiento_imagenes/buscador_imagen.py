#!/usr/bin/env python3
"""Buscar plantillas PNG dentro de la zona o ventana (captura con mss, como módulos 1-2)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pyautogui as pg
from PIL import Image

import config
from common.zona_pantalla import capturar_pantalla_en_zona

if TYPE_CHECKING:
    from window_manager import GestorVentana


def _pil_a_bgr(img: Image.Image) -> np.ndarray:
    if img.mode == "RGBA":
        fondo = Image.new("RGB", img.size, (32, 32, 32))
        fondo.paste(img, mask=img.split()[3])
        img = fondo
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


class BuscadorImagen:
    """Localiza imágenes pequeñas (plantillas) en una región de pantalla."""

    def __init__(
        self,
        log: Callable[[str], None] | None = None,
        log_debug: Callable[[str], None] | None = None,
    ) -> None:
        self._log = log or print
        self._log_debug = log_debug or (lambda _m: None)
        self.ultima_posicion: tuple[int, int] | None = None
        self.ultima_confianza: float | None = None

    def ruta_plantilla(self, nombre: str) -> str:
        return os.path.join(config.CARPETA_PLANTILLAS, f"{nombre}.png")

    def region_busqueda(self, gestor: GestorVentana | None) -> tuple[int, int, int, int] | None:
        modo = getattr(config, "BUSCAR_EN", "zona").lower()

        if modo == "ventana":
            if not gestor or not gestor.ventana_juego:
                return None
            w = gestor.ventana_juego
            return int(w.left), int(w.top), max(1, int(w.width)), max(1, int(w.height))

        izq = int(config.ZONA_IZQUIERDA)
        sup = int(config.ZONA_SUPERIOR)
        ancho = max(1, int(config.ZONA_ANCHO))
        alto = max(1, int(config.ZONA_ALTO))
        if ancho < 4 or alto < 4:
            return None
        return izq, sup, ancho, alto

    def buscar(
        self,
        ruta_plantilla: str,
        region: tuple[int, int, int, int],
        *,
        confianza: float | None = None,
    ) -> tuple[int, int] | None:
        if not os.path.isfile(ruta_plantilla):
            self._log_debug(f"plantilla no existe: {ruta_plantilla}")
            return None

        conf = confianza if confianza is not None else config.CONFIANZA_BUSQUEDA
        izq, sup, ancho, alto = region

        try:
            pantalla = _pil_a_bgr(capturar_pantalla_en_zona(izq, sup, ancho, alto))
            plantilla = _pil_a_bgr(Image.open(ruta_plantilla))
        except Exception as e:
            self._log_debug(f"error captura: {e}")
            return None

        th, tw = plantilla.shape[:2]
        ph, pw = pantalla.shape[:2]
        if th > ph or tw > pw:
            self._log_debug(f"plantilla {tw}x{th} mayor que región {pw}x{ph}")
            return None

        resultado = cv2.matchTemplate(pantalla, plantilla, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(resultado)
        self.ultima_confianza = float(max_val)
        self._log_debug(f"mejor coincidencia: {max_val:.3f} (umbral {conf})")

        if max_val < conf:
            self.ultima_posicion = None
            return None

        pos = (izq + max_loc[0] + tw // 2, sup + max_loc[1] + th // 2)
        self.ultima_posicion = pos
        self._log_debug(f"encontrado {os.path.basename(ruta_plantilla)} en {pos}")
        return pos

    def clic_en(self, posicion: tuple[int, int]) -> bool:
        try:
            pg.click(posicion[0], posicion[1])
            return True
        except Exception as e:
            self._log_debug(f"clic fallido: {e}")
            return False


ImageFinder = BuscadorImagen
