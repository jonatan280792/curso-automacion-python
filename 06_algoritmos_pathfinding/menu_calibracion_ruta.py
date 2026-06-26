"""Modal módulo 6: zonas de calibración + mapa mundial (OCR = posición, click = destino)."""

from __future__ import annotations

import json
import tkinter as tk
import tkinter.messagebox as tkmsg
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import config as config_modulo
from common.vista_mapa_mundo import VistaMapaMundo, cargar_mundo_ui
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
class ResultadoCalibracionRuta:
    cancelado: bool = True
    zona_juego: Optional[tuple[int, int, int, int]] = None
    zona_ocr: Optional[tuple[int, int, int, int]] = None
    destino_x: Optional[int] = None
    destino_y: Optional[int] = None


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


def _islas_del_mapa(celdas: dict[tuple[int, int], object]) -> dict[tuple[int, int], int]:
    """Isla = componente conexo de casillas vecinas (sin contar bloqueos)."""
    from collections import deque

    out: dict[tuple[int, int], int] = {}
    cid = 0
    for start in celdas:
        if start in out:
            continue
        cola: deque[tuple[int, int]] = deque([start])
        out[start] = cid
        while cola:
            x, y = cola.popleft()
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                vecino = (x + dx, y + dy)
                if vecino in celdas and vecino not in out:
                    out[vecino] = cid
                    cola.append(vecino)
        cid += 1
    return out


