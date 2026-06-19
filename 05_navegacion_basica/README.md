# Módulo 5 — Navegación básica

## Qué aprenderás

- **Modal ampliado:** zona del juego + franja de coordenadas + **editor de ruta** con flechas.
- **Leer** las coordenadas del mapa con OCR (antes y después).
- **Armar tu recorrido** con ▲▼◀▶ y click ● en el modal.
- **Ejecutar** cada paso: arrastre o click, y comprobar el cambio con OCR.

## Requisitos

- Tesseract instalado (igual que módulo 4).
- Dofus Touch en un **mapa** donde un arrastre cambie de casilla.
- **Phone Link** o emulador. El arrastre usa `pydirectinput` (en `requirements.txt`).

## Instalación

```bash
cd 05_navegacion_basica
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py --overlay
```

## Flujo

1. Juego al frente → **modal** → marcar juego y coordenadas.
2. **Paso 3:** pulsa flechas para armar la ruta (● = click en el mapa). También puedes escribir: `derecha → arriba`.
3. **Iniciar recorrido** → cuenta atrás → OCR lee posición inicial.
4. Por cada paso: arrastre o click → OCR espera cambio de coords.
5. Comparación final en el panel → **Esc** para cerrar.

## Ajustes (`config.py`)

| Variable | Uso |
|----------|-----|
| `RUTA_EJEMPLO` | Texto inicial en el modal (vacío por defecto; solo si quieres un ejemplo fijo) |
| `DRAG_PIXELES` / `DRAG_DURACION` | Fuerza del arrastre (por defecto 280 px en 0,75 s) |
| `PAUSA_ANTES_ARRASTRE` | Segundos antes de cada arrastre |
| `PAUSA_TRAS_CLICK` | Pausa tras un paso de click |
| `OCR_INTERVALO_ESPERA` | Segundos entre lecturas OCR tras cada arrastre |
| `OCR_ESPERA_MAXIMA` | Tiempo máximo esperando cambio de coords |
| `OCR_PAUSA_TRAS_CAMBIO` | Pausa extra tras detectar cambio (mapa cargando en Phone Link) |
| `OCR_REINTENTOS_ESPERA` | Si falla, cuántas veces vuelve a esperar sin re-arrastrar |

## Relación con otros módulos

| Módulo | Modal |
|--------|-------|
| 4 | Solo 2 zonas (`menu_calibracion_doble.py`) — **sin cambios** |
| 5 | 2 zonas + editor de ruta (`menu_calibracion_navegacion.py`) |
| 6 | 2 zonas + destino X/Y automático (`menu_calibracion_ruta.py`) |

El editor reutilizable vive en `common/editor_ruta.py`.
