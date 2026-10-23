# Prueba de carga con Locust

Simula la hora punta del comedor: todos los estudiantes piden turno casi a la
vez (`POST /queue/join`) y luego consultan su estado (`GET /queue/status`) y el
menú (`GET /menu`) mientras esperan.

## Cómo correrla

Desde la raíz del repositorio:

```powershell
# 1. Infra aislada (otros puertos, datos en memoria: no toca el stack de desarrollo)
docker compose -f benchmarks/docker-compose.carga.yml up -d

# 2. Estudiantes de prueba con sesión en Redis y turno PRUEBA con N raciones
python benchmarks/preparar_datos.py sembrar --estudiantes 2000 --raciones 500
```

En otra terminal, desde la raíz del repositorio, el backend con 6 workers apuntando a esa infra:

```powershell
$env:DB_PORT="5434"; $env:DB_POOL_MAX="15"; $env:REDIS_PORT="6380"; $env:RABBITMQ_PORT="5673"; $env:WORKERS="6"
python run.py
```

Y la carga, más la verificación de consistencia al terminar:

```powershell
pip install locust
locust -f benchmarks/locustfile.py --host http://127.0.0.1:8000 --headless -u 1000 -r 200 -t 90s --html benchmarks/reporte.html
python benchmarks/preparar_datos.py verificar --raciones 500
docker compose -f benchmarks/docker-compose.carga.yml down
```

En Windows, usar `127.0.0.1` y no `localhost`: `localhost` intenta primero IPv6,
uvicorn solo escucha en IPv4, y cada conexión nueva paga ~2 s de reintento.

## Resultados (22-oct-2026, laptop de 20 núcleos / 16 GB, 6 workers, Python 3.12)

| Corrida | Usuarios | Req/s | Errores | `status` p95 | `join` p50 / p95 | Consistencia |
|---|---|---|---|---|---|---|
| Antes de corregir el pool (contra `localhost`) | 1000 | 190 | 11,7 % (500s) | 2,8 s | 0,74 s / 3,9 s | OK |
| Pool corregido | 1000 | 305 | 0 % | 64 ms | 0,83 s / 1,4 s | OK |
| **v1.0** (DB fuera del event loop) | 1000 | 306 | 1 conexión reseteada | 61 ms | 0,70 s / 1,2 s | OK |
| Pool corregido, estrés | 2000 | 590 | 0,7 % (conexiones abortadas, ningún 500) | 3,2 s | 0,73 s / 1,9 s | OK |
| **v1.0, estrés** | 2000 | 729 | 0,01 % (5 conexiones abortadas, ningún 500) | 0,41 s | 0,23 s / 0,68 s | OK |

"Consistencia OK" = en la base no hay números de turno duplicados, ningún
estudiante con dos turnos, numeración sin huecos y nunca más turnos que raciones.

**Lo que se corrigió en `shared/db.py`:**
- psycopg2 solo reutiliza una conexión devuelta si hay menos de `minconn`
  libres; con `minconn=1` cerraba y reabría una conexión TCP en casi cada
  request (agotaba puertos de Windows). Ahora `minconn` = `maxconn`.
- Con el pool lleno, `ThreadedConnectionPool` lanza "pool exhausted" (500) en
  vez de esperar. Ahora un semáforo hace esperar al request hasta
  `DB_POOL_TIMEOUT` segundos (10 por defecto).

**Lo que se corrigió después, en v1.0:**
- `POST /queue/join` era `async def` con llamadas síncronas a la base: mientras
  esperaba el candado `FOR UPDATE` congelaba el event loop de su worker. Ahora
  esa parte corre con `run_in_threadpool` (de ahí la mejora en el estrés).
- El chequeo de raciones estaba fuera del candado de `crear_turno` (carrera
  posible con la última ración). Ahora se cuenta dentro del candado; ver
  `test_concurrency.py`.

**Límite de la medición:** con 2000 usuarios, Locust y el backend comparten la
misma CPU. Para medir el techo real del sistema, Locust debería correr en otra máquina.
