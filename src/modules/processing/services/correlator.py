"""
Orquestador de la estrategia híbrida de correlación.
Módulo: Processing
"""
from loguru import logger
from datetime import datetime, timedelta
from pathlib import Path

from src.shared.contracts.telephony import TelephonyContract
from src.modules.processing.services.ocr_service import OCRService
from src.modules.processing.services.audio_analyzer import AudioAnalyzer
from src.shared.utils.video_utils import VideoUtils
from src.modules.ingestion.models.uploaded_file import UploadedFile

class CallCorrelator:
    def __init__(self, telephony: TelephonyContract, settings):
        self.telephony = telephony
        self.settings = settings
        self.ocr = OCRService()
        self.audio = AudioAnalyzer(settings.AUDIO_SAMPLE_RATE)
        self.video = VideoUtils()

    def process_file_hybrido(self, uploaded_file: UploadedFile, db_session):
        """
        Ejecuta la estrategia híbrida sobre un archivo de video.
        """
        logger.info(f"Iniciando correlación híbrida para: {uploaded_file.filename}")
        
        # 1. Calibración Visual (OCR) inicial
        # Extraemos un frame al segundo 5 para leer el reloj
        temp_frame = Path(self.settings.TEMP_DIRECTORY) / f"calib_{uploaded_file.id}.jpg"
        self.video.extract_frame(uploaded_file.file_path, 5.0, str(temp_frame))
        
        real_time_on_screen = self.ocr.read_clock_from_frame(str(temp_frame))
        # Si el OCR falla, usamos el recording_date del archivo como fallback
        initial_offset = 0
        if real_time_on_screen:
            # Calcular desfase entre el nombre del archivo y la realidad en pantalla
            expected_time = uploaded_file.recording_date + timedelta(seconds=5)
            # Simplificación: solo comparamos segundos de diferencia en el mismo día
            initial_offset = (real_time_on_screen - expected_time).total_seconds()
            logger.info(f"Calibración visual: Desfase detectado de {initial_offset}s")

        # 2. Obtener llamadas del CDR para este empleado en esa hora
        end_recording = uploaded_file.recording_date + timedelta(hours=1)
        cdr_calls = self.telephony.get_calls_by_employee_and_time(
            uploaded_file.employee_id, 
            uploaded_file.recording_date, 
            end_recording
        )

        logger.info(f"Se encontraron {len(cdr_calls)} llamadas en el CDR para este periodo.")

        # 3. Para cada llamada, buscar el ancla de audio (Ringtone)
        for call in cdr_calls:
            # Calcular dónde debería estar la llamada en el video (segundos desde el inicio)
            time_since_start = (call['start_time'] - uploaded_file.recording_date).total_seconds()
            estimated_start_in_video = time_since_start + initial_offset
            
            # Buscar el ringtone en un rango de +/- 30 segundos del estimado
            # (Pendiente: necesitamos una ruta a un audio de ringtone template)
            # ringtone_timestamp = self.audio.find_ringtone_anchor(...)
            
            # Por ahora, usamos el estimado recalibrado por OCR
            logger.info(f"Estimación de clip para llamada {call['id']}: Inicia en {estimated_start_in_video}s")
            
            # 4. Generación del Clip (Corte con FFmpeg)
            output_name = f"clip_{call['id']}.mp4"
            output_path = Path(self.settings.CLIPS_OUTPUT_DIRECTORY) / output_name
            
            success = self.video.cut_clip(
                uploaded_file.file_path,
                max(0, estimated_start_in_video - 2), # 2s de margen antes
                call['talk_time'] + 10, # talk_time + margen después
                str(output_path)
            )
            
            if success:
                logger.success(f"Clip generado exitosamente: {output_name}")

        # Limpieza
        if temp_frame.exists():
            temp_frame.unlink()
