# backend/Dockerfile
#
# Dev-focused image:
# - python:3.10-slim
# - system deps for scientific libs + postgres drivers
# - installs Python deps from requirements.txt
# - prepares runtime dirs (logs/data)
# - runs uvicorn with --reload for hot reload via bind mount

FROM python:3.10-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ---- System dependencies (requested) ----
# build-essential pulls gcc/make and common toolchain.
# libpq-dev supports building/installing postgres-related libs if needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
# Copy only requirements first to leverage Docker layer caching.
COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# ---- Essential setup replicated from scripts (minimal) ----
# Create directories commonly assumed by the app/scripts:
# - /app/logs for server logs
# - /app/data for SQLite + datasets
# - /app/data/backups for DB backups (if used)
RUN mkdir -p /app/logs /app/data /app/data/backups

# Copy application source (optional for build; in docker-compose we also bind mount ./backend:/app)
# Keeping this COPY makes the image runnable even without volumes.
COPY . /app

EXPOSE 8000

# ---- Command (requested) ----
# NOTE: If your app entrypoint is actually "backend.api:app", adjust this line accordingly.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
