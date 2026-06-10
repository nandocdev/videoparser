"""
Contrato para el módulo de Telephony.
Define cómo otros módulos pueden solicitar información de operadores y llamadas.
"""
from abc import ABC, abstractmethod
from typing import Optional

class TelephonyContract(ABC):
    @abstractmethod
    def get_operator_id_by_code(self, code: str) -> Optional[int]:
        """
        Obtiene el ID interno de un operador dado su código (username).
        """
        pass
