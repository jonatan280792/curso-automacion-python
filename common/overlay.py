"""
Ventana flotante semitransparente para mostrar logs encima del juego (grabación / demos).
Tkinter en un hilo aparte; los mensajes son thread-safe vía cola.

Uso típico (cualquier módulo):
    from common.overlay import GameLogOverlay
    ov = GameLogOverlay()
    ov.start()
    ov.log("Hola")
    ov.reposition_on_window(ventana_pygetwindow)  # opcional
    ...
    ov.stop()  # o pulsa Esc en la ventana si la dejaste abierta al terminar el script
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import font as tkfont


class GameLogOverlay:
    """Panel de texto siempre visible, posicionable sobre la ventana del emulador."""

    def __init__(
        self,
        *,
        title: str = "Curso — log",
        max_lines: int = 18,
        alpha: float = 0.88,
        rel_x: float = 0.52,
        rel_y: float = 0.08,
        rel_w: float = 0.46,
        rel_h: float = 0.65,
        bg: str = "#1a1a1a",
        fg: str = "#7cfc00",
        font_size: int = 10,
    ) -> None:
        self._title = title
        self._max_lines = max(5, max_lines)
        self._alpha = max(0.3, min(1.0, alpha))
        self._rel_x = rel_x
        self._rel_y = rel_y
        self._rel_w = rel_w
        self._rel_h = rel_h
        self._bg = bg
        self._fg = fg
        self._font_size = font_size

        self._q: queue.Queue[str] = queue.Queue()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self.root: tk.Tk | None = None
        self._text: tk.Text | None = None

    def start(self, *, persist: bool = True) -> None:
        """persist=True: el script puede terminar y la ventana sigue (hilo no daemon). Esc la cierra."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._tk_main,
            name="GameLogOverlay",
            daemon=not persist,
        )
        self._thread.start()
        self._ready.wait(timeout=5.0)

    def set_alpha(self, alpha: float) -> None:
        """Cambia transparencia sin cerrar el panel (evita parpadeo al capturar)."""
        root = self.root
        if root is None:
            return
        a = max(0.02, min(1.0, alpha))

        def _apply() -> None:
            try:
                root.attributes("-alpha", a)
            except tk.TclError:
                pass

        try:
            root.after(0, _apply)
        except tk.TclError:
            pass

    def stop(self) -> None:
        root = self.root
        if root is None:
            return

        def _destroy() -> None:
            try:
                root.destroy()
            except tk.TclError:
                pass

        try:
            root.after(0, _destroy)
        except tk.TclError:
            pass
        self.root = None
        self._text = None

    def log(self, message: str) -> None:
        if not self._ready.is_set():
            return
        self._q.put(message)

    def reposition_on_window(self, window) -> None:
        """Coloca el panel según el rectángulo de pygetwindow (left, top, width, height)."""
        if window is None or self.root is None:
            return
        try:
            self.reposition_on_region(
                int(window.left),
                int(window.top),
                int(window.width),
                int(window.height),
            )
        except Exception:
            pass

    def reposition_on_region(self, left: int, top: int, width: int, height: int) -> None:
        """Coloca el panel según un rectángulo en pantalla (zona calibrada o ventana)."""
        if self.root is None or width < 1 or height < 1:
            return
        try:
            x = left + int(width * self._rel_x)
            y = top + int(height * self._rel_y)
            w = max(160, int(width * self._rel_w))
            h = max(100, int(height * self._rel_h))
        except Exception:
            return

        def _apply() -> None:
            try:
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                self.root.deiconify()
                self.root.lift()
                self.root.attributes("-topmost", True)
            except tk.TclError:
                pass

        try:
            self.root.after(0, _apply)
        except tk.TclError:
            pass

    def show_fallback_center(self) -> None:
        """Si no hay ventana del juego: mostrar el panel centrado en el monitor principal (Tk)."""
        root = self.root
        if root is None:
            return

        def _apply() -> None:
            try:
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                w, h = 420, 280
                root.geometry(f"{w}x{h}+{max(0, sw // 2 - w // 2)}+{max(0, sh // 2 - h // 2)}")
                root.deiconify()
                root.lift()
                root.attributes("-topmost", True)
            except tk.TclError:
                pass

        try:
            root.after(0, _apply)
        except tk.TclError:
            pass

    def _tk_main(self) -> None:
        root = tk.Tk()
        self.root = root
        root.title(self._title)
        root.overrideredirect(True)
        try:
            root.attributes("-topmost", True)
        except tk.TclError:
            pass
        try:
            root.attributes("-alpha", self._alpha)
        except tk.TclError:
            pass

        root.configure(bg=self._bg)

        f = tkfont.Font(family="Consolas", size=self._font_size)
        txt = tk.Text(
            root,
            wrap=tk.WORD,
            bg=self._bg,
            fg=self._fg,
            insertbackground=self._fg,
            relief=tk.FLAT,
            borderwidth=0,
            padx=6,
            pady=6,
            font=f,
            highlightthickness=1,
            highlightbackground="#333333",
            state=tk.DISABLED,
        )
        txt.pack(fill=tk.BOTH, expand=True)
        self._text = txt

        def on_escape(_event=None) -> str:
            try:
                root.destroy()
            except tk.TclError:
                pass
            return "break"

        def refocus(_event=None) -> None:
            try:
                root.focus_set()
            except tk.TclError:
                pass

        root.bind("<Escape>", on_escape)
        txt.bind("<Escape>", on_escape)
        root.bind("<Button-1>", refocus)
        txt.bind("<Button-1>", refocus)

        # Fuera de pantalla hasta reposition_on_window (evita que aparezca en el monitor principal solo)
        root.geometry("400x280+-10000+-10000")
        root.withdraw()

        def _mantener_frente() -> None:
            try:
                root.attributes("-topmost", True)
                root.lift()
            except tk.TclError:
                pass

        _ticks = 0

        def poll() -> None:
            nonlocal _ticks
            try:
                while True:
                    line = self._q.get_nowait()
                    self._append(line)
                    _mantener_frente()
            except queue.Empty:
                pass
            _ticks += 1
            if _ticks % 4 == 0:
                _mantener_frente()
            try:
                root.after(90, poll)
            except tk.TclError:
                pass

        self._ready.set()
        poll()
        try:
            root.mainloop()
        finally:
            self._ready.clear()
            self.root = None
            self._text = None

    def _append(self, line: str) -> None:
        t = self._text
        root = self.root
        if t is None or root is None:
            return
        clean = (line or "").rstrip()
        if not clean:
            clean = " "

        def _do() -> None:
            try:
                t.configure(state=tk.NORMAL)
                t.insert(tk.END, clean + "\n")
                n = int(t.index("end-1c").split(".")[0])
                if n > self._max_lines:
                    t.delete("1.0", f"{n - self._max_lines + 1}.0")
                t.see(tk.END)
                t.configure(state=tk.DISABLED)
                root.attributes("-topmost", True)
                root.lift()
            except tk.TclError:
                pass

        try:
            root.after(0, _do)
        except tk.TclError:
            pass
