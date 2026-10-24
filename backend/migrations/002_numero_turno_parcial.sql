-- Aplica a bases ya creadas el cambio de 001_init.sql: el número de turno solo
-- es único entre turnos NO cancelados, para que crear_turno pueda reasignar el
-- número de quien salió de la cola (MAX sin contar CANCELADOS + 1).
-- Idempotente: se puede correr más de una vez.
DROP INDEX IF EXISTS idx_turnos_numero_turno_unico;
CREATE UNIQUE INDEX idx_turnos_numero_turno_unico
ON turnos (turno_dia_id, numero_turno)
WHERE estado != 'CANCELADO';
