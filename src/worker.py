"""
Worker de procesamiento asíncrono.
Orquesta los módulos de Ingestion y Processing.
"""
import sys
from loguru import logger
from src.shared.infrastructure.config import settings
from src.shared.infrastructure.database import SessionLocal
from pathlib import Path
from src.modules.ingestion.services.file_watcher import FileWatcherService
from src.modules.processing.actions.process_file import ProcessFileAction
from src.modules.processing.services.correlator import CallCorrelator
from src.modules.telephony.services.telephony_service import TelephonyService

def ensure_storage_dirs():
    """Asegura que los directorios de almacenamiento existan."""
    dirs = [
        settings.UPLOAD_DIRECTORY,
        settings.CLIPS_OUTPUT_DIRECTORY,
        settings.TEMP_DIRECTORY
    ]
    for d in dirs:
        path = Path(d)
        if not path.exists():
            logger.info(f"Creando directorio de almacenamiento: {path}")
            path.mkdir(parents=True, exist_ok=True)

def run_batch():
    logger.info("Iniciando procesamiento Batch de CallQA...")

    # Asegurar infraestructura de carpetas
    ensure_storage_dirs()

    db = SessionLocal()

    # Inicializar servicios y acciones
    file_watcher = FileWatcherService(db)
    telephony_service = TelephonyService(db)
    correlator = CallCorrelator(telephony_service, settings)
    processor = ProcessFileAction(db, correlator)

    try:
        # 1. Ingestion: buscar nuevos archivos y registrarlos
        logger.info("Fase 1: Escaneando nuevos archivos...")
        file_watcher.scan_for_new_files()

        # 2. Processing: ejecutar pipeline en todos los archivos encolados
        logger.info("Fase 2: Procesando cola de archivos...")
        processed_count = 0
        while True:
            processed_any = processor.execute_next()
            if not processed_any:
                break
            processed_count += 1

        logger.success(f"Batch finalizado. Se procesaron {processed_count} archivos en total.")

    except Exception as e:
        logger.exception(f"Error crítico en la ejecución del batch: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    run_batch()
