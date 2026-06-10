"""
Modelo de datos para Operadores y Llamadas CDR.
Módulo: Telephony
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.shared.infrastructure.database import Base

class Operator(Base):
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PhoneCall(Base):
    __tablename__ = "phone_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(100), unique=True, index=True, nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    
    phone_number = Column(String(50))
    direction = Column(String(20))  # inbound, outbound
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    operator = relationship("Operator")
