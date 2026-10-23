"""
Siembra la infra de carga (docker-compose.carga.yml) y verifica su consistencia.

    python preparar_datos.py sembrar  --estudiantes 2000 --raciones 500
    python preparar_datos.py verificar --raciones 500

`sembrar` crea N estudiantes con su sesión en Redis (sid = sid_de(i), el mismo
que calcula locustfile.py), deja el turno PRUEBA de hoy con `raciones` cupos y
vacía la cola.
`verificar` revisa lo que la carga dejó en la base: duplicados, huecos en la
numeración y si se entregaron más turnos que raciones.
"""
import argparse
import json
import os
import uuid

import psycopg2
import redis

PG = dict(host="localhost", port=int(os.getenv("CARGA_PG_PORT", "5434")),
          dbname="comedor_uni", user="postgres", password="postgres")
RD = dict(host="localhost", port=int(os.getenv("CARGA_REDIS_PORT", "6380")), decode_responses=True)


def codigo(i: int) -> str:
    return f"CARGA{i:05d}"


def sid_de(i: int) -> str:
    # UUID v4 válido y determinista: la API solo acepta sids con forma uuid4.
    return str(uuid.UUID(int=i + 1, version=4))


def turno_prueba_id(cur) -> int:
    cur.execute(
        """SELECT td.id FROM turno_dia td JOIN turnos_config tc ON tc.id = td.config_id
           WHERE tc.tipo = 'PRUEBA' AND td.fecha = (NOW() AT TIME ZONE 'America/Lima')::DATE"""
    )
    return cur.fetchone()[0]


def sembrar(n: int, raciones: int) -> None:
    conn = psycopg2.connect(**PG)
    with conn, conn.cursor() as cur:
        tid = turno_prueba_id(cur)
        cur.execute("DELETE FROM historial_encolamiento")
        cur.execute("DELETE FROM historial_asistencia")
        cur.execute("DELETE FROM turnos")
        cur.execute("UPDATE turno_dia SET raciones_max = %s WHERE id = %s", (raciones, tid))
        cur.executemany(
            """INSERT INTO estudiantes (codigo, nombres, apellido_paterno, email)
               VALUES (%s, 'Estudiante', 'Carga', %s) ON CONFLICT (codigo) DO NOTHING""",
            [(codigo(i), f"{codigo(i).lower()}@carga.local") for i in range(n)],
        )
    conn.close()

    r = redis.Redis(**RD)
    pipe = r.pipeline()
    for i in range(n):
        c = codigo(i)
        sid = sid_de(i)
        pipe.set(f"session:{sid}", json.dumps(
            {"codigo": c, "email": f"{c.lower()}@carga.local", "nombre": "Estudiante Carga",
             "creditos": 0, "foto_base64": "", "device_id": "carga"}), ex=8 * 3600)
        pipe.set(f"user_session:{c}", sid, ex=8 * 3600)
    pipe.execute()
    print(f"OK: {n} estudiantes con sesión, turno PRUEBA (id={tid}) con {raciones} raciones")


def verificar(raciones: int) -> None:
    conn = psycopg2.connect(**PG)
    with conn.cursor() as cur:
        tid = turno_prueba_id(cur)
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT numero_turno), COALESCE(MAX(numero_turno),0), "
                    "COUNT(DISTINCT estudiante_id) FROM turnos WHERE turno_dia_id = %s", (tid,))
        total, distintos, maximo, estudiantes = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM turnos WHERE turno_dia_id = %s AND estado != 'CANCELADO'", (tid,))
        activos = cur.fetchone()[0]
    conn.close()

    print(f"Turnos creados:            {total}")
    print(f"Números distintos:         {distintos}  (duplicados: {total - distintos})")
    print(f"Estudiantes distintos:     {estudiantes}  (turno doble: {total - estudiantes})")
    print(f"Huecos en la numeración:   {maximo - distintos}  (máximo = {maximo})")
    print(f"Turnos activos / raciones: {activos} / {raciones}  "
          f"({'SOBREVENTA de ' + str(activos - raciones) if activos > raciones else 'sin sobreventa'})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("accion", choices=["sembrar", "verificar"])
    p.add_argument("--estudiantes", type=int, default=2000)
    p.add_argument("--raciones", type=int, default=500)
    a = p.parse_args()
    sembrar(a.estudiantes, a.raciones) if a.accion == "sembrar" else verificar(a.raciones)
