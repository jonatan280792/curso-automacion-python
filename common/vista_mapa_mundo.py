"""
Visor del mapa mundial (celdas + bloqueos) con zoom, pan y tooltip.
Reutilizable en el módulo 6 y otros que usen data/mundo.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import tkinter as tk

_DIR_BLOQUEO = ("up", "down", "left", "right")

# Proporción ancho:alto de cada casilla (como mapa Touch / plot orientado).
_CELL_ASPECT = 1.4

# Tonos suaves por zona en el visor (sin zona = gris neutro).
_COLORES_ZONA = (
    "#2a3d45",
    "#2d3a52",
    "#3d2a45",
    "#2a4538",
    "#45382a",
    "#2a3545",
    "#3a452a",
    "#452a3a",
)


def _extraer_items_mundo(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("cells"), list):
        return [x for x in data["cells"] if isinstance(x, dict)]
    if isinstance(data.get("zones"), list):
        out: list[dict[str, Any]] = []
        for zona in data["zones"]:
            if not isinstance(zona, dict):
                continue
            meta = {
                "subAreaId": zona.get("subAreaId"),
                "zoneName": zona.get("name"),
                "zoneLevel": zona.get("level"),
            }
            for celda in zona.get("cells") or []:
                if not isinstance(celda, dict):
                    continue
                item = dict(celda)
                for k, v in meta.items():
                    if v is not None:
                        item.setdefault(k, v)
                out.append(item)
        return out
    return []


def cargar_celdas_mundo(ruta: str | Path) -> dict[tuple[int, int], dict[str, bool]]:
    """Lee mundo.json → {(x,y): {dirección: True si bloqueada}}."""
    ruta = Path(ruta)
    data = json.loads(ruta.read_text(encoding="utf-8"))
    items = _extraer_items_mundo(data)

    grafo: dict[tuple[int, int], dict[str, bool]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            continue
        clave = (int(pos[0]), int(pos[1]))
        raw = item.get("directionBlock") or {}
        bloqueos = {k: True for k in _DIR_BLOQUEO if raw.get(k) is True}
        grafo[clave] = bloqueos
    return grafo


def cargar_meta_celdas_mundo(ruta: str | Path) -> dict[tuple[int, int], dict[str, Any]]:
    """Metadatos por casilla: zoneName, zoneLevel, subAreaId, mapId."""
    ruta = Path(ruta)
    data = json.loads(ruta.read_text(encoding="utf-8"))
    items = _extraer_items_mundo(data)
    meta: dict[tuple[int, int], dict[str, Any]] = {}
    for item in items:
        pos = item.get("position")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            continue
        clave = (int(pos[0]), int(pos[1]))
        info: dict[str, Any] = {}
        if item.get("zoneName"):
            info["zoneName"] = item["zoneName"]
        if item.get("zoneLevel") is not None:
            info["zoneLevel"] = item["zoneLevel"]
        if item.get("subAreaId") is not None:
            info["subAreaId"] = int(item["subAreaId"])
        if item.get("mapId") is not None:
            info["mapId"] = int(item["mapId"])
        if info:
            meta[clave] = info
    return meta


def cargar_mundo_ui(
    ruta: str | Path,
) -> tuple[dict[tuple[int, int], dict[str, bool]], dict[tuple[int, int], dict[str, Any]]]:
    """Bloqueos + metadatos de zona para el visor del módulo 6."""
    ruta = Path(ruta)
    return cargar_celdas_mundo(ruta), cargar_meta_celdas_mundo(ruta)


_PALETA = {
    "fondo": "#0c0c12",
    "celda": "#252538",
    "celda_hover": "#3a3a58",
    "celda_actual": "#b91c3c",
    "celda_actual_borde": "#ff4d6d",
    "celda_destino": "#0a5c47",
    "celda_destino_borde": "#00e5a8",
    "borde": "#1a1a28",
    "borde_claro": "#2e2e44",
    "bloqueo": "#ff4757",
    "hover_borde": "#00e5a8",
    "tooltip_bg": "#1a1a26",
    "tooltip_fg": "#ececf4",
    "tooltip_suave": "#9494b0",
}


def _color_zona(sub_area_id: int | None) -> str:
    if sub_area_id is None:
        return _PALETA["celda"]
    return _COLORES_ZONA[int(sub_area_id) % len(_COLORES_ZONA)]


def _limites_mundo(celdas: dict[tuple[int, int], Any]) -> tuple[int, int, int, int]:
    xs = [p[0] for p in celdas]
    ys = [p[1] for p in celdas]
    return min(xs), max(xs), min(ys), max(ys)


def _tiene_bloqueos(bloqueos: dict[str, bool]) -> bool:
    return any(bloqueos.get(d) for d in _DIR_BLOQUEO)


def _rect_celda(
    wx: int,
    wy: int,
    min_x: int,
    min_y: int,
    pan_x: float,
    pan_y: float,
    margin: float,
    sw: float,
    sh: float,
) -> tuple[float, float, float, float]:
    x, y = (wx - min_x) * sw + pan_x + margin, (wy - min_y) * sh + pan_y + margin
    return x, y, x + sw, y + sh


def _dibujar_arista_bloqueo(
    canvas: tk.Canvas,
    x: float,
    y: float,
    x2: float,
    y2: float,
    lado: str,
    *,
    grosor: float,
) -> None:
    """Línea simple en el borde donde no se puede pasar."""
    color = _PALETA["bloqueo"]
    if lado == "up":
        canvas.create_line(x, y, x2, y, fill=color, width=grosor, tags="bloqueo")
    elif lado == "down":
        canvas.create_line(x, y2, x2, y2, fill=color, width=grosor, tags="bloqueo")
    elif lado == "left":
        canvas.create_line(x, y, x, y2, fill=color, width=grosor, tags="bloqueo")
    elif lado == "right":
        canvas.create_line(x2, y, x2, y2, fill=color, width=grosor, tags="bloqueo")


class VistaMapaMundo(tk.Frame):
    """Canvas con el grafo mundial: zoom (rueda), pan (arrastrar), hover (coords)."""

    def __init__(
        self,
        master,
        celdas: dict[tuple[int, int], dict[str, bool]],
        *,
        alto_canvas: int = 520,
        ancho_canvas: int = 560,
        celda_base: int = 14,
        posicion_actual: tuple[int, int] | None = None,
        posicion_destino: tuple[int, int] | None = None,
        meta_celdas: dict[tuple[int, int], dict[str, Any]] | None = None,
        on_celda_hover: Callable[[tuple[int, int] | None], None] | None = None,
        on_celda_click: Callable[[tuple[int, int]], None] | None = None,
        **kw,
    ):
        super().__init__(master, bg=_PALETA["fondo"], **kw)
        self._celdas = celdas
        self._meta_celdas = meta_celdas or {}
        self._on_celda_hover = on_celda_hover
        self._on_celda_click = on_celda_click
        self._posicion_actual = posicion_actual
        self._posicion_destino = posicion_destino
        self._cell_base = celda_base
        self._zoom = 1.0
        self._zoom_min = 0.25
        self._zoom_max = 5.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._margin = 12
        self._hover: tuple[int, int] | None = None
        self._pan_origen: tuple[float, float, float, float] | None = None
        self._pan_movio = False
        self._pan_umbral = 4
        self._vista_inicial_hecha = False
        self._mouse_x = 0.0
        self._mouse_y = 0.0

        if celdas:
            self._min_x, self._max_x, self._min_y, self._max_y = _limites_mundo(celdas)
        else:
            self._min_x = self._max_x = self._min_y = self._max_y = 0

        encabezado = tk.Frame(self, bg=_PALETA["fondo"])
        encabezado.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            encabezado,
            text="Mapa mundial",
            font=("Segoe UI", 10, "bold"),
            fg=_PALETA["tooltip_fg"],
            bg=_PALETA["fondo"],
        ).pack(side=tk.LEFT)

        self._lbl_zoom = tk.Label(
            encabezado,
            text="Zoom 100%",
            font=("Segoe UI", 8),
            fg=_PALETA["tooltip_suave"],
            bg=_PALETA["fondo"],
        )
        self._lbl_zoom.pack(side=tk.RIGHT)

        self._lbl_coords = tk.Label(
            self,
            text="Pasa el ratón sobre una casilla",
            font=("Segoe UI", 9),
            fg=_PALETA["tooltip_suave"],
            bg=_PALETA["fondo"],
            anchor="w",
        )
        self._lbl_coords.pack(fill=tk.X, pady=(0, 4))

        marco = tk.Frame(self, bg=_PALETA["borde"], padx=1, pady=1)
        marco.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            marco,
            width=ancho_canvas,
            height=alto_canvas,
            bg=_PALETA["fondo"],
            highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        pie = tk.Label(
            self,
            text=(
                "Click · destino   ·   Arrastrar · mover   ·   Rueda · zoom   ·   "
                "Línea roja = no se puede pasar por ahí"
            ),
            font=("Segoe UI", 8),
            fg=_PALETA["tooltip_suave"],
            bg=_PALETA["fondo"],
        )
        pie.pack(fill=tk.X, pady=(6, 0))

        self._canvas.bind("<Configure>", self._al_canvas_redimensionado)
        self._canvas.bind("<Motion>", self._al_mover_raton)
        self._canvas.bind("<Leave>", self._al_salir_canvas)
        self._canvas.bind("<ButtonPress-1>", self._iniciar_pan)
        self._canvas.bind("<B1-Motion>", self._arrastrar_pan)
        self._canvas.bind("<ButtonRelease-1>", self._fin_pan)
        self._canvas.bind("<MouseWheel>", self._zoom_rueda)
        self._canvas.bind("<Button-4>", lambda _e: self._zoom_paso(1.12))
        self._canvas.bind("<Button-5>", lambda _e: self._zoom_paso(1 / 1.12))

        if self._posicion_actual is not None:
            self._actualizar_etiqueta_posicion()

    def establecer_posicion_destino(self, posicion: tuple[int, int] | None) -> None:
        """Marca la casilla destino (verde)."""
        self._posicion_destino = posicion
        self._redibujar()

    def establecer_posicion_actual(
        self,
        posicion: tuple[int, int] | None,
        *,
        centrar: bool = True,
    ) -> None:
        """Marca la casilla actual (rojo) y opcionalmente centra la vista."""
        self._posicion_actual = posicion
        self._actualizar_etiqueta_posicion()
        if centrar and posicion is not None:
            self._vista_inicial_hecha = False
            if self._canvas.winfo_width() > 1:
                self._ajustar_vista_inicial()
        self._redibujar()

    def _actualizar_etiqueta_posicion(self) -> None:
        if self._posicion_actual is None:
            return
        wx, wy = self._posicion_actual
        if (wx, wy) in self._celdas:
            self._lbl_coords.configure(
                text=f"Estás aquí: {wx} , {wy}  ·  pasa el ratón para otras casillas",
                fg=_PALETA["celda_actual_borde"],
            )
        else:
            self._lbl_coords.configure(
                text=f"Posición OCR: {wx} , {wy}  (no está en el mapa cargado)",
                fg=_PALETA["tooltip_suave"],
            )

    def _tam_celda_h(self) -> float:
        return self._cell_base * self._zoom

    def _tam_celda_w(self) -> float:
        return self._tam_celda_h() * _CELL_ASPECT

    def _world_a_pantalla(self, wx: int, wy: int) -> tuple[float, float]:
        sw = self._tam_celda_w()
        sh = self._tam_celda_h()
        x = (wx - self._min_x) * sw + self._pan_x + self._margin
        y = (wy - self._min_y) * sh + self._pan_y + self._margin
        return x, y

    def _pantalla_a_world(self, px: float, py: float) -> tuple[int, int] | None:
        sw = self._tam_celda_w()
        sh = self._tam_celda_h()
        if sw < 0.5 or sh < 0.5:
            return None
        col = int((px - self._pan_x - self._margin) / sw)
        fila = int((py - self._pan_y - self._margin) / sh)
        wx = self._min_x + col
        wy = self._min_y + fila
        if (wx, wy) in self._celdas:
            return wx, wy
        return None

    def _ajustar_vista_inicial(self) -> None:
        cw = max(self._canvas.winfo_width(), 200)
        ch = max(self._canvas.winfo_height(), 200)
        if not self._celdas:
            return
        cols = self._max_x - self._min_x + 1
        filas = self._max_y - self._min_y + 1
        map_w = cols * self._cell_base * _CELL_ASPECT
        map_h = filas * self._cell_base
        zx = (cw - 2 * self._margin) / map_w
        zy = (ch - 2 * self._margin) / map_h
        zoom_base = max(self._zoom_min, min(1.0, min(zx, zy)))

        if self._posicion_actual and self._posicion_actual in self._celdas:
            self._zoom = max(zoom_base, min(2.5, self._zoom_max))
            wx, wy = self._posicion_actual
            sw = self._tam_celda_w()
            sh = self._tam_celda_h()
            cx = (wx - self._min_x + 0.5) * sw + self._margin
            cy = (wy - self._min_y + 0.5) * sh + self._margin
            self._pan_x = cw / 2 - cx
            self._pan_y = ch / 2 - cy
        else:
            self._zoom = zoom_base
            sw = self._tam_celda_w()
            sh = self._tam_celda_h()
            self._pan_x = max(self._margin, (cw - cols * sw) / 2)
            self._pan_y = max(self._margin, (ch - filas * sh) / 2)
        self._vista_inicial_hecha = True

    def _al_canvas_redimensionado(self, _event=None) -> None:
        if not self._vista_inicial_hecha and self._celdas:
            self._ajustar_vista_inicial()
        self._redibujar()

    def _redibujar(self) -> None:
        c = self._canvas
        c.delete("all")
        if not self._celdas:
            c.create_text(
                20, 20,
                text="Sin datos de mapa",
                fill=_PALETA["tooltip_suave"],
                anchor="nw",
                font=("Segoe UI", 10),
            )
            return

        sw = self._tam_celda_w()
        sh = self._tam_celda_h()
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        hover = self._hover
        grosor_bloqueo = max(1.5, min(sw, sh) * 0.08)

        # —— Capa 1: casillas (limpias, sin franjas) ——
        for (wx, wy), bloqueos in self._celdas.items():
            x, y, x2, y2 = _rect_celda(
                wx, wy, self._min_x, self._min_y, self._pan_x, self._pan_y, self._margin, sw, sh
            )
            if x2 < 0 or y2 < 0 or x > cw + sw or y > ch + sh:
                continue

            es_hover = hover == (wx, wy)
            es_actual = self._posicion_actual == (wx, wy)
            es_destino = self._posicion_destino == (wx, wy)

            if es_actual and es_destino:
                relleno = _PALETA["celda_actual"]
                borde = _PALETA["celda_destino_borde"]
                grosor = 2
            elif es_actual:
                relleno = _PALETA["celda_actual"]
                borde = _PALETA["celda_actual_borde"]
                grosor = 2
            elif es_destino:
                relleno = _PALETA["celda_destino"]
                borde = _PALETA["celda_destino_borde"]
                grosor = 2
            elif es_hover:
                relleno = _PALETA["celda_hover"]
                borde = _PALETA["hover_borde"]
                grosor = 2
            else:
                info = self._meta_celdas.get((wx, wy), {})
                relleno = _color_zona(info.get("subAreaId"))
                borde = _PALETA["borde_claro"]
                grosor = 1

            c.create_rectangle(
                x, y, x2, y2,
                fill=relleno,
                outline=borde,
                width=grosor,
                tags="celda",
            )

        # —— Capa 2: línea roja solo donde hay bloqueo (sin línea = se puede pasar) ——
        for (wx, wy), bloqueos in self._celdas.items():
            if not _tiene_bloqueos(bloqueos):
                continue
            x, y, x2, y2 = _rect_celda(
                wx, wy, self._min_x, self._min_y, self._pan_x, self._pan_y, self._margin, sw, sh
            )
            if x2 < 0 or y2 < 0 or x > cw + sw or y > ch + sh:
                continue

            for lado in _DIR_BLOQUEO:
                if bloqueos.get(lado):
                    _dibujar_arista_bloqueo(
                        c, x, y, x2, y2, lado, grosor=grosor_bloqueo
                    )

        self._dibujar_tooltip_flotante()
        self._lbl_zoom.configure(text=f"Zoom {int(self._zoom * 100)}%")

    def _texto_zona_celda(self, celda: tuple[int, int]) -> str | None:
        info = self._meta_celdas.get(celda, {})
        zona = info.get("zoneName")
        if not zona:
            return None
        if info.get("zoneLevel") is not None:
            return f"{zona}  ·  niv. {info['zoneLevel']}"
        return str(zona)

    def _dibujar_tooltip_flotante(self) -> None:
        """Etiqueta que sigue el puntero con el nombre de la zona."""
        c = self._canvas
        c.delete("tooltip_flotante")
        if self._hover is None:
            return
        texto = self._texto_zona_celda(self._hover)
        if not texto:
            return

        fuente = ("Segoe UI", 9, "bold")
        pad_x, pad_y = 8, 5
        offset_x, offset_y = 16, -22

        tmp = c.create_text(
            0, 0, text=texto, font=fuente, anchor="nw", tags="tooltip_flotante"
        )
        bbox = c.bbox(tmp)
        c.delete(tmp)
        if not bbox:
            return
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        cw = max(c.winfo_width(), 1)
        ch = max(c.winfo_height(), 1)
        tx = self._mouse_x + offset_x
        ty = self._mouse_y + offset_y
        if tx + tw + pad_x * 2 > cw - 4:
            tx = self._mouse_x - tw - pad_x * 2 - 8
        if ty < 4:
            ty = self._mouse_y + 18
        if ty + th + pad_y * 2 > ch - 4:
            ty = max(4, self._mouse_y - th - pad_y * 2 - 8)

        x1, y1 = tx - pad_x, ty - pad_y
        x2, y2 = tx + tw + pad_x, ty + th + pad_y
        c.create_rectangle(
            x1, y1, x2, y2,
            fill="#1e1e2e",
            outline="#ff4757",
            width=1,
            tags="tooltip_flotante",
        )
        c.create_text(
            tx, ty,
            text=texto,
            fill="#ffffff",
            font=fuente,
            anchor="nw",
            tags="tooltip_flotante",
        )

    def _notificar_hover(self, celda: tuple[int, int] | None) -> None:
        if celda is None:
            if self._posicion_actual is not None:
                self._actualizar_etiqueta_posicion()
            else:
                self._lbl_coords.configure(
                    text="Pasa el ratón sobre una casilla",
                    fg=_PALETA["tooltip_suave"],
                )
        else:
            bloqueos = self._celdas.get(celda, {})
            partes = [d for d in _DIR_BLOQUEO if bloqueos.get(d)]
            if partes:
                extra = f"  ·  bloqueado ({', '.join(partes)})"
            else:
                extra = ""
            es_actual = celda == self._posicion_actual
            es_destino = celda == self._posicion_destino
            if es_actual and es_destino:
                prefijo = "Estás aquí y es el destino · "
                color = _PALETA["celda_destino_borde"]
            elif es_actual:
                prefijo = "Estás aquí · "
                color = _PALETA["celda_actual_borde"]
            elif es_destino:
                prefijo = "Destino · "
                color = _PALETA["celda_destino_borde"]
            else:
                prefijo = "Posición: "
                color = _PALETA["tooltip_suave"]
            self._lbl_coords.configure(
                text=f"{prefijo}{celda[0]} , {celda[1]}{extra}",
                fg=color,
            )
        if self._on_celda_hover:
            self._on_celda_hover(celda)

    def _al_mover_raton(self, event: tk.Event) -> None:
        self._mouse_x = float(event.x)
        self._mouse_y = float(event.y)
        celda = self._pantalla_a_world(event.x, event.y)
        if celda != self._hover:
            self._hover = celda
            self._notificar_hover(celda)
            self._redibujar()
        else:
            self._dibujar_tooltip_flotante()

    def _al_salir_canvas(self, _event=None) -> None:
        if self._hover is not None:
            self._hover = None
            self._notificar_hover(None)
            self._redibujar()

    def _iniciar_pan(self, event: tk.Event) -> None:
        self._pan_origen = (event.x, event.y, self._pan_x, self._pan_y)
        self._pan_movio = False

    def _arrastrar_pan(self, event: tk.Event) -> None:
        if self._pan_origen is None:
            return
        ox, oy, px, py = self._pan_origen
        if abs(event.x - ox) > self._pan_umbral or abs(event.y - oy) > self._pan_umbral:
            self._pan_movio = True
        self._pan_x = px + (event.x - ox)
        self._pan_y = py + (event.y - oy)
        self._redibujar()

    def _fin_pan(self, event: tk.Event | None = None) -> None:
        if (
            not self._pan_movio
            and self._pan_origen is not None
            and event is not None
            and self._on_celda_click is not None
        ):
            celda = self._pantalla_a_world(event.x, event.y)
            if celda is not None:
                self._on_celda_click(celda)
        self._pan_origen = None

    def _zoom_hacia(self, factor: float, cx: float, cy: float) -> None:
        antes = self._pantalla_a_world(cx, cy)
        nuevo = max(self._zoom_min, min(self._zoom_max, self._zoom * factor))
        if abs(nuevo - self._zoom) < 1e-6:
            return
        self._zoom = nuevo
        if antes is not None:
            nx, ny = self._world_a_pantalla(antes[0], antes[1])
            self._pan_x += cx - nx
            self._pan_y += cy - ny
        self._redibujar()

    def _zoom_rueda(self, event: tk.Event) -> None:
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        factor = 1.12 if delta > 0 else 1 / 1.12
        self._zoom_hacia(factor, event.x, event.y)

    def _zoom_paso(self, factor: float) -> None:
        cx = self._canvas.winfo_width() / 2
        cy = self._canvas.winfo_height() / 2
        self._zoom_hacia(factor, cx, cy)


__all__ = [
    "VistaMapaMundo",
    "cargar_celdas_mundo",
    "cargar_meta_celdas_mundo",
    "cargar_mundo_ui",
]
