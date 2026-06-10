"""
Worker de procesamiento asíncrono.
Orquesta los módulos de Ingestion y Processing.
"""
import time
from loguru import logger
from src.shared.infrastructure.config import settings
from src.shared.infrastructure.database import SessionLocal

from src.modules.ingestion.services.file_watcher import FileWatcherService

def run_worker():
    logger.info("Iniciando CallQA Worker...")
    db = SessionLocal()
    
    # Inicializar servicios
    file_watcher = FileWatcherService(db)
    
    try:
        while True:
            # 1. Ingestion: buscar nuevos archivos y registrarlos
            file_watcher.scan_for_new_files()
            
            # 2. Telephony: sincronizar CDR (Pendiente implementar CDRSyncAction)
            
            # 3. Processing: ejecutar pipeline (Pendiente implementar ProcessingPipeline)
            
            time.sleep(settings.WORKER_CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario.")
    finally:
        db.close()

if __name__ == "__main__":
    run_worker()
