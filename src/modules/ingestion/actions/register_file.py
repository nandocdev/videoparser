"""
Acción para registrar un nuevo archivo de video subido.
Módulo: Ingestion
"""
from sqlalchemy.orm import Session
from pathlib import Path
from loguru import logger
from typing import Optional

from src.modules.ingestion.models.uploaded_file import UploadedFile, ProcessingState
from src.modules.ingestion.services.file_parser import VideoFileParser
from src.shared.contracts.telephony import TelephonyContract

class RegisterUploadedFileAction:
    def __init__(self, db: Session, telephony_module: TelephonyContract):
        self.db = db
        self.telephony = telephony_module

    def execute(self, file_path: Path) -> Optional[UploadedFile]:
        """
        Registra el archivo en la base de datos si es válido y no existe.
        """
        filename = file_path.name
        parsed_info = VideoFileParser.parse(filename)
        
        if not parsed_info:
            logger.warning(f"Formato de archivo inválido, omitiendo: {filename}")
            return None
        
        # Obtener ID del empleado mediante el contrato de Telephony
        employee_id = self.telephony.get_employee_id_by_username(parsed_info["username"])
        
        if not employee_id:
            logger.error(f"Empleado '{parsed_info['username']}' no encontrado en WFM. Archivo: {filename}")
            return None
            
        # Verificar si el archivo ya fue registrado previamente
        existing = self.db.query(UploadedFile).filter(
            UploadedFile.file_path == str(file_path)
        ).first()
        
        if existing:
            logger.debug(f"Archivo ya registrado: {filename}")
            return existing
            
        try:
            new_file = UploadedFile(
                filename=filename,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                employee_id=employee_id,
                recording_date=parsed_info["recording_date"],
                state=ProcessingState.RECEIVED
            )
            
            self.db.add(new_file)
            self.db.commit()
            self.db.refresh(new_file)
            
            logger.success(f"Archivo registrado: {filename} (Operador ID: {operator_id})")
            return new_file
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al registrar archivo {filename}: {str(e)}")
            return None
