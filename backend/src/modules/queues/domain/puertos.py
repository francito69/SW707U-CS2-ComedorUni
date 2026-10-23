from abc import ABC, abstractmethod


class RepositorioTurnos(ABC):
    @abstractmethod
    def obtener_ultimo_numero(self, turno_dia_id: int) -> int:
        pass

    @abstractmethod
    def guardar(self, estudiante_id: int, turno_dia_id: int, numero_turno: int) -> int:
        pass
