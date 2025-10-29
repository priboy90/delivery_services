#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] starting app…"

# Чтобы импорты находили пакеты и при миграциях, и при запуске сервера
export PYTHONPATH="/app:/app/src:${PYTHONPATH:-}"

PG_HOST="${POSTGRES_HOST:-db}"
PG_PORT="${POSTGRES_PORT:-5432}"
echo "[entrypoint] waiting for postgres at ${PG_HOST}:${PG_PORT}…"

# Ждём Postgres без nc/pg_isready — чистый Python socket
python - <<'PY'
import os, socket, time, sys
host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
deadline = time.time() + 120
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] postgres is reachable")
            break
    except OSError:
        if time.time() > deadline:
            print(f"[entrypoint] ERROR: cannot reach postgres at {host}:{port}", file=sys.stderr)
            sys.exit(1)
        time.sleep(0.5)
PY

# Ищем alembic.ini
ALEMBIC_CONFIG_CANDIDATES=(
  "/app/src/alembic.ini"
  "/app/alembic.ini"
  "/app/src/alembic/alembic.ini"
)

ALEMBIC_CFG=""
for p in "${ALEMBIC_CONFIG_CANDIDATES[@]}"; do
  if [[ -f "$p" ]]; then
    ALEMBIC_CFG="$p"
    break
  fi
done

if [[ -z "${ALEMBIC_CFG}" ]]; then
  echo "[entrypoint] ERROR: alembic.ini not found. Looked at:"
  for p in "${ALEMBIC_CONFIG_CANDIDATES[@]}"; do echo "  - $p"; done
  echo "[entrypoint] If your alembic.ini is elsewhere, set ALEMBIC_CONFIG env var or move the file."
  exit 1
fi

echo "[entrypoint] applying alembic migrations using ${ALEMBIC_CFG}…"
alembic -c "${ALEMBIC_CFG}" upgrade head

# Какой модуль грузить uvicorn (по умолчанию — src.app.main:app)
UVICORN_APP="${UVICORN_APP:-src.app.main:app}"
PORT="${PORT:-8000}"

echo "[entrypoint] launching uvicorn on 0.0.0.0:${PORT}"
exec uvicorn "${UVICORN_APP}" --host 0.0.0.0 --port "${PORT}"
