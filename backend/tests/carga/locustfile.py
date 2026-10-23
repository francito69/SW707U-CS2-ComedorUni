"""
Carga de "hora punta": todos los estudiantes piden turno casi a la vez y luego
consultan su estado mientras esperan.

    locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 1000 -r 200 -t 90s

Cada usuario de Locust es un estudiante distinto sembrado por preparar_datos.py
(mismo sid_de(i)). No usar más usuarios que estudiantes sembrados.
"""
import itertools
import os
import uuid

from locust import HttpUser, between, task

_siguiente = itertools.count()
TIPO = os.getenv("CARGA_TIPO", "PRUEBA")


def sid_de(i: int) -> str:
    return str(uuid.UUID(int=i + 1, version=4))  # igual que preparar_datos.sid_de


class Estudiante(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.sid = sid_de(next(_siguiente))
        self.client.get("/queue/active-service", name="GET /queue/active-service")

        with self.client.post("/queue/join", json={"sid": self.sid, "tipo": TIPO},
                              name="POST /queue/join", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 400 and "sin_raciones" in r.text:
                # Respuesta de negocio esperada cuando se acaban los cupos.
                r.request_meta["name"] = "POST /queue/join (sin raciones)"
                r.success()
            else:
                r.failure(f"{r.status_code}: {r.text[:120]}")
        self.tiene_turno = r.status_code == 200

    @task(5)
    def consultar_estado(self):
        if not self.tiene_turno:
            return
        self.client.get(f"/queue/status?sid={self.sid}", name="GET /queue/status")

    @task(1)
    def ver_menu(self):
        self.client.get("/menu", name="GET /menu")
