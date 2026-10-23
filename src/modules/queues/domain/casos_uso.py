from .puertos import RepositorioTurnos


class AsignarTurno:
    def __init__(self, repositorio: RepositorioTurnos):
        self.repositorio = repositorio

    def ejecutar(self, estudiante_id: int, turno_dia_id: int) -> int:
        ultimo = self.repositorio.obtener_ultimo_numero(turno_dia_id)
        siguiente = ultimo + 1
        return self.repositorio.guardar(estudiante_id, turno_dia_id, siguiente)
