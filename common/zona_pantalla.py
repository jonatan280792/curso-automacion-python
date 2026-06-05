"""
Calibración de zona rectangular en pantalla (multi-monitor vía mss).
Menú básico + arrastre para definir la región de una captura final.

Requiere: mss, tkinter (stdlib en Windows con Python oficial).
"""

from __future__ import annotations

import json
import tkinter as tk
import tkinter.messagebox as tkmsg
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mss
from PIL import Image


@dataclass
class EleccionCaptura:
    """Resultado del menú / calibración para usar en guardar_captura."""

    cancelado: bool = False
    usar_region_pantalla: bool = False
    region: Optional[tuple[int, int, int, int]] = None  # left, top, width, height


def _monitor_virtual() -> dict:
    with mss.MSS() as sct:
        return dict(sct.monitors[0])


def cargar_zona_captura_json(path: str | Path) -> Optional[tuple[int, int, int, int]]:
    p = Path(path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        t = (
            int(data["left"]),
            int(data["top"]),
            int(data["width"]),
            int(data["height"]),
        )
        if t[2] < 4 or t[3] < 4:
            return None
        return t
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def capturar_pantalla_en_zona(
    left: int,
    top: int,
    width: int,
    height: int,
) -> Image.Image:
    """
    Captura un rectángulo de pantalla con mss (multi-monitor y coords. negativas).
    PyAutoGUI a veces devuelve imagen negra en el monitor secundario; mss coincide
    con la calibración de seleccionar_rectangulo_pantalla.
    """
    region = {
        "left": int(left),
        "top": int(top),
        "width": max(1, int(width)),
        "height": max(1, int(height)),
    }
    with mss.mss() as sct:
        shot = sct.grab(region)
    return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def describir_zona(rect: tuple[int, int, int, int]) -> str:
    """Texto corto para logs (consola / overlay)."""
    left, top, w, h = rect
    mon = _monitor_virtual()
    return (
        f"zona pantalla: esquina ({left}, {top}), tamaño {w} x {h} px "
        f"(escritorio virtual mss: {mon['width']}x{mon['height']}, origen {mon['left']},{mon['top']})"
    )


def guardar_zona_captura_json(path: str | Path, rect: tuple[int, int, int, int]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    left, top, w, h = rect
    payload = {"left": left, "top": top, "width": w, "height": h, "version": 1}
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seleccionar_rectangulo_pantalla(
    hint: str = "Arrastra un rectángulo sobre la zona a capturar · Esc cancelar",
    ventana_padre: tk.Misc | None = None,
) -> Optional[tuple[int, int, int, int]]:
    """
    Pantalla virtual completa semitransparente: arrastra con el botón izquierdo.
    Suelta para confirmar. Esc = cancelar.
    Devuelve (left, top, width, height) en coordenadas de pantalla o None.

    Si ventana_padre está definida (p. ej. modal de calibración), usa Toplevel
    y no crea un segundo Tk (evita que el menú no vuelva en Windows).
    """
    mon = _monitor_virtual()
    vl, vt, vw, vh = mon["left"], mon["top"], mon["width"], mon["height"]

    resultado: list[Optional[tuple[int, int, int, int]]] = [None]
    inicio: list[tuple[int, int]] = [(0, 0)]

    if ventana_padre is not None:
        overlay = tk.Toplevel(ventana_padre)
        usar_wait_window = True
    else:
        overlay = tk.Tk()
        usar_wait_window = False
    overlay.title("Seleccionar zona")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.geometry(f"{vw}x{vh}+{vl}+{vt}")
    try:
        overlay.attributes("-alpha", 0.28)
    except tk.TclError:
        pass

    canvas = tk.Canvas(overlay, highlightthickness=0, bg="#000044", cursor="crosshair")
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_text(
        16,
        12,
        anchor="nw",
        fill="#ffffff",
        font=("Segoe UI", 11),
        text=hint,
    )
    rect_id: list[Optional[int]] = [None]

    def a_pantalla(ex: int, ey: int) -> tuple[int, int]:
        return vl + ex, vt + ey

    def en_pantalla(sx: int, sy: int) -> tuple[int, int]:
        return sx - vl, sy - vt

    def empezar(e: tk.Event) -> None:
        inicio[0] = a_pantalla(e.x, e.y)

    def arrastrar(e: tk.Event) -> None:
        x0, y0 = inicio[0]
        x1, y1 = a_pantalla(e.x, e.y)
        xa, xb = min(x0, x1), max(x0, x1)
        ya, yb = min(y0, y1), max(y0, y1)
        if rect_id[0] is not None:
            canvas.delete(rect_id[0])
        rect_id[0] = canvas.create_rectangle(
            *en_pantalla(xa, ya),
            *en_pantalla(xb, yb),
            outline="#00ff88",
            width=2,
        )

    def terminar(e: tk.Event) -> None:
        x0, y0 = inicio[0]
        x1, y1 = a_pantalla(e.x, e.y)
        left, right = min(x0, x1), max(x0, x1)
        top, bottom = min(y0, y1), max(y0, y1)
        w, h = right - left, bottom - top
        if w >= 20 and h >= 20:
            resultado[0] = (left, top, w, h)
        overlay.destroy()

    def cancelar(_: tk.Event | None = None) -> None:
        resultado[0] = None
        overlay.destroy()

    canvas.bind("<ButtonPress-1>", empezar)
    canvas.bind("<B1-Motion>", arrastrar)
    canvas.bind("<ButtonRelease-1>", terminar)
    overlay.bind("<Escape>", cancelar)

    overlay.update_idletasks()
    try:
        overlay.grab_set_global()  # type: ignore[attr-defined]
    except (tk.TclError, AttributeError):
        try:
            overlay.grab_set()
        except tk.TclError:
            pass
    overlay.lift()
    overlay.focus_force()
    if usar_wait_window:
        ventana_padre.wait_window(overlay)
    else:
        overlay.mainloop()
    return resultado[0]


def ocultar_ventana_para_selector(ventana: tk.Misc) -> None:
    """Oculta sin withdraw (en Windows withdraw rompe el Toplevel hijo)."""
    try:
        ventana.attributes("-alpha", 0.0)
    except tk.TclError:
        ventana.withdraw()
    ventana.update_idletasks()


def restaurar_ventana_tras_selector(ventana: tk.Misc) -> None:
    try:
        ventana.attributes("-alpha", 1.0)
    except tk.TclError:
        ventana.deiconify()
    try:
        ventana.attributes("-topmost", True)
    except tk.TclError:
        pass
    ventana.lift()
    ventana.focus_force()
    ventana.update_idletasks()


def aplicar_zona_en_config(
    config_mod,
    rect: tuple[int, int, int, int],
) -> None:
    """Copia la zona al módulo config (ZONA_IZQUIERDA, ZONA_SUPERIOR, etc.)."""
    left, top, w, h = rect
    config_mod.ZONA_IZQUIERDA = left
    config_mod.ZONA_SUPERIOR = top
    config_mod.ZONA_ANCHO = w
    config_mod.ZONA_ALTO = h


def calibrar_zona_al_inicio(ruta_zona_json: str | Path) -> Optional[tuple[int, int, int, int]]:
    """
    Paso obligatorio: pantalla semitransparente, arrastras el rectángulo del juego.
    Guarda en JSON. None si el usuario pulsa Esc o el rectángulo es demasiado pequeño.
    """
    print()
    print("  Marca la zona del juego en pantalla.")
    print("  Arrastra un rectángulo · Esc para salir sin continuar")
    print()
    rect = seleccionar_rectangulo_pantalla()
    if rect is None:
        return None
    guardar_zona_captura_json(ruta_zona_json, rect)
    print("  ✓ Zona guardada. En un momento empieza el programa.")
    print()
    return rect


def menu_captura_basico(ruta_zona_json: str | Path) -> EleccionCaptura:
    """Menú pequeño: ventana del juego, dibujar zona, usar JSON guardado o cancelar."""
    ruta = Path(ruta_zona_json)
    eleccion = EleccionCaptura(cancelado=True)

    root = tk.Tk()
    root.title("Captura — módulo 1")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    fr = tk.Frame(root, padx=14, pady=14)
    fr.pack()

    tk.Label(
        fr,
        text="¿Cómo quieres la foto final?",
        font=("Segoe UI", 11, "bold"),
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

    def solo_ventana() -> None:
        eleccion.cancelado = False
        eleccion.usar_region_pantalla = False
        eleccion.region = None
        root.destroy()

    def dibujar_zona() -> None:
        ocultar_ventana_para_selector(root)
        rect = seleccionar_rectangulo_pantalla(ventana_padre=root)
        restaurar_ventana_tras_selector(root)
        if rect:
            guardar_zona_captura_json(ruta, rect)
            eleccion.cancelado = False
            eleccion.usar_region_pantalla = True
            eleccion.region = rect
            root.destroy()

    def usar_guardada() -> None:
        rect = cargar_zona_captura_json(ruta)
        if rect is None:
            tkmsg.showwarning(
                "Zona guardada",
                f"No hay archivo válido:\n{ruta}\n\nElige otra opción.",
                parent=root,
            )
            return
        eleccion.cancelado = False
        eleccion.usar_region_pantalla = True
        eleccion.region = rect
        root.destroy()

    def cancelar() -> None:
        eleccion.cancelado = True
        root.destroy()

    tk.Button(fr, text="Solo ventana del juego", width=28, command=solo_ventana).grid(
        row=1, column=0, columnspan=2, pady=2, sticky="ew"
    )
    tk.Button(
        fr,
        text="Dibujar zona en pantalla (y guardar)",
        width=28,
        command=dibujar_zona,
    ).grid(row=2, column=0, columnspan=2, pady=2, sticky="ew")
    existe = ruta.is_file()
    tk.Button(
        fr,
        text="Usar zona guardada (archivo)",
        width=28,
        command=usar_guardada,
        state=tk.NORMAL if existe else tk.DISABLED,
    ).grid(row=3, column=0, columnspan=2, pady=2, sticky="ew")
    tk.Button(fr, text="Cancelar", width=28, command=cancelar).grid(
        row=4, column=0, columnspan=2, pady=(10, 0), sticky="ew"
    )

    root.update_idletasks()
    rw = root.winfo_reqwidth()
    rh = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw - rw) // 2}+{(sh - rh) // 2}")

    root.mainloop()
    return eleccion


__all__ = [
    "EleccionCaptura",
    "aplicar_zona_en_config",
    "calibrar_zona_al_inicio",
    "capturar_pantalla_en_zona",
    "describir_zona",
    "menu_captura_basico",
    "seleccionar_rectangulo_pantalla",
    "guardar_zona_captura_json",
    "cargar_zona_captura_json",
    "ocultar_ventana_para_selector",
    "restaurar_ventana_tras_selector",
]
