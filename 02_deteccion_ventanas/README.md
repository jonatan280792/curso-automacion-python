# Módulo 2 — Ventana del juego y coordenadas

## Qué aprenderás

- Marcar la **zona de trabajo** (igual que el módulo 1).
- Leer datos básicos de la ventana del juego.
- Guardar **tres recortes** dentro del juego (no pantalla entera).
- Idea de coordenadas en pantalla vs dentro del juego.
- Clics de prueba en puntos relativos.

## Archivos

- `config.py` — Ajustes en español (zona, títulos, pausas, panel).
- `main.py` — Secuencia del vídeo.
- `window_manager.py` — Clase `GestorVentana`.

## Instalación

```bash
cd 02_deteccion_ventanas
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py --overlay
```

Detalles técnicos solo para pruebas: `--debug-temp`

## Flujo

1. Marcas la zona del juego (pantalla gris).
2. Cuenta atrás → busca ventana Dofus Touch → la activa.
3. Muestra datos de la ventana.
4. Guarda `output/region_zona_*.png` (tres recortes).
5. Ejemplos pantalla ↔ juego y tres clics de prueba.
6. Abre la carpeta `output` al terminar.

El juego debe estar **abierto** antes de ejecutar. Funciona con uno o dos monitores (capturas con **mss**, como el módulo 1).
