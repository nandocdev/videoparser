"""
Contrato para el módulo de Telephony.
Define cómo otros módulos pueden solicitar información de operadores y llamadas.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

class TelephonyContract(ABC):
    @abstractmethod
    def get_employee_id_by_username(self, username: str) -> Optional[int]:
        """
        Obtiene el ID interno de un empleado dado su username.
        """
        pass

    @abstractmethod
    def get_calls_by_employee_and_time(
        self, 
        employee_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las llamadas realizadas por un empleado en un rango de tiempo específico.
        """
        pass
