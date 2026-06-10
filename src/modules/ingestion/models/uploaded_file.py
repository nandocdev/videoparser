"""
Modelo de datos para archivos subidos.
Módulo: Ingestion
"""
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Enum as SQLEnum
import enum
from datetime import datetime
from src.shared.infrastructure.database import Base

class ProcessingState(str, enum.Enum):
    RECEIVED = "received"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    # ID del operador (Referencia al módulo Telephony)
    operator_id = Column(Integer, nullable=False, index=True)
    
    recording_date = Column(DateTime, nullable=False)
    state = Column(SQLEnum(ProcessingState), default=ProcessingState.RECEIVED)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    error_message = Column(String(500), nullable=True)
