from fastapi import FastAPI, Header, HTTPException
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = FastAPI()

try:
    redis_client = redis.Redis(host='redis-cache', port=6379, db=0, decode_responses=True)
    db_params = {
        "host": "postgres-db",        
        "database": "comedor_db",     
        "user": "postgres",           
        "password": "password123",     
        "port": 5432                  
    }
except Exception as e:
    print(f"Error inicializando conexiones: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok", "modulo": "M7-Configuracion"}

# 🔹 1. CONSULTAR CONFIGURACIÓN (GET) - Estrategia Cache-Aside
@app.get("/api/v1/configuracion")
def get_configuracion():
    try:
        cached_data = redis_client.get("comedor_config")
        if cached_data:
            return {"source": "cache-redis", "data": json.loads(cached_data)}
    except Exception:
        pass 

    try:
        conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("SELECT version, max_aforo_comedor, tiempo_max_confirmacion_min, tiempo_tolerancia_expiracion_min FROM configuracion ORDER BY version DESC LIMIT 1;")
            row = cur.fetchone()
        conn.close()
        
        if row:
            try:
                redis_client.setex("comedor_config", 180, json.dumps(row))
            except Exception:
                pass
            return {"source": "database-postgres", "data": row}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")

    return {"message": "No hay configuraciones iniciales."}

# 🔹 2. MODIFICAR CONFIGURACIÓN (POST) - Caso de Uso Crítico
@app.post("/api/v1/configuracion")
def update_configuracion(body: dict, x_consumer_username: str = Header(None)):
    if not x_consumer_username:
        raise HTTPException(status_code=403, detail="Acceso denegado: No se pudo verificar la gobernabilidad desde el Gateway.")

    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO configuracion (version, max_aforo_comedor, tiempo_max_confirmacion_min, tiempo_tolerancia_expiracion_min, modificado_por) 
                   VALUES (%s, %s, %s, %s, %s);""",
                (body.get('version', 1), body.get('max_aforo_comedor', 1200), body.get('tiempo_max_confirmacion_min', 15), body.get('tiempo_tolerancia_expiracion_min', 5), x_consumer_username)
            )
            conn.commit()
        conn.close()
        
        try:
            redis_client.delete("comedor_config")
        except Exception:
            pass
            
        return {"status": "success", "message": "Configuracion actualizada con exito. Cache invalidada.", "operador": x_consumer_username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar configuracion: {str(e)}")