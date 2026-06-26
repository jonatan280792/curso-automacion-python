# Módulo 6 — Pathfinding con mapa mundial

## Qué aprenderás

- Mismo **modal de calibración** que los módulos 4 y 5, más **mapa mundial** (click = destino).
- Leer **dónde estás** con OCR (origen).
- Calcular la **ruta más corta** con **BFS**, respetando bloqueos del grafo (`data/mundo.json`).
- **Ejecutar la ruta:** arrastrar el mapa paso a paso (igual que módulo 5).
- Tras cada arrastre, **esperar con OCR** hasta que cambien las coordenadas.

> El módulo 5 enseña a **mover el mapa a mano** (flechas).  
> El módulo 6 **calcula solo** la secuencia de movimientos y la ejecuta con el mismo arrastre.

## Requisitos

- Tesseract instalado (igual que módulos 4 y 5).
- Mismo entorno que el módulo 5 (Phone Link o emulador; arrastre con `pydirectinput`).
- `data/mundo.json` incluido (~2700 casillas, 21 zonas nombradas del mundo Touch).

## Instalación

```bash
cd 06_algoritmos_pathfinding
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py --overlay
```

## Flujo

1. Juego al frente → **modal** → marcar juego y coordenadas → **click** en el mapa (destino verde) → **Iniciar**.
2. Cuenta atrás → OCR lee **origen** → BFS calcula pasos (izquierda/derecha/arriba/abajo).
3. **Por cada paso:** arrastra el mapa → relee OCR hasta que **X e Y cambien**.
4. Comprueba si llegaste al destino → pulsa **Esc** en el panel.

## Grafo mundial (`data/mundo.json`)

JSON version 3 con dos vistas del mismo dato:

| Sección | Uso |
|---------|-----|
| `zones[]` | Agrupado por subArea: nombre, nivel y `cells[]` con posición + bloqueos (UI / lectura) |
| `cells[]` | Lista plana para pathfinding (BFS del bot) |

Cada casilla:

| Campo | Significado |
|-------|-------------|
| `position` | Coordenadas `[x, y]` del mapa (las mismas que lee el OCR) |
| `mapId` | ID interno del mapa en Touch (referencia) |
| `directionBlock` | Direcciones **bloqueadas** (`true` = no puedes salir por ahí) |

En el modal, al pasar el ratón verás el **nombre de la zona** junto al puntero; **rojo** = tu posición (OCR), **verde** = destino.

**Cómo se calculan los bloqueos:**
1. **Bordes del mundo:** si no hay mapa vecino en esa dirección → bloqueado.
2. **Bloqueos finos** (`routes/principal.json`): mapas que solo dejan ir abajo, solo derecha, etc.

Si `directionBlock` no aparece en una casilla → las **4 direcciones** están libres.

**Plus del curso:** ~2700 casillas; **21 zonas** con nombre; **~789** con algún bloqueo.

### Regenerar el JSON (mapa completo)

Tras actualizar el catálogo con huérfanos (`setup_mapa_touch`):

```bash
cd setup_mapa_touch
python main.py sync-data          # fase 1: puede tardar horas (escaneo reanudable)
python main.py sync-assets        # fase 2: imágenes (opcional para el bot)

cd ../06_algoritmos_pathfinding
python generar_mundo.py
```

`sync-data` escanea IDs huérfanos por defecto. Para una prueba rápida: `sync-data --no-scan`.

Lee `setup_mapa_touch/output/catalog/bot/routes_by_position.json` y escribe `data/mundo.json`.

## Ejemplo

Estás en `-9, -36` y pones destino `-12, -40`:

- Si no hay bloqueos en el camino → ruta corta (p. ej. 3 izquierda + 4 arriba).
- Si a la derecha hay borde de mapa → BFS **desvía** por otra dirección.

## Ajustes (`config.py`)

| Variable | Uso |
|----------|-----|
| `RUTA_MUNDO_JSON` | Grafo de casillas y bloqueos |
| `DESTINO_DEFAULT` | Coordenadas destino en el modal, ej. `-12, -40` |
| `DRAG_PIXELES` / `DRAG_DURACION` | Fuerza del arrastre por paso |
| `OCR_INTERVALO_ESPERA` | Segundos entre lecturas OCR tras cada paso |
| `OCR_ESPERA_MAXIMA` | Tiempo máximo esperando cambio de coords |
| `OCR_REINTENTOS_ARRASTRE` | Si falla la espera, vuelve a arrastrar (lag Phone Link) |
| `VALIDAR_VECINO_PASO` | Comprueba que OCR leyó la casilla vecina esperada |

El **origen** siempre lo lee el OCR. El **destino** lo pones en el modal (o cambias los defaults en config).

## Archivos

- `menu_calibracion_ruta.py` — modal propio del módulo 6 (zonas + destino).
- `data/mundo.json` — grafo mundial (position + directionBlock).
- `generar_mundo.py` — regenera `mundo.json` desde el catálogo.
- `buscador_rutas.py` — BFS sobre el grafo.
- `navegacion.py` — arrastre + espera por cambio de OCR (vía `common/navegacion_mapa.py`).
- `main.py` — orquesta calibración, plan y ejecución.

## Relación con módulo 5

| | Módulo 5 | Módulo 6 |
|---|----------|----------|
| Quién elige la ruta | Tú (flechas en el modal) | El programa (BFS + JSON) |
| Movimiento en juego | Arrastre / click | Arrastre (mismo mecanismo) |
| OCR | Confirma cada paso | Confirma cada paso |
