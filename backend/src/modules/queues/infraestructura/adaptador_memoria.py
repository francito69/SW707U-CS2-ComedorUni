from ..domain.puertos import RepositorioTurnos


class RepositorioTurnosMemoria(RepositorioTurnos):
    def __init__(self):
        self.turnos=[]

    def obtener_ultimo_numero(self, turno_dia_id):
        maximo=0
        for t in self.turnos:
            if t["turno_dia_id"]==turno_dia_id:
                if t["numero_turno"]>maximo:
                    maximo=t["numero_turno"]
        return maximo

    def guardar(self, estudiante_id, turno_dia_id, numero_turno):
        self.turnos.append({
            "estudiante_id": estudiante_id,
            "turno_dia_id": turno_dia_id,
            "numero_turno": numero_turno
        })
        return numero_turno

