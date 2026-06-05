"""Utilidades compartidas entre módulos del curso."""

from .menu_calibracion_doble import (
    ResultadoCalibracionDoble,
    aplicar_zona_ocr_en_config,
    mostrar_menu_calibracion_doble,
)
from .overlay import GameLogOverlay
from .zona_pantalla import (
    EleccionCaptura,
    aplicar_zona_en_config,
    calibrar_zona_al_inicio,
    capturar_pantalla_en_zona,
    cargar_zona_captura_json,
    describir_zona,
    guardar_zona_captura_json,
    menu_captura_basico,
    seleccionar_rectangulo_pantalla,
)

__all__ = [
    "ResultadoCalibracionDoble",
    "aplicar_zona_ocr_en_config",
    "mostrar_menu_calibracion_doble",
    "GameLogOverlay",
    "EleccionCaptura",
    "aplicar_zona_en_config",
    "calibrar_zona_al_inicio",
    "capturar_pantalla_en_zona",
    "cargar_zona_captura_json",
    "describir_zona",
    "guardar_zona_captura_json",
    "menu_captura_basico",
    "seleccionar_rectangulo_pantalla",
]
