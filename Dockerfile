# Imagen de la API (Python 3.12 + FastAPI)
FROM python:3.12-slim

WORKDIR /app

# 1. Dependencias (se cachean mientras requirements.txt no cambie)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Código de la API
COPY app ./app

EXPOSE 3000

# Al arrancar: crea la tabla si falta, asegura el admin y levanta la API
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
