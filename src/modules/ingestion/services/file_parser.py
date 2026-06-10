"""
Servicio para parsear nombres de archivos de video.
Módulo: Ingestion
"""
import re
from datetime import datetime
from typing import Optional, Dict, Any

class VideoFileParser:
    # Patrón: {username} - {YYYY-MM-DD HH-MM-SS}.mp4
    # Ejemplo: f.castillo - 2024-06-10 14-30-00.mp4
    PATTERN = re.compile(r"^(?P<username>.+?) - (?P<date>\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2})\.mp4$")

    @classmethod
    def parse(cls, filename: str) -> Optional[Dict[str, Any]]:
        """
        Extrae el username y la fecha de grabación del nombre del archivo.
        """
        match = cls.PATTERN.match(filename)
        if not match:
            return None
        
        username = match.group("username")
        date_str = match.group("date")
        
        try:
            # El formato en el nombre usa guiones para la hora para evitar caracteres ilegales en archivos
            recording_date = datetime.strptime(date_str, "%Y-%m-%d %H-%M-%S")
            return {
                "username": username,
                "recording_date": recording_date
            }
        except ValueError:
            return None
