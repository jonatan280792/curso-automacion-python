# Se rellenan al marcar la zona al arrancar main.py
ZONA_IZQUIERDA = 0
ZONA_SUPERIOR = 0
ZONA_ANCHO = 0
ZONA_ALTO = 0

PAUSA_ENTRE_ACCIONES = 0.45
SEGURIDAD_ESQUINA = True  # Mover ratón a esquina = parar (PyAutoGUI)

# pygetwindow: el título de la ventana debe contener alguna de estas cadenas
TITULOS_VENTANA = (
    "DOFUS Touch",
    "Dofus Touch",
    "Phone Link",
    "Vínculo con el teléfono",
    "Link to Windows",
    "Enlace con el teléfono",
)

TITULOS_VENTANA_PRIORIDAD = (
    "DOFUS Touch",
    "Dofus Touch",
)

VENTANA_MIN_ANCHO = 400
VENTANA_MIN_ALTO = 320
VENTANA_MIN_ANCHO_RELAX = 280
VENTANA_MIN_ALTO_RELAX = 240
UMBRAL_FUERA_PANTALLA = -28000
VENTANA_DIMINUTA_ANCHO = 120
VENTANA_DIMINUTA_ALTO = 80

# Márgenes de clics dentro de la zona marcada (0.0 a 1.0)
CLIC_MARGEN_IZQ = 0.22
CLIC_MARGEN_DER = 0.78
CLIC_MARGEN_ARRIBA = 0.22
CLIC_MARGEN_ABAJO = 0.78

CARPETA_TEMP = "temp"
CARPETA_IMAGENES = "images"
CARPETA_SALIDA = "output"
ARCHIVO_CAPTURA = "captura_modulo1.png"
RUTA_ZONA_JSON = "output/zona_captura_modulo1.json"
PAUSA_ANTES_CAPTURA = 0.55

# Segundos tras ejecutar main.py antes del rectángulo gris (minimizar IDE, dejar Dofus visible)
PAUSA_ANTES_CALIBRAR_ZONA = 2.0

SEGUNDOS_CUENTA_ATRAS = 4
ABRIR_CARPETA_AL_FINAL = True
LOG_DEPURACION = False

PANEL_ACTIVO = False
PANEL_POS_X = 0.72
PANEL_POS_Y = 0.08
PANEL_ANCHO_FRAC = 0.26
PANEL_ALTO_FRAC = 0.58
