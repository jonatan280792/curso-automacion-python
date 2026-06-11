# Zona de trabajo (se marca al arrancar, igual que módulos 1 y 2)
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
CARPETA_PLANTILLAS = "images/plantillas"
RUTA_ZONA_JSON = "output/zona_captura_modulo3.json"

# Segundos tras poner el juego al frente antes del rectángulo gris
PAUSA_ANTES_CALIBRAR_ZONA = 2.0

# "zona" = rectángulo calibrado; "ventana" = toda la ventana del juego
BUSCAR_EN = "zona"

CONFIANZA_BUSQUEDA = 0.72

# Demo del video: buscar plantilla → clic → pausa → siguiente paso (todo en el log)
# Archivos en images/plantillas/{nombre}.png
DEMO_SECUENCIA = (
    ("inventario", "Abrir inventario"),
    ("cerrar", "Cerrar inventario"),
    ("caracteristicas", "Abrir características"),
)

PAUSA_ENTRE_PASOS_DEMO = 5.0
CUENTA_ATRAS_ENTRE_PASOS = True

SEGUNDOS_CUENTA_ATRAS = 5
LOG_DEPURACION = False
ABRIR_CARPETA_AL_FINAL = True

PAUSA_TRAS_BUSCAR_VENTANA = 0.7
PAUSA_TRAS_ACTIVAR_VENTANA = 1.0
PAUSA_PANEL_LAYOUT = 0.25
PAUSA_ENTRE_BLOQUES = 2.0
PAUSA_TRAS_CLIC = 0.8

PAUSA_TRAS_RESTAURAR = 0.35
PAUSA_TRAS_ACTIVAR = 0.55
PAUSA_ANTES_CLIC = 0.45

PANEL_ACTIVO = False
PANEL_POS_X = 0.72
PANEL_POS_Y = 0.08
PANEL_ANCHO_FRAC = 0.26
PANEL_ALTO_FRAC = 0.58
