FROM python:3.12-slim

# libgl1/libglib2.0-0: opencv-python (usado por deepface para detectar rostros)
# los necesita en tiempo de ejecución aunque no se use ninguna GUI.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# run.py decide el modo según WORKERS: >1 arranca varios procesos sin
# --reload (producción); si no se define, cae en modo desarrollo (1 proceso
# con auto-reload). docker-compose.prod.yml pasa WORKERS=BACKEND_WORKERS.
CMD ["python", "run.py"]