def mostrar_menu_calibracion_ruta(
    *,
    titulo: str = "Módulo 6 — Calibración",
    subtitulo: str = "Marca las dos zonas y elige destino en el mapa",
    ruta_zona_juego: str | Path,
    ruta_zona_ocr: str | Path,
    ruta_mundo_json: str | Path,
    leer_posicion_ocr: Callable[[tuple[int, int, int, int]], tuple[int, int] | None] | None = None,
) -> ResultadoCalibracionRuta:
    ruta_juego = Path(ruta_zona_juego)
    ruta_ocr = Path(ruta_zona_ocr)
    ruta_mundo = Path(ruta_mundo_json)
    resultado = ResultadoCalibracionRuta(cancelado=True)

    zona_juego: list[Optional[tuple[int, int, int, int]]] = [None]
    zona_ocr: list[Optional[tuple[int, int, int, int]]] = [None]
    posicion_actual: list[Optional[tuple[int, int]]] = [None]
    destino_coords: list[Optional[tuple[int, int]]] = [None]
    islas_mapa: dict[tuple[int, int], int] = {}
    lbl_destino: tk.Label | None = None
    puede_iniciar = [False]
    btn_iniciar: tk.Label | None = None
    vista_mapa: VistaMapaMundo | None = None

    root = tk.Tk()
    root.title(titulo)
    root.configure(bg=_C["fondo"])
    root.resizable(True, True)
    root.minsize(920, 640)
    root.attributes("-topmost", True)

    cont = tk.Frame(root, bg=_C["fondo"], padx=22, pady=20)
    cont.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        cont, text=titulo, font=("Segoe UI", 14, "bold"), fg=_C["texto"], bg=_C["fondo"],
    ).pack(anchor="w")
    tk.Label(
        cont, text=subtitulo, font=("Segoe UI", 9), fg=_C["suave"], bg=_C["fondo"],
    ).pack(anchor="w", pady=(4, 14))

    cuerpo = tk.Frame(cont, bg=_C["fondo"])
    cuerpo.pack(fill=tk.BOTH, expand=True)

    col_izq = tk.Frame(cuerpo, bg=_C["fondo"], width=340)
    col_izq.pack(side=tk.LEFT, fill=tk.Y, anchor="n", padx=(0, 16))

    col_der = tk.Frame(cuerpo, bg=_C["fondo"])
    col_der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tarjeta = tk.Frame(
        col_izq, bg=_C["tarjeta"], padx=16, pady=16,
        highlightthickness=1, highlightbackground=_C["borde"],
    )
    tarjeta.pack(fill=tk.X)

    estado_juego = tk.StringVar(value="Pendiente — pulsa el botón y arrastra")
    estado_ocr = tk.StringVar(value="Pendiente — pulsa el botón y arrastra")
    estado_posicion = tk.StringVar(value="Marca la zona de coordenadas (paso 2)")
    estado_destino = tk.StringVar(value="Haz click en el mapa para elegir destino")

    def _misma_isla(a: tuple[int, int], b: tuple[int, int]) -> bool:
        if not islas_mapa:
            return True
        return islas_mapa.get(a) == islas_mapa.get(b)

    def _limpiar_destino() -> None:
        destino_coords[0] = None
        if vista_mapa is not None:
            vista_mapa.establecer_posicion_destino(None)

    def _aplicar_posicion_ocr(coords: tuple[int, int] | None) -> None:
        if coords is None:
            posicion_actual[0] = None
            estado_posicion.set("No pude leer tu posición — revisa la zona OCR")
            if vista_mapa is not None:
                vista_mapa.establecer_posicion_actual(None, centrar=False)
            _actualizar_estados()
            return
        posicion_actual[0] = coords
        estado_posicion.set(f"✓  Estás en: {coords[0]} , {coords[1]}")
        if vista_mapa is not None:
            vista_mapa.establecer_posicion_actual(coords, centrar=True)
        dest = destino_coords[0]
        if dest is not None and not _misma_isla(coords, dest):
            _limpiar_destino()
            estado_destino.set("✗ Otra isla — primero ve ahí en el juego")
            if lbl_destino is not None:
                lbl_destino.configure(fg="#ff6b8a")
        _actualizar_estados()

    def _leer_posicion_desde_ocr() -> None:
        if leer_posicion_ocr is None or zona_ocr[0] is None:
            return
        estado_posicion.set("Leyendo posición…")
        root.update_idletasks()
        _aplicar_posicion_ocr(leer_posicion_ocr(zona_ocr[0]))

    def _al_elegir_destino(celda: tuple[int, int]) -> None:
        origen = posicion_actual[0]
        if origen is not None and not _misma_isla(origen, celda):
            _limpiar_destino()
            estado_destino.set("✗ Otra isla — primero ve ahí en el juego")
            if lbl_destino is not None:
                lbl_destino.configure(fg="#ff6b8a")
            _actualizar_estados()
            return
        destino_coords[0] = celda
        estado_destino.set(f"✓  Ir a: {celda[0]} , {celda[1]}")
        if lbl_destino is not None:
            lbl_destino.configure(fg=_C["acento"])
        if vista_mapa is not None:
            vista_mapa.establecer_posicion_destino(celda)
        _actualizar_estados()

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

        pos = posicion_actual[0]
        if pos is not None:
            estado_posicion.set(f"✓  Estás en: {pos[0]} , {pos[1]}")
        elif zona_ocr[0] is None:
            txt_pos = estado_posicion.get()
            if not txt_pos.startswith("No pude"):
                estado_posicion.set("Marca la zona de coordenadas (paso 2)")

        dest = destino_coords[0]
        if dest is not None:
            estado_destino.set(f"✓  Ir a: {dest[0]} , {dest[1]}")
            if lbl_destino is not None:
                lbl_destino.configure(fg=_C["acento"])
        else:
            txt = estado_destino.get()
            if not txt.startswith("✗"):
                estado_destino.set("Haz click en el mapa para elegir destino")
                if lbl_destino is not None:
                    lbl_destino.configure(fg=_C["acento"])

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
        if which == "ocr":
            pausa_ms = int(getattr(config_modulo, "PAUSA_TRAS_RESTAURAR", 0.35) * 1000)
            root.after(pausa_ms, _leer_posicion_desde_ocr)

    tk.Label(tarjeta, text="1 · Zona del juego", font=("Segoe UI", 10, "bold"), fg=_C["acento"], bg=_C["tarjeta"]).pack(anchor="w")
    tk.Label(tarjeta, textvariable=estado_juego, font=("Segoe UI", 9), fg=_C["suave"], bg=_C["tarjeta"], wraplength=340, justify=tk.LEFT).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(tarjeta, "Dibujar zona del juego", lambda: _dibujar("juego"), secundario=True).pack(fill=tk.X, pady=(0, 14))

    tk.Frame(tarjeta, height=1, bg=_C["borde"]).pack(fill=tk.X, pady=(0, 14))

    tk.Label(tarjeta, text="2 · Zona de coordenadas", font=("Segoe UI", 10, "bold"), fg=_C["acento"], bg=_C["tarjeta"]).pack(anchor="w")
    tk.Label(tarjeta, textvariable=estado_ocr, font=("Segoe UI", 9), fg=_C["suave"], bg=_C["tarjeta"], wraplength=340, justify=tk.LEFT).pack(anchor="w", pady=(2, 8))
    _BotonEstilo(tarjeta, "Dibujar zona de coordenadas", lambda: _dibujar("ocr"), secundario=True).pack(fill=tk.X)

    tk.Frame(tarjeta, height=1, bg=_C["borde"]).pack(fill=tk.X, pady=(14, 14))

    tk.Label(tarjeta, text="3 · Tu posición (OCR)", font=("Segoe UI", 10, "bold"), fg=_C["acento"], bg=_C["tarjeta"]).pack(anchor="w")
    tk.Label(
        tarjeta,
        text="Se detecta al marcar la zona de coordenadas (casilla roja en el mapa).",
        font=("Segoe UI", 8),
        fg=_C["suave"],
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 6))
    tk.Label(
        tarjeta,
        textvariable=estado_posicion,
        font=("Segoe UI", 9),
        fg="#ff6b8a",
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    ).pack(anchor="w", pady=(0, 0))

    tk.Frame(tarjeta, height=1, bg=_C["borde"]).pack(fill=tk.X, pady=(14, 14))

    tk.Label(tarjeta, text="4 · A dónde quieres ir", font=("Segoe UI", 10, "bold"), fg=_C["acento"], bg=_C["tarjeta"]).pack(anchor="w")
    tk.Label(
        tarjeta,
        text="Haz click en una casilla del mapa (verde).",
        font=("Segoe UI", 8),
        fg=_C["suave"],
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    ).pack(anchor="w", pady=(2, 6))
    lbl_destino = tk.Label(
        tarjeta,
        textvariable=estado_destino,
        font=("Segoe UI", 9, "bold"),
        fg=_C["acento"],
        bg=_C["tarjeta"],
        wraplength=340,
        justify=tk.LEFT,
    )
    lbl_destino.pack(anchor="w", pady=(0, 0))

    try:
        if ruta_mundo.is_file():
            celdas_mapa, meta_mapa = cargar_mundo_ui(ruta_mundo)
        else:
            celdas_mapa, meta_mapa = {}, {}
    except (OSError, json.JSONDecodeError, ValueError):
        celdas_mapa, meta_mapa = {}, {}
    islas_mapa = _islas_del_mapa(celdas_mapa)

    tarjeta_mapa = tk.Frame(
        col_der, bg=_C["tarjeta"], padx=12, pady=12,
        highlightthickness=1, highlightbackground=_C["borde"],
    )
    tarjeta_mapa.pack(fill=tk.BOTH, expand=True)
    vista_mapa = VistaMapaMundo(
        tarjeta_mapa,
        celdas_mapa,
        alto_canvas=520,
        ancho_canvas=560,
        meta_celdas=meta_mapa,
        posicion_actual=None,
        posicion_destino=None,
        on_celda_click=_al_elegir_destino,
    )
    vista_mapa.pack(fill=tk.BOTH, expand=True)

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
        if posicion_actual[0] is None:
            tkmsg.showerror(
                "Falta tu posición",
                "Marca la zona de coordenadas (paso 2) para detectar dónde estás.",
                parent=root,
            )
            return
        dest = destino_coords[0]
        if dest is None:
            tkmsg.showerror(
                "Falta el destino",
                "Haz click en el mapa para elegir a dónde quieres ir.",
                parent=root,
            )
            return
        resultado.cancelado = False
        resultado.zona_juego = zona_juego[0]
        resultado.zona_ocr = zona_ocr[0]
        resultado.destino_x, resultado.destino_y = dest
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
    rw = min(max(root.winfo_reqwidth(), 920), root.winfo_screenwidth() - 40)
    rh = min(max(root.winfo_reqheight(), 640), root.winfo_screenheight() - 40)
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{rw}x{rh}+{(sw - rw) // 2}+{(sh - rh) // 2}")

    root.mainloop()
    return resultado


__all__ = ["ResultadoCalibracionRuta", "mostrar_menu_calibracion_ruta"]
