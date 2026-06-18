# Zona de trabajo (se marca al arrancar, igual que módulos 1–3)
ZONA_IZQUIERDA = 0
ZONA_SUPERIOR = 0
ZONA_ANCHO = 0
ZONA_ALTO = 0

PAUSA_ENTRE_ACCIONES = 0.55
SEGURIDAD_ESQUINA = True

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

CARPETA_SALIDA = "output"
RUTA_ZONA_JSON = "output/zona_captura_modulo4.json"
RUTA_ZONA_OCR_JSON = "output/zona_coordenadas_modulo4.json"
ARCHIVO_RECORTE_OCR = "recorte_coordenadas.png"

# Recorte de coordenadas (se rellena en el modal de calibración)
OCR_IZQUIERDA = 0
OCR_SUPERIOR = 0
OCR_ANCHO = 0
OCR_ALTO = 0

# Windows: si Tesseract no está en el PATH, pon la ruta completa, por ejemplo:
# RUTA_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
RUTA_TESSERACT = None

# PSM 6: bloque de texto (varias líneas). Whitelist: dígitos, coma y menos.
TESSERACT_CONFIG = r"--psm 6 -c tessedit_char_whitelist=-0123456789,"

SEGUNDOS_CUENTA_ATRAS = 5

# Segundos para que muevas el mapa a mano entre la 1.ª y la 2.ª lectura OCR
PAUSA_MANUAL_CAMBIO_MAPA = 10.0
CUENTA_ATRAS_CAMBIO_MAPA = True

LOG_DEPURACION = False
GUARDAR_RECORTE_OCR = True
ARCHIVO_RECORTE_OCR_2 = "recorte_coordenadas_2.png"
ABRIR_CARPETA_AL_FINAL = False

PAUSA_TRAS_BUSCAR_VENTANA = 0.7
PAUSA_TRAS_ACTIVAR_VENTANA = 1.0
PAUSA_PANEL_LAYOUT = 0.25
PAUSA_ENTRE_BLOQUES = 2.0

PAUSA_TRAS_RESTAURAR = 0.35
PAUSA_TRAS_ACTIVAR = 0.55
PAUSA_ANTES_CLIC = 0.45

PANEL_ACTIVO = False
PANEL_POS_X = 0.72
PANEL_POS_Y = 0.08
PANEL_ANCHO_FRAC = 0.26
PANEL_ALTO_FRAC = 0.58
