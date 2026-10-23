import pytest
from src.modules.queues.service import calcular_turno_asignado


def test_calcular_turno_asignado_primeros_turnos():
    
    raciones_max = 100
   
    assert calcular_turno_asignado(1, raciones_max) == 1
    
    assert calcular_turno_asignado(10, raciones_max) == 1
    
    assert calcular_turno_asignado(11, raciones_max) == 2


def test_calcular_turno_asignado_ultimos_turnos():
    
    raciones_max = 100
    assert calcular_turno_asignado(95, raciones_max) == 10
    
    assert calcular_turno_asignado(100, raciones_max) == 10


def test_calcular_turno_asignado_capacidad_pequena():
    
    raciones_max = 5
    
    assert calcular_turno_asignado(1, raciones_max) == 1
    
    assert calcular_turno_asignado(3, raciones_max) == 3
