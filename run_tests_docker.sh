#!/usr/bin/env bash
# run_tests_docker.sh
#
# QA runner (Linux/Git Bash compatible):
# 1) Verifies backend container is running
# 2) Verifies test dependencies (httpx, pytest-asyncio) exist inside container
# 3) Runs pytest against the mounted /app/tests directory

set -euo pipefail

# Prefer `docker compose`, fallback to `docker-compose`
dc() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

BACKEND_SERVICE="backend"

backend_container_id="$(dc ps -q "${BACKEND_SERVICE}" || true)"

if [[ -z "${backend_container_id}" ]]; then
  echo "[ERROR] Backend service is not created or not started."
  echo "Start it with:"
  echo "  $(basename "$0") (after running: docker compose up -d backend)"
  echo "Or run:"
  echo "  docker compose up -d backend"
  exit 1
fi

is_running="$(docker inspect -f '{{.State.Running}}' "${backend_container_id}" 2>/dev/null || echo "false")"
if [[ "${is_running}" != "true" ]]; then
  echo "[ERROR] Backend container exists but is not running."
  echo "Start it with:"
  echo "  docker compose up -d backend"
  exit 1
fi

echo "[OK] Backend container is running: ${backend_container_id}"

# Verify pytest is installed (should be in requirements.txt, but we validate anyway)
if ! dc exec -T "${BACKEND_SERVICE}" python -c "import pytest" >/dev/null 2>&1; then
  echo "[ERROR] pytest is not available inside the backend container."
  echo "Install it inside the container (temporary) with:"
  echo "  docker compose exec backend pip install pytest"
  echo "Preferably, add pytest to backend/requirements.txt (or a requirements-dev.txt) and rebuild."
  exit 1
fi

# Verify common test deps (requested)
missing_deps=0
if ! dc exec -T "${BACKEND_SERVICE}" python -c "import httpx" >/dev/null 2>&1; then
  echo "[WARN] Missing dependency: httpx"
  missing_deps=1
fi
if ! dc exec -T "${BACKEND_SERVICE}" python -c "import pytest_asyncio" >/dev/null 2>&1; then
  echo "[WARN] Missing dependency: pytest-asyncio"
  missing_deps=1
fi

if [[ "${missing_deps}" -eq 1 ]]; then
  echo
  echo "[ACTION REQUIRED] Install missing test dependencies inside the container:"
  echo "  docker compose exec backend pip install httpx pytest-asyncio"
  echo
  echo "Better (recommended): add them to backend/requirements.txt or create backend/requirements-dev.txt"
  echo "and rebuild the image:"
  echo "  docker compose build backend"
  exit 1
fi

# Run tests
# Assumes docker-compose.yml mounts ./tests -> /app/tests
echo "[INFO] Running pytest..."
dc exec -T "${BACKEND_SERVICE}" pytest -q /app/tests
echo "[OK] Tests completed."
