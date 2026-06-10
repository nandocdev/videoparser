"""
Servicio encargado de monitorear el directorio de subidas.
Módulo: Ingestion
"""
from pathlib import Path
from sqlalchemy.orm import Session
from loguru import logger

from src.shared.infrastructure.config import settings
from src.modules.ingestion.actions.register_file import RegisterUploadedFileAction
from src.modules.telephony.services.telephony_service import TelephonyService

class FileWatcherService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIRECTORY)
        # Inyectamos el servicio de Telephony como implementación del contrato
        self.telephony = TelephonyService(db)
        self.register_action = RegisterUploadedFileAction(db, self.telephony)

    def scan_for_new_files(self):
        """
        Escanea el directorio configurado buscando archivos .mp4 para procesar.
        """
        logger.debug(f"Escaneando directorio: {self.upload_dir}")
        
        if not self.upload_dir.exists():
            logger.warning(f"Directorio de subidas no encontrado: {self.upload_dir}. Creándolo...")
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            return

        files_found = 0
        for file_path in self.upload_dir.glob("*.mp4"):
            if file_path.is_file():
                result = self.register_action.execute(file_path)
                if result:
                    files_found += 1
        
        if files_found > 0:
            logger.info(f"Escaneo finalizado. Se registraron {files_found} archivos nuevos.")
