"""
Editor de ruta con flechas y click (reutilizable en módulos de navegación).
"""

from __future__ import annotations

import re
import tkinter as tk
from typing import Callable

# Paleta alineada con menu_calibracion_doble / menu_calibracion_ruta
_C = {
    "tarjeta": "#1a1a26",
    "borde": "#2d2d42",
    "texto": "#ececf4",
    "suave": "#9494b0",
    "acento": "#00e5a8",
    "boton": "#252538",
    "boton_hover": "#32324a",
    "flecha": "#2a2a40",
    "flecha_hover": "#3d3d58",
    "click": "#3a2848",
    "click_hover": "#4a3558",
}

_TOKEN_A_ES = {
    "up": "arriba",
    "down": "abajo",
    "left": "izquierda",
    "right": "derecha",
    "click": "click",
}

_ES_A_TOKEN = {
    "arriba": "up",
    "abajo": "down",
    "izquierda": "left",
    "derecha": "right",
    "click": "click",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
}

PASOS_VALIDOS = frozenset(_TOKEN_A_ES)


def token_a_etiqueta(token: str) -> str:
    return _TOKEN_A_ES.get(token.strip().lower(), token)


def etiqueta_a_token(etiqueta: str) -> str | None:
    return _ES_A_TOKEN.get(etiqueta.strip().lower())


def formatear_ruta(pasos: list[str]) -> str:
    if not pasos:
        return ""
    return " → ".join(token_a_etiqueta(p) for p in pasos)


def parsear_ruta_texto(texto: str) -> list[str] | None:
    """Convierte texto libre (flechas en UI o escrito a mano) en lista de tokens."""
    t = texto.strip()
    if not t:
        return None
    partes = re.split(r"\s*(?:→|,|/|\|)\s*|\s+", t)
    pasos: list[str] = []
    for parte in partes:
        p = parte.strip()
        if not p:
            continue
        token = etiqueta_a_token(p)
        if token is None:
            return None
        pasos.append(token)
    return pasos or None


class EditorRuta(tk.Frame):
    """Cuadrícula de flechas + click y caja de texto con la ruta."""

    def __init__(
        self,
        master,
        *,
        on_change: Callable[[], None] | None = None,
        ancho_texto: int = 42,
        **kw,
    ):
        super().__init__(master, bg=_C["tarjeta"], **kw)
        self._on_change = on_change
        self._pasos: list[str] = []

        rejilla = tk.Frame(self, bg=_C["tarjeta"])
        rejilla.pack(pady=(0, 10))

        self._btn_up = self._boton_flecha(rejilla, "▲", "up", fila=0, col=1)
        self._btn_left = self._boton_flecha(rejilla, "◀", "left", fila=1, col=0)
        self._btn_click = self._boton_flecha(
            rejilla, "●", "click", fila=1, col=1, es_click=True, hint="Click en el mapa",
        )
        self._btn_right = self._boton_flecha(rejilla, "▶", "right", fila=1, col=2)
        self._btn_down = self._boton_flecha(rejilla, "▼", "down", fila=2, col=1)

        tk.Label(
            self,
            text="Ruta (también puedes editar el texto)",
            font=("Segoe UI", 9),
            fg=_C["suave"],
            bg=_C["tarjeta"],
        ).pack(anchor="w")

        self._entry = tk.Text(
            self,
            height=3,
            width=ancho_texto,
            font=("Segoe UI", 10),
            bg=_C["boton"],
            fg=_C["texto"],
            insertbackground=_C["texto"],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=_C["borde"],
            highlightcolor=_C["acento"],
            wrap=tk.WORD,
        )
        self._entry.pack(fill=tk.X, pady=(4, 8))
        self._entry.bind("<KeyRelease>", lambda _e: self._notificar())

        fila_acc = tk.Frame(self, bg=_C["tarjeta"])
        fila_acc.pack(fill=tk.X)

        for texto, cmd in (("Deshacer último", self.deshacer), ("Limpiar", self.limpiar)):
            lbl = tk.Label(
                fila_acc,
                text=texto,
                font=("Segoe UI", 9),
                fg=_C["suave"],
                bg=_C["tarjeta"],
                cursor="hand2",
                padx=4,
            )
            lbl.pack(side=tk.LEFT, padx=(0, 12))
            lbl.bind("<Button-1>", lambda _e, c=cmd: c())
            lbl.bind("<Enter>", lambda _e, w=lbl: w.configure(fg=_C["acento"]))
            lbl.bind("<Leave>", lambda _e, w=lbl: w.configure(fg=_C["suave"]))

    def _boton_flecha(
        self,
        master,
        simbolo: str,
        token: str,
        *,
        fila: int,
        col: int,
        es_click: bool = False,
        hint: str = "",
    ) -> tk.Label:
        bg = _C["click"] if es_click else _C["flecha"]
        hover = _C["click_hover"] if es_click else _C["flecha_hover"]
        lbl = tk.Label(
            master,
            text=simbolo,
            font=("Segoe UI", 14, "bold"),
            fg=_C["acento"] if es_click else _C["texto"],
            bg=bg,
            width=3,
            height=1,
            cursor="hand2",
        )
        lbl.grid(row=fila, column=col, padx=4, pady=4)

        def _agregar(_e=None) -> None:
            self.agregar(token)

        lbl.bind("<Button-1>", _agregar)
        lbl.bind("<Enter>", lambda _e: lbl.configure(bg=hover))
        lbl.bind("<Leave>", lambda _e: lbl.configure(bg=bg))
        if hint:
            lbl.bind("<Enter>", lambda _e: lbl.configure(bg=hover))
        return lbl

    def _sincronizar_texto(self) -> None:
        self._entry.delete("1.0", tk.END)
        self._entry.insert("1.0", formatear_ruta(self._pasos))

    def _notificar(self) -> None:
        if self._on_change:
            self._on_change()

    def agregar(self, token: str) -> None:
        t = token.strip().lower()
        if t not in PASOS_VALIDOS:
            return
        self._pasos.append(t)
        self._sincronizar_texto()
        self._notificar()

    def deshacer(self) -> None:
        if self._pasos:
            self._pasos.pop()
            self._sincronizar_texto()
            self._notificar()

    def limpiar(self) -> None:
        self._pasos.clear()
        self._entry.delete("1.0", tk.END)
        self._notificar()

    def establecer_desde_texto(self, texto: str) -> bool:
        pasos = parsear_ruta_texto(texto)
        if pasos is None:
            return False
        self._pasos = pasos
        self._sincronizar_texto()
        self._notificar()
        return True

    def obtener_pasos(self) -> list[str] | None:
        """Lee la caja de texto y devuelve tokens válidos, o None si está vacía o mal escrita."""
        texto = self._entry.get("1.0", tk.END)
        return parsear_ruta_texto(texto)

    def cantidad_pasos(self) -> int:
        pasos = self.obtener_pasos()
        return len(pasos) if pasos else 0
