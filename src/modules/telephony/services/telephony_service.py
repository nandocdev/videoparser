"""
Implementación del contrato de Telephony.
Módulo: Telephony
"""
from typing import Optional
from sqlalchemy.orm import Session
from src.shared.contracts.telephony import TelephonyContract
from src.modules.telephony.models.phone_call import Operator

class TelephonyService(TelephonyContract):
    def __init__(self, db: Session):
        self.db = db

    def get_operator_id_by_code(self, code: str) -> Optional[int]:
        operator = self.db.query(Operator).filter(Operator.operator_code == code).first()
        return operator.id if operator else None
