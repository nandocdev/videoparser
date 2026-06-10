"""
Modelos del sistema WFM (Read-Only desde Python).
Módulo: Telephony
"""
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from src.shared.infrastructure.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(BigInteger, primary_key=True, index=True)
    employee_number = Column(String(20), unique=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    cisco_username = Column(String(255), unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    metadata_json = Column("metadata", JSON) # Mapeo de la columna 'metadata' de Laravel

class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(BigInteger, primary_key=True, index=True)
    cisco_call_id = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=False)
    ivr_started_at = Column(DateTime, nullable=False)
    talk_time = Column(BigInteger, default=0) # en segundos
    employee_id = Column(BigInteger, ForeignKey("employees.id"))
    status = Column(String(255), default="pending_operator")
    
    employee = relationship("Employee")
