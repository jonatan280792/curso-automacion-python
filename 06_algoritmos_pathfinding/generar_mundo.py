#!/usr/bin/env python3
"""
Regenera data/mundo.json con position + directionBlock (true = no se puede ir).

Fuentes:
  1. Catálogo setup_mapa_touch (casillas, zonas, directionBlock del catálogo)
  2. Inferencia: bloquea si no hay mapa vecino en esa dirección
  3. routes/principal.json: bloqueos finos adicionales (Bonta, etc.)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import config

_DIRECCIONES = ("up", "down", "left", "right")
_NEIGHBOURS = (
    ("left", -1, 0),
    ("right", 1, 0),
    ("up", 0, -1),
    ("down", 0, 1),
)


def _bloqueos_sparse(raw: dict[str, Any]) -> dict[str, bool]:
    return {k: True for k in _DIRECCIONES if raw.get(k) is True}


def _inferir_bloqueos(celdas: set[tuple[int, int]]) -> dict[tuple[int, int], dict[str, bool]]:
    """Sin mapa en (x+dx, y+dy) → esa dirección bloqueada."""
    out: dict[tuple[int, int], dict[str, bool]] = {}
    for x, y in celdas:
        bloqueo: dict[str, bool] = {}
        for nombre, dx, dy in _NEIGHBOURS:
            if (x + dx, y + dy) not in celdas:
                bloqueo[nombre] = True
        out[(x, y)] = bloqueo
    return out


def _fusionar_bloqueos(
    inferidos: dict[str, bool],
    manuales: dict[str, bool],
) -> dict[str, bool]:
    """Unión: bloqueado si cualquier fuente lo marca."""
    fusion: dict[str, bool] = {}
    for d in _DIRECCIONES:
        if inferidos.get(d) or manuales.get(d):
            fusion[d] = True
    return fusion


def _cargar_bloqueos_manuales(ruta: Path) -> dict[tuple[int, int], dict[str, bool]]:
    if not ruta.is_file():
        return {}
    data = json.loads(ruta.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("cells", [])
    out: dict[tuple[int, int], dict[str, bool]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            continue
        bloqueo = _bloqueos_sparse(item.get("directionBlock") or {})
        if bloqueo:
            clave = (int(pos[0]), int(pos[1]))
            out[clave] = _fusionar_bloqueos(out.get(clave, {}), bloqueo)
    return out


def _cargar_todos_bloqueos_manuales(base: Path) -> dict[tuple[int, int], dict[str, bool]]:
    rutas = getattr(config, "RUTAS_BLOQUEOS_MANUAL", None)
    if rutas is None:
        rutas = (getattr(config, "RUTA_BLOQUEOS_MANUAL", "routes/principal.json"),)
    elif isinstance(rutas, str):
        rutas = (rutas,)
    out: dict[tuple[int, int], dict[str, bool]] = {}
    for rel in rutas:
        for pos, bloqueo in _cargar_bloqueos_manuales(base / rel).items():
            out[pos] = _fusionar_bloqueos(out.get(pos, {}), bloqueo)
    return out


def _agrupar_por_zona(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa celdas por subAreaId + nombre (ordenado para UI y lectura humana)."""
    from collections import defaultdict

    grupos: dict[tuple[int | None, str, int | None], list[dict[str, Any]]] = defaultdict(list)
    for celda in cells:
        sid = celda.get("subAreaId")
        nombre = celda.get("zoneName") or "Continente (sin zona)"
        nivel = celda.get("zoneLevel")
        clave = (int(sid) if sid is not None else None, str(nombre), int(nivel) if nivel is not None else None)
        item: dict[str, Any] = {"position": celda["position"]}
        if celda.get("mapId") is not None:
            item["mapId"] = celda["mapId"]
        if celda.get("directionBlock"):
            item["directionBlock"] = celda["directionBlock"]
        grupos[clave].append(item)

    zonas: list[dict[str, Any]] = []
    for (sid, nombre, nivel), celdas_zona in sorted(
        grupos.items(),
        key=lambda kv: (-len(kv[1]), kv[0][1]),
    ):
        zona: dict[str, Any] = {
            "name": nombre,
            "cellCount": len(celdas_zona),
            "cells": sorted(celdas_zona, key=lambda c: (c["position"][0], c["position"][1])),
        }
        if sid is not None:
            zona["subAreaId"] = sid
        if nivel is not None:
            zona["level"] = nivel
        zonas.append(zona)
    return zonas


