"""
Servicio para extraer texto (reloj) de frames de video usando OCR.
Módulo: Processing
"""
import cv2
import pytesseract
from loguru import logger
from datetime import datetime
import re

class OCRService:
    def __init__(self, tesseract_cmd: str = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def read_clock_from_frame(self, image_path: str, roi: tuple = None) -> datetime | None:
        """
        Lee la hora del sistema desde un frame.
        roi: (x, y, w, h) para recortar el área del reloj.
        """
        image = cv2.imread(image_path)
        if image is None:
            return None

        # Recortar área de interés si se proporciona (ej: esquina inferior derecha)
        if roi:
            x, y, w, h = roi
            image = image[y:y+h, x:x+w]

        # Preprocesamiento básico para OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Binarización para resaltar texto blanco sobre fondo oscuro o viceversa
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # Configuración de tesseract: --psm 6 (asumir un bloque único de texto)
        try:
            text = pytesseract.image_to_string(thresh, config='--psm 6')
            return self._parse_time_string(text)
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return None

    def _parse_time_string(self, text: str) -> datetime | None:
        """
        Intenta encontrar un patrón de hora HH:MM:SS en el texto.
        """
        # Limpiar texto
        text = text.strip()
        # Buscar patrón HH:MM:SS o HH:MM
        match = re.search(r'(\d{1,2})[:\s](\d{2})[:\s]?(\d{2})?', text)
        if not match:
            return None
        
        # Por ahora solo retornamos una estructura simple para comparar offsets
        # En una implementación real, se debe normalizar a la fecha del video
        try:
            h, m = int(match.group(1)), int(match.group(2))
            s = int(match.group(3)) if match.group(3) else 0
            return datetime.now().replace(hour=h, minute=m, second=s, microsecond=0)
        except:
            return None
