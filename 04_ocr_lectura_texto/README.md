# Módulo 4 — Leer coordenadas (OCR)

## Qué aprenderás

- **Modal de calibración:** marca la zona del juego y, aparte, la franja donde salen los números (`-8, -34`).
- Leer coordenadas del mapa con **Tesseract** (OCR).
- **Doble lectura:** el programa lee, te da unos segundos para mover el mapa a mano, y vuelve a leer para comprobar que cambiaron.

## Requisito extra: Tesseract

1. https://github.com/UB-Mannheim/tesseract/wiki  
2. Si no lo detecta: `RUTA_TESSERACT` en `config.py`

## Instalación

```bash
cd 04_ocr_lectura_texto
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py --overlay
```

## Flujo

1. El programa **pone el juego al frente** (para verlo al marcar).
2. **Modal** → “Dibujar zona del juego” → “Dibujar zona de coordenadas” → **Iniciar**.
3. Cuenta atrás → **1.ª lectura OCR** (muestra X, Y).
4. **10 segundos** para que muevas el mapa a mano (cuenta atrás en el panel).
5. **2.ª lectura OCR** → compara ambas coordenadas.
6. Pulsa **Esc** en el panel para cerrar.

Archivos guardados en `output/`:

- `zona_captura_modulo4.json` — juego completo (panel, límites).
- `zona_coordenadas_modulo4.json` — franja de coordenadas.
- `recorte_coordenadas.png` / `recorte_coordenadas_2.png` — capturas OCR de cada lectura.

## Ajustes en `config.py`

- `PAUSA_MANUAL_CAMBIO_MAPA` — segundos para mover el mapa entre lecturas (por defecto 10).
- `TESSERACT_CONFIG` — modo de lectura de Tesseract (whitelist de dígitos y coma).

## Módulos 1–3

Siguen usando **un solo** rectángulo al inicio (`calibrar_zona_al_inicio`). El modal doble es **solo** del módulo 4 (`common/menu_calibracion_doble.py`).