def _cargar_zonas_por_posicion(ruta: Path) -> dict[tuple[int, int], dict[str, Any]]:
    if not ruta.is_file():
        return {}
    data = json.loads(ruta.read_text(encoding="utf-8"))
    by_pos = data.get("byPosition") or {}
    sub_areas = data.get("subAreas") or {}
    out: dict[tuple[int, int], dict[str, Any]] = {}
    for key, sid in by_pos.items():
        if not isinstance(key, str) or "," not in key:
            continue
        x_str, y_str = key.split(",", 1)
        zone = sub_areas.get(str(sid), {})
        meta: dict[str, Any] = {"subAreaId": int(sid)}
        if zone.get("name"):
            meta["zoneName"] = zone["name"]
        if zone.get("level") is not None:
            meta["zoneLevel"] = zone["level"]
        out[(int(x_str), int(y_str))] = meta
    return out


def generar(*, fuente: Path | None = None, destino: Path | None = None) -> Path:
    base = Path(__file__).resolve().parent
    fuente = fuente or (base / config.CATALOGO_RUTAS_FUENTE)
    destino = destino or (base / config.RUTA_MUNDO_JSON)

    if not fuente.is_file():
        raise FileNotFoundError(
            f"No se encontró el catálogo: {fuente}\n"
            "Ejecuta sync-data en setup_mapa_touch primero."
        )

    routes = json.loads(fuente.read_text(encoding="utf-8"))
    sub_areas_path = fuente.parent / "sub_areas.json"
    zonas_por_pos = _cargar_zonas_por_posicion(sub_areas_path)
    map_id_por_pos: dict[tuple[int, int], int] = {}
    catalogo_bloqueos: dict[tuple[int, int], dict[str, bool]] = {}
    celdas: set[tuple[int, int]] = set()

    for item in routes:
        pos = item.get("position")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            continue
        clave = (int(pos[0]), int(pos[1]))
        celdas.add(clave)
        bloqueo_cat = _bloqueos_sparse(item.get("directionBlock") or {})
        if bloqueo_cat:
            catalogo_bloqueos[clave] = bloqueo_cat
        mid = item.get("mapId")
        if mid is not None:
            map_id_por_pos[clave] = int(mid)
        zona: dict[str, Any] = {}
        if item.get("subAreaId") is not None:
            zona["subAreaId"] = int(item["subAreaId"])
        if item.get("zoneName"):
            zona["zoneName"] = item["zoneName"]
        if item.get("zoneLevel") is not None:
            zona["zoneLevel"] = item["zoneLevel"]
        if zona:
            zonas_por_pos[clave] = {**zonas_por_pos.get(clave, {}), **zona}

    primary_path = fuente.parent / "map_id_by_position.json"
    if primary_path.is_file():
        primary_by_pos = json.loads(primary_path.read_text(encoding="utf-8"))
        for key, mid in primary_by_pos.items():
            if not isinstance(key, str) or "," not in key:
                continue
            x_str, y_str = key.split(",", 1)
            map_id_por_pos[(int(x_str), int(y_str))] = int(mid)

    manuales = _cargar_todos_bloqueos_manuales(base)
    celdas |= set(manuales.keys())

    inferidos = _inferir_bloqueos(celdas)
    cells_out: list[dict[str, Any]] = []
    con_bloqueo = 0

    for x, y in sorted(celdas):
        pos = (x, y)
        if pos in manuales:
            bloqueo = _fusionar_bloqueos(inferidos.get(pos, {}), manuales[pos])
        else:
            bloqueo = _fusionar_bloqueos(
                _fusionar_bloqueos(inferidos.get(pos, {}), catalogo_bloqueos.get(pos, {})),
                manuales.get(pos, {}),
            )
        celda: dict[str, Any] = {"position": [x, y]}
        if pos in map_id_por_pos:
            celda["mapId"] = map_id_por_pos[pos]
        if pos in zonas_por_pos:
            celda.update(zonas_por_pos[pos])
        if bloqueo:
            celda["directionBlock"] = bloqueo
            con_bloqueo += 1
        cells_out.append(celda)

    zones_out = _agrupar_por_zona(cells_out)

    payload = {
        "version": 3,
        "description": (
            "Grafo mundial Dofus Touch. zones[] agrupa casillas por subArea; "
            "cells[] es la vista plana para pathfinding. "
            "directionBlock: true = no puedes cambiar de mapa por ahí."
        ),
        "cellCount": len(cells_out),
        "cellsWithBlocks": con_bloqueo,
        "zoneCount": len(zones_out),
        "zones": zones_out,
        "cells": cells_out,
    }

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return destino


def main() -> int:
    try:
        out = generar()
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return 1

    data = json.loads(out.read_text(encoding="utf-8"))
    kb = out.stat().st_size / 1024
    zonas = data.get("zoneCount", "?")
    print(
        f"✓ {out.name}: {data['cellCount']} casillas, {zonas} zonas, "
        f"{data['cellsWithBlocks']} con bloqueos ({kb:.1f} KB)"
    )
    print(f"  → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
