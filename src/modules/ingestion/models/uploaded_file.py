"""
Modelo de datos para archivos subidos (Gestionado por Laravel).
Módulo: Ingestion
"""
from sqlalchemy import Column, BigInteger, String, DateTime, Enum as SQLEnum
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
    
    id = Column(BigInteger, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    
    # Referencia al ID de Employee del sistema WFM
    employee_id = Column(BigInteger, nullable=False, index=True)
    
    recording_date = Column(DateTime, nullable=False, index=True)
    state = Column(SQLEnum(ProcessingState), default=ProcessingState.RECEIVED)
    
    error_message = Column(String(500), nullable=True)
    
    # Timestamps estándar de Laravel (created_at, updated_at)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
