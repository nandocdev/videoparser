"""
Implementación del contrato de Telephony vinculada al sistema WFM.
Módulo: Telephony
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from src.shared.contracts.telephony import TelephonyContract
from src.modules.telephony.models.phone_call import Employee, AgentCallPerformance

class TelephonyService(TelephonyContract):
    def __init__(self, db: Session):
        self.db = db

    def get_employee_id_by_username(self, username: str) -> Optional[int]:
        """
        Busca el ID del empleado en la tabla maestra de WFM.
        """
        employee = self.db.query(Employee).filter(Employee.username == username).first()
        return employee.id if employee else None

    def get_calls_by_employee_and_time(
        self, 
        employee_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Obtiene registros de agent_call_performance para un empleado y rango horario.
        """
        calls = self.db.query(AgentCallPerformance).filter(
            AgentCallPerformance.employee_id == employee_id,
            AgentCallPerformance.start_time >= start_time,
            AgentCallPerformance.start_time <= end_time
        ).all()

        return [
            {
                "id": c.id,
                "start_time": c.start_time,
                "end_time": c.end_time,
                "talk_time": c.talk_time,
                "phone_number": c.phone_number,
                "csq_name": c.csq_name
            }
            for c in calls
        ]
