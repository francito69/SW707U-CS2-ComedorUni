from src.modules.queues.domain.casos_uso import AsignarTurno
from src.modules.queues.infraestructura.adaptador_memoria import RepositorioTurnosMemoria


def test_asignar_primer_turno_en_memoria():
    repo = RepositorioTurnosMemoria()
    caso_uso = AsignarTurno(repo)
    numero = caso_uso.ejecutar(estudiante_id=101, turno_dia_id=1)
    assert numero == 1


def test_asignar_turnos_consecutivos_en_memoria():
    repo = RepositorioTurnosMemoria()
    caso_uso = AsignarTurno(repo)
    t1 = caso_uso.ejecutar(estudiante_id=101, turno_dia_id=1)
    t2 = caso_uso.ejecutar(estudiante_id=102, turno_dia_id=1)
    assert t1 == 1
    assert t2 == 2
