# Módulo 1 — Fundamentos e instalación

## Qué aprenderás

- Instalar dependencias del módulo (PyAutoGUI, Pillow, mss).
- Marcar la **zona de trabajo** dibujando un rectángulo sobre el juego.
- Localizar y activar la ventana de Dofus Touch.
- Hacer **4 clics aleatorios** dentro de la zona marcada.
- Guardar una captura en `output/captura_modulo1.png`.
- Usar el panel flotante de logs con `--overlay`.

## Requisitos

- Windows 10/11
- Python 3.10+
- Dofus Touch abierto en ventana (emulador, Phone Link, etc.)

## Instalación

```bash
cd 01_fundamentos_instalacion
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py --overlay
```

Opcional (solo para pruebas): `--debug-temp` muestra detalles técnicos en consola.

## Flujo

1. Aparece una pantalla gris → **arrastra un rectángulo** solo sobre el juego (Esc = cancelar).
2. Cuenta atrás de 4 segundos.
3. El programa busca la ventana del juego y la pone al frente.
4. Hace 4 clics aleatorios dentro de la zona marcada.
5. Guarda `output/captura_modulo1.png` y abre la carpeta `output/`.

## Archivos generados en `output/`

| Archivo | Descripción |
|---------|-------------|
| `captura_modulo1.png` | Captura del rectángulo que marcaste |
| `zona_captura_modulo1.json` | Coordenadas de la zona guardadas |

## Ajustes en `config.py`

- `TITULOS_VENTANA` — títulos que reconoce el programa.
- `CLIC_MARGEN_*` — márgenes para que los clics no caigan en el borde.
- `SEGUNDOS_CUENTA_ATRAS` — segundos antes de empezar la demo.
