"""
Contrato para el módulo de Telephony.
Define cómo otros módulos pueden solicitar información de operadores y llamadas.
"""
from abc import ABC, abstractmethod
from typing import Optional

class TelephonyContract(ABC):
    @abstractmethod
    def get_employee_id_by_username(self, username: str) -> Optional[int]:
        """
        Obtiene el ID interno de un empleado dado su username.
        """
        pass
