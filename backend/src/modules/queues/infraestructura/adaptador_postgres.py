from ....shared.db import get_db_conn
from ..domain.puertos import RepositorioTurnos


class RepositorioTurnosPostgres(RepositorioTurnos):
    def obtener_ultimo_numero(self, turno_dia_id):
        conn=get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(numero_turno), 0) FROM turnos WHERE turno_dia_id = %s AND estado != 'CANCELADO'",
                    (turno_dia_id,)
                )
                return cur.fetchone()[0]
        finally:
            conn.close()

    def guardar(self, estudiante_id, turno_dia_id, numero_turno):
        conn=get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO turnos (estudiante_id, turno_dia_id, numero_turno) VALUES (%s, %s, %s) RETURNING numero_turno",
                    (estudiante_id, turno_dia_id, numero_turno)
                )
                numero=cur.fetchone()[0]
            conn.commit()
            return numero
        finally:
            conn.close()

