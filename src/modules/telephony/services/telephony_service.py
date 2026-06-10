"""
Implementación del contrato de Telephony vinculada al sistema WFM.
Módulo: Telephony
"""
from typing import Optional
from sqlalchemy.orm import Session
from src.shared.contracts.telephony import TelephonyContract
from src.modules.telephony.models.phone_call import Employee

class TelephonyService(TelephonyContract):
    def __init__(self, db: Session):
        self.db = db

    def get_employee_id_by_username(self, username: str) -> Optional[int]:
        """
        Busca el ID del empleado en la tabla maestra de WFM.
        """
        employee = self.db.query(Employee).filter(Employee.username == username).first()
        return employee.id if employee else None
