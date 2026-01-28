FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ---- System dependencies ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies (Otimizado com Cache) ----
# 1. Primeiro, instalamos o que é pesado e raramente muda
COPY requirements-base.txt /app/requirements-base.txt
RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements-base.txt

# 2. Depois, instalamos os complementos/novas bibliotecas
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# ---- Setup de diretórios ----
RUN mkdir -p /app/logs /app/data /app/data/backups

# ---- Copy source code ----
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]