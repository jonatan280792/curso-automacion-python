#!/usr/bin/env python3
"""Pathfinding BFS sobre el grafo mundial (position + directionBlock)."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import config
from common.vista_mapa_mundo import cargar_celdas_mundo

_DELTAS: dict[str, tuple[int, int]] = {
    "left": (-1, 0),
    "right": (1, 0),
    "up": (0, -1),
    "down": (0, 1),
}


class BuscadorRutas:
    """Calcula rutas respetando bloqueos del grafo mundial."""

    _grafo: dict[tuple[int, int], dict[str, bool]] | None = None
    _ruta_json: Path | None = None

    @classmethod
    def _ruta_mundo(cls) -> Path:
        base = Path(__file__).resolve().parent
        rel = getattr(config, "RUTA_MUNDO_JSON", "data/mundo.json")
        return base / rel

    @classmethod
    def cargar_grafo(cls, *, forzar: bool = False) -> dict[tuple[int, int], dict[str, bool]]:
        ruta = cls._ruta_mundo()
        if not forzar and cls._grafo is not None and cls._ruta_json == ruta:
            return cls._grafo

        if not ruta.is_file():
            raise FileNotFoundError(
                f"No existe el grafo mundial: {ruta}. "
                "Ejecuta: python generar_mundo.py"
            )

        cls._grafo = cargar_celdas_mundo(ruta)
        cls._ruta_json = ruta
        return cls._grafo

    @classmethod
    def info_grafo(cls) -> tuple[int, Path]:
        grafo = cls.cargar_grafo()
        return len(grafo), cls._ruta_mundo()

    @classmethod
    def calcular_ruta(
        cls,
        inicio: tuple[int, int] | list[int],
        fin: tuple[int, int] | list[int],
    ) -> tuple[list[str] | None, str | None]:
        """Ruta más corta (BFS). Devuelve (pasos, error)."""
        origen = (int(inicio[0]), int(inicio[1]))
        destino = (int(fin[0]), int(fin[1]))

        if origen == destino:
            return [], None

        try:
            grafo = cls.cargar_grafo()
        except FileNotFoundError as e:
            return None, str(e)

        if origen not in grafo:
            return None, (
                f"Origen {origen[0]} , {origen[1]} no está en el mapa del curso "
                f"({len(grafo)} casillas)."
            )
        if destino not in grafo:
            return None, (
                f"Destino {destino[0]} , {destino[1]} no está en el mapa del curso "
                f"({len(grafo)} casillas)."
            )

        cola: deque[tuple[int, int]] = deque([origen])
        padre: dict[tuple[int, int], tuple[int, int] | None] = {origen: None}
        movimiento: dict[tuple[int, int], str] = {}

        while cola:
            x, y = cola.popleft()
            if (x, y) == destino:
                return cls._reconstruir_ruta(destino, padre, movimiento), None

            bloqueos = grafo.get((x, y), {})
            for direccion, (dx, dy) in _DELTAS.items():
                if bloqueos.get(direccion):
                    continue
                vecino = (x + dx, y + dy)
                if vecino not in grafo or vecino in padre:
                    continue
                padre[vecino] = (x, y)
                movimiento[vecino] = direccion
                cola.append(vecino)

        return None, (
            f"No hay ruta de {origen[0]} , {origen[1]} a "
            f"{destino[0]} , {destino[1]} (bloqueos o mapas desconectados)."
        )

    @staticmethod
    def _reconstruir_ruta(
        destino: tuple[int, int],
        padre: dict[tuple[int, int], tuple[int, int] | None],
        movimiento: dict[tuple[int, int], str],
    ) -> list[str]:
        pasos: list[str] = []
        nodo = destino
        while padre.get(nodo) is not None:
            pasos.append(movimiento[nodo])
            nodo = padre[nodo]  # type: ignore[assignment]
        pasos.reverse()
        return pasos

    @staticmethod
    def direccion_a_espanol(direccion: str) -> str:
        etiquetas = getattr(config, "ETIQUETAS_DIRECCION", {})
        return etiquetas.get(direccion, direccion)
