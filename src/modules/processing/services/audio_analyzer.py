"""
Servicio para análisis de audio y detección de patrones (ringtones).
Módulo: Processing
"""
import librosa
import numpy as np
from scipy import signal
from loguru import logger

class AudioAnalyzer:
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def find_ringtone_anchor(self, audio_path: str, template_path: str, start_search: float, end_search: float) -> float | None:
        """
        Busca un patrón de audio (ringtone) en un rango específico.
        Retorna el timestamp en segundos donde se detecta el match más fuerte.
        """
        try:
            # Cargar audio principal solo en el rango de búsqueda
            duration = end_search - start_search
            y, _ = librosa.load(audio_path, sr=self.sr, offset=start_search, duration=duration)
            
            # Cargar template
            y_template, _ = librosa.load(template_path, sr=self.sr)
            
            # Correlación cruzada (Cross-correlation) para encontrar el patrón
            correlation = signal.correlate(y, y_template, mode='valid')
            best_match_idx = np.argmax(correlation)
            
            # Convertir índice a tiempo relativo y luego absoluto
            relative_match_time = librosa.samples_to_time(best_match_idx, sr=self.sr)
            absolute_match_time = start_search + relative_match_time
            
            # Validar fuerza del match (umbral empírico)
            if correlation[best_match_idx] > 0.5: # Valor a calibrar
                return absolute_match_time
            
            return None
        except Exception as e:
            logger.error(f"Error en detección de ringtone: {e}")
            return None

    def detect_voice_activity(self, audio_path: str, start_time: float, duration: float) -> list[tuple[float, float]]:
        """
        Detecta segmentos de voz (VAD) en un rango de tiempo.
        """
        y, _ = librosa.load(audio_path, sr=self.sr, offset=start_time, duration=duration)
        
        # Usar intervalos de energía para detectar voz
        intervals = librosa.effects.split(y, top_db=30)
        
        segments = []
        for start, end in intervals:
            s_sec = start_time + librosa.samples_to_time(start, sr=self.sr)
            e_sec = start_time + librosa.samples_to_time(end, sr=self.sr)
            segments.append((s_sec, e_sec))
            
        return segments
