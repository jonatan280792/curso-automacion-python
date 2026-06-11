# Módulo 3 — Reconocimiento de imágenes (iconos)

## Qué aprende la audiencia

- Marcar la **zona de trabajo** (igual que módulos 1 y 2).
- Usar una **plantilla PNG pequeña** (icono de interfaz) para buscar dentro del juego.
- Entender **confianza** de la búsqueda (sin tecnicismos).
- Secuencia demo: **inventario → cerrar → características** (con pausas y log).

No usa trigo ni recursos del mapa: eso va en módulos posteriores.

## Archivos

- `config.py` — Zona, ventana, plantillas, confianza, pausas.
- `main.py` — Secuencia del vídeo.
- `window_manager.py` — Clase `GestorVentana` (igual que módulo 2).
- `buscador_imagen.py` — Clase `BuscadorImagen`.
- `images/plantillas/` — Tus PNG (ver `LEEME.md`).

## Instalación

```bash
cd 03_reconocimiento_imagenes
pip install -r requirements.txt
```

`opencv-python-headless` es necesario para usar `confidence` en PyAutoGUI.

## Ejecución

```bash
python main.py --overlay
```

Detalles técnicos: `--debug-temp`

## Flujo

1. Marcas la zona del juego (pantalla gris).
2. Cuenta atrás → busca ventana Dofus Touch → la activa.
3. Comprueba las 3 plantillas en `images/plantillas/`.
4. **Paso 1:** busca `inventario.png` → clic (abre inventario).
5. Pausa 5 s (cuenta atrás en el log).
6. **Paso 2:** busca `cerrar.png` → clic (cierra inventario).
7. Pausa 5 s.
8. **Paso 3:** busca `caracteristicas.png` → clic.
9. Panel hasta **Esc**; opcional: abre carpeta plantillas.

El juego debe estar **abierto** con el HUD visible (no hace falta estar en un mapa concreto).

## Relación con el módulo 2

- Las fotos `region_*.png` del módulo 2 son **zonas grandes**.
- Aquí necesitas una plantilla **pequeña**; puedes recortar el icono desde una de esas fotos o crear `inventario.png` a mano.

## Ajustes

| Variable | Uso |
|----------|-----|
| `BUSCAR_EN` | `"zona"` (por defecto) o `"ventana"` |
| `CONFIANZA_BUSQUEDA` | Precisión de la coincidencia (0.0–1.0) |
| `DEMO_SECUENCIA` | Orden de plantillas (nombre, texto log) |
| `PAUSA_ENTRE_PASOS_DEMO` | Segundos entre pasos (default 5) |
