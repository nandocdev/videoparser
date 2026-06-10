"""
Worker de procesamiento asíncrono.
Orquesta los módulos de Ingestion y Processing.
"""
import time
from loguru import logger
from src.shared.infrastructure.config import settings
from src.shared.infrastructure.database import SessionLocal

def run_worker():
    logger.info("Iniciando CallQA Worker...")
    db = SessionLocal()
    
    try:
        while True:
            # Aquí vendrá la lógica de orquestación
            # 1. Ingestion: buscar nuevos archivos
            # 2. Telephony: sincronizar CDR si es necesario
            # 3. Processing: ejecutar pipeline
            
            logger.debug("Escaneando tareas...")
            time.sleep(settings.worker_check_interval)
            
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario.")
    finally:
        db.close()

if __name__ == "__main__":
    run_worker()
