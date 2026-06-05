"""
Ventana de calibración en dos pasos (juego + coordenadas).
Solo la usan módulos que la importen explícitamente (p. ej. módulo 4).
No modifica calibrar_zona_al_inicio ni los módulos 1–3.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.messagebox as tkmsg
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .zona_pantalla import (
    cargar_zona_captura_json,
    guardar_zona_captura_json,
    ocultar_ventana_para_selector,
    restaurar_ventana_tras_selector,
    seleccionar_rectangulo_pantalla,
)

# Paleta oscura (alineada con el selector de zona verde)
_C = {
    "fondo": "#0f0f14",
    "tarjeta": "#1a1a26",
    "borde": "#2d2d42",
    "texto": "#ececf4",
    "suave": "#9494b0",
    "acento": "#00e5a8",
    "acento_oscuro": "#00b88a",
    "boton": "#252538",
    "boton_hover": "#32324a",
    "ok": "#3dffa8",
    "pendiente": "#6b6b85",
    "iniciar_off": "#3a3a52",
}


@dataclass
class ResultadoCalibracionDoble:
    cancelado: bool = True
    zona_juego: Optional[tuple[int, int, int, int]] = None
    zona_ocr: Optional[tuple[int, int, int, int]] = None


def aplicar_zona_ocr_en_config(
    config_mod,
    rect: tuple[int, int, int, int],
) -> None:
    left, top, w, h = rect
    config_mod.OCR_IZQUIERDA = left
    config_mod.OCR_SUPERIOR = top
    config_mod.OCR_ANCHO = w
    config_mod.OCR_ALTO = h


def _rect_dentro_de(
    interior: tuple[int, int, int, int],
    exterior: tuple[int, int, int, int],
) -> bool:
    ix, iy, iw, ih = interior
    ex, ey, ew, eh = exterior
    return ix >= ex and iy >= ey and (ix + iw) <= (ex + ew) and (iy + ih) <= (ey + eh)


def _interseccion_rect(
    a: tuple[int, int, int, int],
    b: tuple[int, int, int, int],
) -> Optional[tuple[int, int, int, int]]:
    """Solape de dos rectángulos (left, top, width, height) o None si no se tocan."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)
    w, h = right - left, bottom - top
    if w < 1 or h < 1:
        return None
    return (left, top, w, h)


def _ajustar_zona_ocr_a_juego(
    rect_ocr: tuple[int, int, int, int],
    rect_juego: tuple[int, int, int, int],
    *,
    min_ancho: int = 20,
    min_alto: int = 20,
) -> tuple[Optional[tuple[int, int, int, int]], str]:
    """
    Recorta el rectángulo de coordenadas a la zona del juego.
    Devuelve (rect_final, motivo): ok | recortado | sin_solape | demasiado_pequeño.
    """
    if _rect_dentro_de(rect_ocr, rect_juego):
        return rect_ocr, "ok"
    inter = _interseccion_rect(rect_ocr, rect_juego)
    if inter is None:
        return None, "sin_solape"
    _, _, iw, ih = inter
    if iw < min_ancho or ih < min_alto:
        return None, "demasiado_pequeño"
    return inter, "recortado"


def _fmt_rect(rect: tuple[int, int, int, int]) -> str:
    left, top, w, h = rect
    return f"{w}×{h} px @ ({left}, {top})"


class _BotonEstilo(tk.Frame):
    def __init__(
        self,
        master,
        texto: str,
        comando,
        *,
        secundario: bool = False,
        **kw,
    ):
        super().__init__(master, bg=_C["tarjeta"], **kw)
        self._comando = comando
        self._secundario = secundario
        self._hover = False
        bg = _C["boton"] if secundario else _C["borde"]
        self._lbl = tk.Label(
            self,
            text=texto,
            font=("Segoe UI", 10),
            fg=_C["texto"],
            bg=bg,
            padx=14,
            pady=11,
            cursor="hand2",
        )
        self._lbl.pack(fill=tk.BOTH, expand=True)
        for w in (self, self._lbl):
            w.bind("<ButtonRelease-1>", self._click)
            w.bind("<Enter>", self._entrar)
            w.bind("<Leave>", self._salir)

    def _click(self, _e=None) -> None:
        if self._comando:
            self._comando()

    def _entrar(self, _e=None) -> None:
        self._hover = True
        self._lbl.configure(bg=_C["boton_hover"])

    def _salir(self, _e=None) -> None:
        self._hover = False
        bg = _C["boton"] if self._secundario else _C["borde"]
        self._lbl.configure(bg=bg)


