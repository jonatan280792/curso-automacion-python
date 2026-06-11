# Plantillas del módulo 3

Aquí van **imágenes pequeñas** (PNG) de iconos del juego que el programa **busca** en pantalla.

## Archivos del demo (los 3)

| Archivo | Cuándo se usa |
|---------|----------------|
| `inventario.png` | Icono del HUD para **abrir** inventario |
| `cerrar.png` | Botón **X / cerrar** del panel de inventario (visible con inventario abierto) |
| `caracteristicas.png` | Icono de **características** en el HUD (con inventario cerrado) |

El programa ejecuta en orden: **inventario → pausa 5 s → cerrar → pausa 5 s → características**.  
Todo se escribe en el panel con `--overlay`.

## Cómo crearlas

1. Captura del juego con el HUD visible.
2. Recorta **solo el icono** (unos píxeles), no un recorte grande del módulo 2.
3. Para `cerrar.png`: abre el inventario a mano y recorta la **X** o botón cerrar.
4. Guarda aquí con el **nombre exacto** de la tabla.

## Confianza

En `config.py`, `CONFIANZA_BUSQUEDA` (por defecto `0.72`):

- Más alto (0.85) = más estricto.
- Más bajo (0.65) = más permisivo si el icono cambia un poco.

## Ritmo del demo

`PAUSA_ENTRE_PASOS_DEMO = 5.0` — segundos entre pasos (con cuenta atrás en el log).
