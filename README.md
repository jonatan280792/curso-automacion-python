# Curso: Automatización con Python

Material del curso en **YouTube** — canal [**Script & Play HQ**](https://www.youtube.com/@ScriptPlayHQ).

Aprende a automatizar la pantalla con Python: ventanas, clics, capturas, recortes, búsqueda de imágenes, OCR y navegación básica.

> **Ejemplo en pantalla:** Dofus Touch (emulador, navegador o Phone Link).  
> No afiliado a Ankama. Contenido **educativo** para aprender programación.

---

## ⚠️ Aviso importante

Automatizar juegos puede ir contra sus términos de servicio y conllevar riesgo de sanción en la cuenta.  
Este repositorio es material de **aprendizaje**. Úsalo con responsabilidad y preferiblemente en entorno de prueba.

---

## Requisitos

| Requisito | Detalle |
|-----------|---------|
| **Sistema** | Windows 10/11 (los ejemplos usan ventanas de escritorio) |
| **Python** | 3.10 o superior recomendado |
| **Editor** | VS Code, Cursor o similar |
| **Juego (ejemplo)** | Dofus Touch abierto en ventana (emulador, app o Phone Link) |
| **Extras según módulo** | Tesseract OCR (módulo 4+), plantillas PNG (módulo 3) |

Cada módulo tiene su propio `requirements.txt`. Instala dependencias **dentro de la carpeta del módulo**:

```bash
cd 01_fundamentos_instalacion
pip install -r requirements.txt
```

---

## Inicio rápido (Módulo 1)

```bash
git clone https://github.com/jonatan280792/curso-automacion-python.git
cd curso-automacion-python/01_fundamentos_instalacion
pip install -r requirements.txt
python main.py --overlay
```

1. Marca la zona del juego con el rectángulo en pantalla.
2. Espera la cuenta atrás.
3. El programa localiza la ventana, hace clics de prueba y guarda una captura en `output/`.

---

## Módulos del curso

El código se publica módulo a módulo cuando sale el video en YouTube.

| # | Carpeta | Qué aprenderás | Estado |
|---|---------|----------------|--------|
| 1 | `01_fundamentos_instalacion` | Instalación, PyAutoGUI, marcar zona de trabajo, localizar ventana, clics de prueba y captura de pantalla | ✅ Publicado |
| 2 | `02_deteccion_ventanas` | Propiedades de la ventana, coordenadas relativas/absolutas, recortes con mss (3 regiones) | ✅ Publicado |
| 3 | `03_reconocimiento_imagenes` | Plantillas con OpenCV, buscar un icono en la zona y hacer clic | 🔜 Próximamente |
| 4 | `04_ocr_lectura_texto` | Tesseract OCR, leer coordenadas del mapa, calibración doble (juego + zona OCR) | 🔜 Próximamente |
| 5 | `05_navegacion_basica` | OCR antes/después, mover el mapa una vez desde el centro de la zona | 🔜 Próximamente |
| 6 | `06_algoritmos_pathfinding` | Pathfinding A*, rutas y bloqueos por casilla (JSON) | 🔜 Próximamente |
| 7 | `07_automatizacion_recursos` | Recolección por imagen, gestión de pods/inventario | 🔜 Próximamente |
| 8 | `08_sistema_combate` | Detección de celdas en combate | 🔜 Próximamente |
| 9 | `09_interfaz_usuario` | Interfaz gráfica con Tkinter (launcher) | 🔜 Próximamente |
| 10 | `10_integracion_optimizacion` | Integración de piezas y cierre del curso | 🔜 Próximamente |

---

## Detalle por módulo

### Módulo 1 — Fundamentos e instalación

Instalación de dependencias (PyAutoGUI, Pillow, mss). Calibración de la **zona de trabajo** dibujando un rectángulo sobre el juego. Localización y activación de la ventana de Dofus Touch. Cuatro clics aleatorios dentro de la zona y captura guardada en `output/captura_modulo1.png`. Panel opcional con `--overlay`.

**Herramientas:** PyAutoGUI, calibración de zona, overlay de logs.

---

### Módulo 2 — Detección de ventanas

Misma calibración de zona que el módulo 1. Obtiene título, posición y tamaño de la ventana del juego. Guarda **tres recortes** (`region_zona_*.png`) con mss — esquina superior, centro e inferior — sin capturar todo el monitor. Muestra ejemplos de conversión entre coordenadas de **pantalla** y coordenadas **dentro del juego**. Tres clics de prueba en posiciones relativas.

**Herramientas:** PyAutoGUI, mss, `GestorVentana`.

---

### Módulo 3 — Reconocimiento de imágenes

Busca un **icono pequeño** (plantilla PNG en `images/plantillas/`) dentro de la zona calibrada. Ajuste de **confianza** de la coincidencia. Clic automático en el icono encontrado (ejemplo: inventario). Si no hay plantilla, puede generar un recorte de ejemplo desde el HUD.

**Herramientas:** OpenCV, PyAutoGUI, template matching.

---

### Módulo 4 — OCR (lectura de coordenadas)

**Calibración doble:** rectángulo del juego + franja donde aparecen las coordenadas del mapa (`-8, -34`). Captura del recorte OCR y lectura con **Tesseract**. Preprocesado de imagen (invertir, binarizar). Muestra las coordenadas leídas en el panel hasta pulsar Esc.

**Herramientas:** Tesseract, pytesseract, modal de calibración doble.

**Requisito extra:** Tesseract OCR instalado en Windows.

---

### Módulo 5 — Navegación básica

Reutiliza calibración doble y OCR del módulo 4. **Lee coordenadas antes** de mover el mapa. **Arrastra** el mapa una vez desde el centro de la zona (dirección y distancia configurables). **Lee coordenadas después** y comprueba que X e Y cambiaron.

**Herramientas:** OCR, arrastre con PyAutoGUI, validación de movimiento.

---

### Módulo 6 — Pathfinding (A*)

Introducción al algoritmo **A\*** para calcular rutas entre casillas del mapa. Carga datos de mapa desde JSON (`directionBlock` — bloqueos por casilla y dirección). Demostración en consola: punto de inicio, destino y secuencia de pasos.

**Herramientas:** A*, JSON de rutas, lógica de navegación en grid.

---

### Módulo 7 — Automatización de recursos

Detección de recursos en pantalla por **imágenes** (ej. trigo). Comprobación de **PODS** / inventario lleno antes de recolectar. Bucle de búsqueda y recolección con reintentos e intervalos configurables.

**Herramientas:** reconocimiento de imágenes, asyncio, gestión básica de inventario.

---

### Módulo 8 — Sistema de combate

Detección de **celdas de combate** en la interfaz usando plantillas PNG. Análisis del estado del combate en pantalla. Base para decisiones automáticas en turnos (detección, no bot completo de combate).

**Herramientas:** template matching, `CombatSystem`.

---

### Módulo 9 — Interfaz de usuario

Interfaz gráfica con **Tkinter** para lanzar y controlar scripts. Visualización de logs en tiempo real. Punto de entrada unificado para ejecutar el bot desde ventana en lugar de solo terminal.

**Herramientas:** Tkinter, `GUIController`.

---

### Módulo 10 — Integración y optimización

Visión general de cómo encajan todos los módulos: ventanas → imágenes → OCR → navegación → pathfinding → recursos → combate → GUI. Cierre del curso y repaso del flujo completo del sistema.

**Herramientas:** integración de componentes, arquitectura del proyecto.

---

## Estructura del repositorio

```
curso-automacion-python/
├── common/                 # Overlay, zona de pantalla, calibración compartida
├── 01_fundamentos_instalacion/
├── 02_deteccion_ventanas/
├── 03_reconocimiento_imagenes/
└── ...
```

Carpeta `common/`: código compartido entre módulos (no ejecutar sola; usar desde cada `main.py`).

---

## Flag útil

```bash
python main.py --overlay
```

Muestra un panel flotante con los mensajes del programa (útil mientras sigues el video).

---

## Enlaces

- **Canal:** [Script & Play HQ](https://www.youtube.com/@ScriptPlayHQ)
- **Playlist del curso:** *(añadir cuando la crees)*

---

## Licencia

Material educativo del curso. No redistribuir como producto comercial de botting.

---

*Curso en construcción — Script & Play HQ*