def mostrar_menu_calibracion_doble(
    *,
    titulo: str = "Calibración",
    subtitulo: str = "Marca las dos zonas y pulsa Iniciar",
    ruta_zona_juego: str | Path,
    ruta_zona_ocr: str | Path,
    log_debug=None,
) -> ResultadoCalibracionDoble:
    """
    Modal: botón juego → dibujar; botón coordenadas → dibujar; Iniciar.
    No reutiliza JSON al abrir: hay que marcar las zonas en cada ejecución.
    """
    ruta_juego = Path(ruta_zona_juego)
    ruta_ocr = Path(ruta_zona_ocr)
    resultado = ResultadoCalibracionDoble(cancelado=True)
    _log_debug = log_debug or (lambda _m: None)

    zona_juego: list[Optional[tuple[int, int, int, int]]] = [None]
    zona_ocr: list[Optional[tuple[int, int, int, int]]] = [None]

    root = tk.Tk()
    root.title(titulo)
    root.configure(bg=_C["fondo"])
    root.resizable(False, False)
    root.attributes("-topmost", True)

    cont = tk.Frame(root, bg=_C["fondo"], padx=22, pady=20)
    cont.pack()

    tk.Label(
        cont,
        text=titulo,
        font=("Segoe UI", 14, "bold"),
        fg=_C["texto"],
        bg=_C["fondo"],
    ).pack(anchor="w")
    tk.Label(
        cont,
        text=subtitulo,
        font=("Segoe UI", 9),
        fg=_C["suave"],
        bg=_C["fondo"],
    ).pack(anchor="w", pady=(4, 16))

    tarjeta = tk.Frame(cont, bg=_C["tarjeta"], padx=16, pady=16, highlightthickness=1,
                     highlightbackground=_C["borde"])
    tarjeta.pack(fill=tk.X)

    estado_juego = tk.StringVar(value="Pendiente")
    estado_ocr = tk.StringVar(value="Pendiente")
    puede_iniciar = [False]

    def _actualizar_estados() -> None:
        if zona_juego[0]:
            estado_juego.set(f"✓  {_fmt_rect(zona_juego[0])}  (vuelve a pulsar para cambiar)")
        else:
            estado_juego.set("Pendiente — pulsa el botón y arrastra")
        if zona_ocr[0]:
            estado_ocr.set(f"✓  {_fmt_rect(zona_ocr[0])}  (vuelve a pulsar para cambiar)")
        else:
            estado_ocr.set("Pendiente — pulsa el botón y arrastra")
        ok = zona_juego[0] is not None and zona_ocr[0] is not None
        puede_iniciar[0] = ok
        btn_iniciar.configure(
            bg=_C["acento"] if ok else _C["iniciar_off"],
            fg="#0a0a10" if ok else _C["suave"],
            cursor="hand2" if ok else "arrow",
        )

    def _dibujar(which: str) -> None:
        nombre = "juego" if which == "juego" else "coordenadas"
        estado_juego.set("Arrastra en pantalla…") if which == "juego" else estado_ocr.set(
            "Arrastra en pantalla…"
        )
        root.update_idletasks()

        hint = (
            "Arrastra el rectángulo sobre TODO el juego · Esc cancelar"
            if which == "juego"
            else "Arrastra solo la franja de coordenadas (-8,-34) · Esc cancelar"
        )
        ocultar_ventana_para_selector(root)
        rect = seleccionar_rectangulo_pantalla(hint=hint, ventana_padre=root)
        restaurar_ventana_tras_selector(root)

        if rect is None:
            _actualizar_estados()
            return
        if which == "juego":
            guardar_zona_captura_json(ruta_juego, rect)
            zona_juego[0] = rect
        else:
            rect_final = rect
            if zona_juego[0]:
                rect_final, motivo = _ajustar_zona_ocr_a_juego(rect, zona_juego[0])
                if motivo in ("sin_solape", "demasiado_pequeño"):
                    tkmsg.showerror(
                        "Fuera del juego",
                        "El recorte de coordenadas no cae sobre la zona del juego.\n"
                        "Marca primero el juego y luego la franja de coordenadas dentro.",
                        parent=root,
                    )
                    _actualizar_estados()
                    return
            guardar_zona_captura_json(ruta_ocr, rect_final)
            zona_ocr[0] = rect_final
        _actualizar_estados()

    # Paso 1
    tk.Label(
        tarjeta,
        text="1 · Zona del juego",
        font=("Segoe UI", 10, "bold"),
        fg=_C["acento"],
        bg=_C["tarjeta"],
    ).pack(anchor="w")
    tk.Label(
        tarjeta,
        textvariable=estado_juego,
        font=("Segoe UI", 9),
        fg=_C["suave"],
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(
        tarjeta,
        "Dibujar zona del juego",
        lambda: _dibujar("juego"),
        secundario=True,
    ).pack(fill=tk.X, pady=(0, 14))

    sep = tk.Frame(tarjeta, height=1, bg=_C["borde"])
    sep.pack(fill=tk.X, pady=(0, 14))

    # Paso 2
    tk.Label(
        tarjeta,
        text="2 · Zona de coordenadas",
        font=("Segoe UI", 10, "bold"),
        fg=_C["acento"],
        bg=_C["tarjeta"],
    ).pack(anchor="w")
    tk.Label(
        tarjeta,
        textvariable=estado_ocr,
        font=("Segoe UI", 9),
        fg=_C["suave"],
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(
        tarjeta,
        "Dibujar zona de coordenadas",
        lambda: _dibujar("ocr"),
        secundario=True,
    ).pack(fill=tk.X)

    pie = tk.Frame(cont, bg=_C["fondo"])
    pie.pack(fill=tk.X, pady=(18, 0))

    btn_iniciar = tk.Label(
        pie,
        text="Iniciar",
        font=("Segoe UI", 11, "bold"),
        bg=_C["iniciar_off"],
        fg=_C["suave"],
        padx=20,
        pady=12,
        cursor="hand2",
    )
    btn_iniciar.pack(fill=tk.X)

    def _iniciar(_e=None) -> None:
        if not puede_iniciar[0]:
            return
        resultado.cancelado = False
        resultado.zona_juego = zona_juego[0]
        resultado.zona_ocr = zona_ocr[0]
        root.destroy()

    def _cancelar() -> None:
        resultado.cancelado = True
        root.destroy()

    btn_iniciar.bind("<Button-1>", _iniciar)
    def _hover_iniciar_entrar(_e=None) -> None:
        if puede_iniciar[0]:
            btn_iniciar.configure(bg=_C["acento_oscuro"])

    def _hover_iniciar_salir(_e=None) -> None:
        if puede_iniciar[0]:
            btn_iniciar.configure(bg=_C["acento"])
        else:
            btn_iniciar.configure(bg=_C["iniciar_off"])

    btn_iniciar.bind("<Enter>", _hover_iniciar_entrar)
    btn_iniciar.bind("<Leave>", _hover_iniciar_salir)

    tk.Label(
        pie,
        text="Esc · cerrar sin iniciar",
        font=("Segoe UI", 8),
        fg=_C["suave"],
        bg=_C["fondo"],
        cursor="hand2",
    ).pack(pady=(10, 0))
    lbl_esc = tk.Label(
        pie,
        text="Cancelar",
        font=("Segoe UI", 9),
        fg=_C["suave"],
        bg=_C["fondo"],
        cursor="hand2",
    )
    lbl_esc.pack(pady=(6, 0))
    lbl_esc.bind("<Button-1>", lambda _e: _cancelar())
    root.bind("<Escape>", lambda _e: _cancelar())

    _actualizar_estados()

    root.update_idletasks()
    rw = root.winfo_reqwidth()
    rh = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{rw}x{rh}+{(sw - rw) // 2}+{(sh - rh) // 2}")

    root.mainloop()
    return resultado
