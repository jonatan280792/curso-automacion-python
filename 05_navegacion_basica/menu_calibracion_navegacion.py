"""
Modal del módulo 5: juego + coordenadas + editor de ruta (flechas y click).
No toca menu_calibracion_doble.py (módulo 4).
"""

from __future__ import annotations

import tkinter as tk
import tkinter.messagebox as tkmsg
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from common.editor_ruta import EditorRuta, formatear_ruta
from common.menu_calibracion_doble import aplicar_zona_ocr_en_config
from common.zona_pantalla import (
    guardar_zona_captura_json,
    ocultar_ventana_para_selector,
    restaurar_ventana_tras_selector,
    seleccionar_rectangulo_pantalla,
)

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
    "iniciar_off": "#3a3a52",
}


@dataclass
class ResultadoCalibracionNavegacion:
    cancelado: bool = True
    zona_juego: Optional[tuple[int, int, int, int]] = None
    zona_ocr: Optional[tuple[int, int, int, int]] = None
    pasos: list[str] = field(default_factory=list)


def _fmt_rect(rect: tuple[int, int, int, int]) -> str:
    left, top, w, h = rect
    return f"{w}×{h} px @ ({left}, {top})"


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
    if _rect_dentro_de(rect_ocr, rect_juego):
        return rect_ocr, "ok"
    inter = _interseccion_rect(rect_ocr, rect_juego)
    if inter is None:
        return None, "sin_solape"
    _, _, iw, ih = inter
    if iw < min_ancho or ih < min_alto:
        return None, "demasiado_pequeño"
    return inter, "recortado"


class _BotonEstilo(tk.Frame):
    def __init__(self, master, texto: str, comando, *, secundario: bool = False, **kw):
        super().__init__(master, bg=_C["tarjeta"], **kw)
        self._comando = comando
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
            w.bind("<Enter>", lambda _e: self._lbl.configure(bg=_C["boton_hover"]))
            w.bind("<Leave>", lambda _e: self._lbl.configure(bg=bg))

    def _click(self, _e=None) -> None:
        if self._comando:
            self._comando()


