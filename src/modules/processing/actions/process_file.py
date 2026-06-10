"""
Acción para procesar los archivos de video encolados.
Módulo: Processing
"""
from sqlalchemy.orm import Session
from loguru import logger

from src.modules.ingestion.models.uploaded_file import UploadedFile, ProcessingState
from src.modules.processing.services.correlator import CallCorrelator

class ProcessFileAction:
    def __init__(self, db: Session, correlator: CallCorrelator):
        self.db = db
        self.correlator = correlator

    def execute_next(self) -> bool:
        """
        Toma el siguiente archivo en estado RECEIVED de la base de datos y lo procesa.
        Retorna True si procesó un archivo, False si la cola estaba vacía.
        """
        # Usamos .with_for_update() para evitar race conditions si hubiera múltiples workers
        file_to_process = self.db.query(UploadedFile).filter(
            UploadedFile.state == ProcessingState.RECEIVED.value
        ).order_by(UploadedFile.created_at.asc()).with_for_update(skip_locked=True).first()

        if not file_to_process:
            return False

        logger.info(f"Iniciando procesamiento de archivo ID {file_to_process.id}: {file_to_process.filename}")
        
        try:
            # 1. Marcar como ANALYZING
            file_to_process.state = ProcessingState.ANALYZING.value
            self.db.commit()

            # 2. Ejecutar la correlación híbrida (OCR + Audio + FFmpeg)
            self.correlator.process_file_hybrido(file_to_process, self.db)
            
            # 3. Marcar como COMPLETED
            file_to_process.state = ProcessingState.COMPLETED.value
            self.db.commit()
            
            logger.success(f"Archivo ID {file_to_process.id} procesado exitosamente y marcado como COMPLETED.")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Fallo catastrófico procesando archivo ID {file_to_process.id}: {e}")
            
            # Intentar marcar como FAILED
            try:
                # Se necesita refrescar o buscar de nuevo la entidad tras el rollback
                file_to_fail = self.db.query(UploadedFile).get(file_to_process.id)
                if file_to_fail:
                    file_to_fail.state = ProcessingState.FAILED.value
                    file_to_fail.error_message = str(e)[:500] # Limitar tamaño del error
                    self.db.commit()
            except Exception as rollback_err:
                logger.error(f"Error al intentar marcar archivo como FAILED: {rollback_err}")
                self.db.rollback()
                
            return True # Retornamos True porque la cola sí tenía elementos
