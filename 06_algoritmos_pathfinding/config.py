# Zona del juego (modal al arrancar, igual que módulos 4 y 5)
ZONA_IZQUIERDA = 0
ZONA_SUPERIOR = 0
ZONA_ANCHO = 0
ZONA_ALTO = 0

# Zona OCR coordenadas del mapa
OCR_IZQUIERDA = 0
OCR_SUPERIOR = 0
OCR_ANCHO = 0
OCR_ALTO = 0

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
RUTA_ZONA_JSON = "output/zona_captura_modulo6.json"
RUTA_ZONA_OCR_JSON = "output/zona_coordenadas_modulo6.json"

# Grafo mundial: casillas + bloqueos (data/mundo.json)
RUTA_MUNDO_JSON = "data/mundo.json"
# Fuentes para regenerar con generar_mundo.py
CATALOGO_RUTAS_FUENTE = "../setup_mapa_touch/output/catalog/bot/routes_by_position.json"
RUTA_BLOQUEOS_MANUAL = "routes/principal.json"  # retrocompat
RUTAS_BLOQUEOS_MANUAL = (
    "routes/principal.json",  # Bonta
    "routes/otomai.json",  # Otomai (copia de setup_mapa_touch/data/manual_direction_blocks/)
)

# Vacío = el usuario elige destino con click en el mapa
DESTINO_DEFAULT = ""

# Arrastre de cada paso de la ruta (centro de la zona del juego)
DRAG_PIXELES = 280
DRAG_DURACION = 0.75
PAUSA_ANTES_ARRASTRE = 1.0
PAUSA_TRAS_POSICIONAR_RATON = 0.3
PAUSA_TRAS_MOUSE_DOWN = 0.2

# Si el arrastre desde el centro no cambia mapa: probar esquinas del borde de salida
ARRASTRE_ABANICO_ACTIVO = True
ARRASTRE_ABANICO_MARGEN_FRACC = 0.15  # inset desde la esquina (15 % del ancho/alto)
# Tras un arrastre sin cambio OCR: pasar al siguiente origen del abanico (no esperar 45 s)
OCR_ESPERA_SIN_CAMBIO_ABANICO = 5.0
OCR_LECTURAS_IGUALES_ABANICO = 4
# Lecturas con coords distintas pero que no encajan con el paso (OCR adelantado) → siguiente origen
OCR_LECTURAS_INVALIDAS_ABORT = 6

# Espera tras cada arrastre (Phone Link — misma base que módulo 5)
PAUSA_MINIMA_TRAS_ARRASTRE = 1.5
OCR_INTERVALO_ESPERA = 0.5
OCR_ESPERA_MAXIMA = 45.0
OCR_LECTURAS_ESTABLES = 2
OCR_PAUSA_TRAS_CAMBIO = 1.2
OCR_REINTENTOS_ESPERA = 2
OCR_REINTENTOS_ARRASTRE = 2
OCR_PAUSA_ENTRE_REINTENTOS = 2.0
OCR_LOG_ESTADO_CADA = 8.0
# Comprueba que OCR leyó el vecino esperado del grafo (desactiva si da problemas)
VALIDAR_VECINO_PASO = True

# Lectura fiable — zona manual del modal (solo módulo 6)
OCR_PREFLIGHT_ACTIVO = True
OCR_VOTOS_LECTURAS = 3
OCR_VOTOS_MINIMO = 2
OCR_VOTOS_INTERVALO = 0.25
OCR_VALIDAR_EN_GRAFO = True

RUTA_TESSERACT = None
TESSERACT_CONFIG = r"--psm 6 -c tessedit_char_whitelist=-0123456789,"

SEGUNDOS_CUENTA_ATRAS = 5
LOG_DEPURACION = False
GUARDAR_RECORTE_OCR = True

PAUSA_TRAS_BUSCAR_VENTANA = 0.7
PAUSA_TRAS_ACTIVAR_VENTANA = 1.0
PAUSA_PANEL_LAYOUT = 0.25
PAUSA_ENTRE_BLOQUES = 1.5

PAUSA_TRAS_RESTAURAR = 0.35
PAUSA_TRAS_ACTIVAR = 0.55

PANEL_ACTIVO = False
# Panel flotante (--overlay): esquina superior DERECHA del monitor (no depende de la zona mapa).
PANEL_ANCLAR_MONITOR = True
PANEL_MARGEN_DERECHA_FRAC = 0.004
PANEL_POS_Y = 0.03
PANEL_ANCHO_FRAC = 0.22
PANEL_ALTO_FRAC = 0.72

ETIQUETAS_DIRECCION = {
    "left": "izquierda",
    "right": "derecha",
    "up": "arriba",
    "down": "abajo",
}
