"""
Modelos para segmentos detectados y clips procesados (Gestionado por Laravel).
Módulo: Processing
"""
from sqlalchemy import Column, BigInteger, String, Float, DateTime, JSON
from datetime import datetime
from src.shared.infrastructure.database import Base

class CallSegment(Base):
    __tablename__ = "call_segments"
    
    id = Column(BigInteger, primary_key=True, index=True)
    uploaded_file_id = Column(BigInteger, nullable=False, index=True)
    
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Referencia al ID de CallRecord del sistema WFM
    call_record_id = Column(BigInteger, nullable=True, index=True)
    correlation_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessedClip(Base):
    __tablename__ = "processed_clips"
    
    id = Column(BigInteger, primary_key=True, index=True)
    uploaded_file_id = Column(BigInteger, nullable=False, index=True)
    call_segment_id = Column(BigInteger, nullable=False, index=True)
    
    # Opcional: Referencia redundante para optimizar lecturas
    call_record_id = Column(BigInteger, nullable=True, index=True)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    
    metadata_json = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
