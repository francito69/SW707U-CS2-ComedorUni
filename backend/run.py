import os

# deepface emite un warning con emoji al importarse (ver DeepFace.py); en
# Windows, la consola por defecto usa una codepage (cp1252) que no puede
# codificar esos caracteres, y como esto ocurre a nivel de import, un
# UnicodeEncodeError ahí mata el arranque completo del proceso — sobre todo
# al subproceso que lanza el reloader (--reload), que no hereda el encoding
# de la terminal. Forzarlo antes de cualquier import evita el crash sin
# depender de que quien lo ejecute recuerde exportar la variable a mano.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv
load_dotenv()

import uvicorn

if __name__ == "__main__":
    workers = int(os.getenv("WORKERS", "1"))

    if workers > 1:
        # Modo producción (prueba de carga real): uvicorn no permite --reload
        # junto con workers > 1, y no lo necesitamos acá — cada worker es un
        # proceso separado, pensado para aprovechar varios núcleos de CPU.
        print(f"[run.py] Modo producción: {workers} workers, sin auto-reload", flush=True)
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, workers=workers)
    else:
        # Modo desarrollo (por defecto, sin tocar nada): 1 proceso, recarga
        # automática al guardar un archivo.
        uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