def mostrar_menu_calibracion_navegacion(
    *,
    titulo: str = "Módulo 5 — Calibración",
    subtitulo: str = "Marca las zonas y arma tu ruta con las flechas",
    ruta_zona_juego: str | Path,
    ruta_zona_ocr: str | Path,
    ruta_ejemplo: str = "",
) -> ResultadoCalibracionNavegacion:
    ruta_juego = Path(ruta_zona_juego)
    ruta_ocr = Path(ruta_zona_ocr)
    resultado = ResultadoCalibracionNavegacion(cancelado=True)

    zona_juego: list[Optional[tuple[int, int, int, int]]] = [None]
    zona_ocr: list[Optional[tuple[int, int, int, int]]] = [None]
    puede_iniciar = [False]
    btn_iniciar: tk.Label | None = None
    editor: EditorRuta | None = None

    root = tk.Tk()
    root.title(titulo)
    root.configure(bg=_C["fondo"])
    root.resizable(False, False)
    root.attributes("-topmost", True)

    cont = tk.Frame(root, bg=_C["fondo"], padx=22, pady=20)
    cont.pack()

    tk.Label(
        cont, text=titulo, font=("Segoe UI", 14, "bold"), fg=_C["texto"], bg=_C["fondo"],
    ).pack(anchor="w")
    tk.Label(
        cont, text=subtitulo, font=("Segoe UI", 9), fg=_C["suave"], bg=_C["fondo"],
    ).pack(anchor="w", pady=(4, 16))

    tarjeta = tk.Frame(
        cont, bg=_C["tarjeta"], padx=16, pady=16,
        highlightthickness=1, highlightbackground=_C["borde"],
    )
    tarjeta.pack(fill=tk.X)

    estado_juego = tk.StringVar(value="Pendiente")
    estado_ocr = tk.StringVar(value="Pendiente")
    estado_ruta = tk.StringVar(value="Pendiente — pulsa flechas o escribe la ruta")

    def _actualizar_estados() -> None:
        if zona_juego[0]:
            estado_juego.set(f"✓  {_fmt_rect(zona_juego[0])}  (vuelve a pulsar para cambiar)")
        else:
            estado_juego.set("Pendiente — pulsa el botón y arrastra")
        if zona_ocr[0]:
            estado_ocr.set(f"✓  {_fmt_rect(zona_ocr[0])}  (vuelve a pulsar para cambiar)")
        else:
            estado_ocr.set("Pendiente — pulsa el botón y arrastra")

        pasos = editor.obtener_pasos() if editor else None
        n = len(pasos) if pasos else 0
        if n > 0:
            estado_ruta.set(f"✓  {n} paso(s): {formatear_ruta(pasos)}")
        else:
            estado_ruta.set("Pendiente — pulsa flechas (● = click en el mapa)")

        ok = zona_juego[0] is not None and zona_ocr[0] is not None and n > 0
        puede_iniciar[0] = ok
        if btn_iniciar is not None:
            btn_iniciar.configure(
                bg=_C["acento"] if ok else _C["iniciar_off"],
                fg="#0a0a10" if ok else _C["suave"],
                cursor="hand2" if ok else "arrow",
            )

    def _dibujar(which: str) -> None:
        if which == "juego":
            estado_juego.set("Arrastra en pantalla…")
        else:
            estado_ocr.set("Arrastra en pantalla…")
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

    tk.Label(
        tarjeta, text="1 · Zona del juego", font=("Segoe UI", 10, "bold"),
        fg=_C["acento"], bg=_C["tarjeta"],
    ).pack(anchor="w")
    tk.Label(
        tarjeta, textvariable=estado_juego, font=("Segoe UI", 9), fg=_C["suave"],
        bg=_C["tarjeta"], wraplength=380, justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(tarjeta, "Dibujar zona del juego", lambda: _dibujar("juego"), secundario=True).pack(
        fill=tk.X, pady=(0, 14),
    )

    tk.Frame(tarjeta, height=1, bg=_C["borde"]).pack(fill=tk.X, pady=(0, 14))

    tk.Label(
        tarjeta, text="2 · Zona de coordenadas", font=("Segoe UI", 10, "bold"),
        fg=_C["acento"], bg=_C["tarjeta"],
    ).pack(anchor="w")
    tk.Label(
        tarjeta, textvariable=estado_ocr, font=("Segoe UI", 9), fg=_C["suave"],
        bg=_C["tarjeta"], wraplength=380, justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(tarjeta, "Dibujar zona de coordenadas", lambda: _dibujar("ocr"), secundario=True).pack(
        fill=tk.X,
    )

    tk.Frame(tarjeta, height=1, bg=_C["borde"]).pack(fill=tk.X, pady=(14, 14))

    tk.Label(
        tarjeta, text="3 · Tu ruta", font=("Segoe UI", 10, "bold"),
        fg=_C["acento"], bg=_C["tarjeta"],
    ).pack(anchor="w")
    tk.Label(
        tarjeta, textvariable=estado_ruta, font=("Segoe UI", 9), fg=_C["suave"],
        bg=_C["tarjeta"], wraplength=380, justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 8))

    editor = EditorRuta(tarjeta, on_change=_actualizar_estados)
    editor.pack(fill=tk.X)
    if ruta_ejemplo.strip():
        editor.establecer_desde_texto(ruta_ejemplo.strip())

    pie = tk.Frame(cont, bg=_C["fondo"])
    pie.pack(fill=tk.X, pady=(18, 0))

    btn_iniciar = tk.Label(
        pie,
        text="Iniciar recorrido",
        font=("Segoe UI", 11, "bold"),
        bg=_C["iniciar_off"],
        fg=_C["suave"],
        padx=20,
        pady=12,
        cursor="hand2",
    )
    btn_iniciar.pack(fill=tk.X)

    def _iniciar(_e=None) -> None:
        if not puede_iniciar[0] or editor is None:
            return
        pasos = editor.obtener_pasos()
        if not pasos:
            tkmsg.showerror(
                "Ruta vacía",
                "Añade al menos un paso con las flechas o escribe la ruta en la caja.",
                parent=root,
            )
            return
        resultado.cancelado = False
        resultado.zona_juego = zona_juego[0]
        resultado.zona_ocr = zona_ocr[0]
        resultado.pasos = pasos
        root.destroy()

    def _cancelar() -> None:
        resultado.cancelado = True
        root.destroy()

    btn_iniciar.bind("<Button-1>", _iniciar)
    btn_iniciar.bind("<Enter>", lambda _e: btn_iniciar.configure(bg=_C["acento_oscuro"]) if puede_iniciar[0] else None)
    btn_iniciar.bind("<Leave>", lambda _e: btn_iniciar.configure(bg=_C["acento"] if puede_iniciar[0] else _C["iniciar_off"]))

    tk.Label(pie, text="Esc · cerrar sin iniciar", font=("Segoe UI", 8), fg=_C["suave"], bg=_C["fondo"]).pack(pady=(10, 0))
    lbl_esc = tk.Label(pie, text="Cancelar", font=("Segoe UI", 9), fg=_C["suave"], bg=_C["fondo"], cursor="hand2")
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


__all__ = [
    "ResultadoCalibracionNavegacion",
    "aplicar_zona_ocr_en_config",
    "mostrar_menu_calibracion_navegacion",
]
