"""
Modelos para segmentos detectados y clips procesados.
Módulo: Processing
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from datetime import datetime
from src.shared.infrastructure.database import Base

class CallSegment(Base):
    __tablename__ = "call_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    uploaded_file_id = Column(Integer, nullable=False, index=True)
    
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # ID de la llamada CDR (Referencia al módulo Telephony)
    phone_call_id = Column(Integer, nullable=True, index=True)
    correlation_confidence = Column(Float, nullable=True)
    
    detected_at = Column(DateTime, default=datetime.utcnow)

class ProcessedClip(Base):
    __tablename__ = "processed_clips"
    
    id = Column(Integer, primary_key=True, index=True)
    uploaded_file_id = Column(Integer, nullable=False, index=True)
    call_segment_id = Column(Integer, nullable=True, index=True)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    
    start_time_seconds = Column(Float, nullable=False)
    end_time_seconds = Column(Float, nullable=False)
    
    metadata_json = Column(JSON, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.utcnow)
