#!/usr/bin/env sh
set -eu

echo "[worker] starting…"

# Чтобы импорты находили пакеты и при миграциях, и при запуске воркера
export PYTHONPATH="/app:/app/src:${PYTHONPATH:-}"

PG_HOST="${POSTGRES_HOST:-db}"
PG_PORT="${POSTGRES_PORT:-5432}"
echo "[worker] waiting for postgres at ${PG_HOST}:${PG_PORT}…"

# Ждём Postgres (без nc/pg_isready) — чистый Python socket
python - <<'PY'
import os, socket, time, sys
host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
deadline = time.time() + 120
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[worker] postgres is reachable")
            break
    except OSError:
        if time.time() > deadline:
            print(f"[worker] ERROR: cannot reach postgres at {host}:{port}", file=sys.stderr)
            sys.exit(1)
        time.sleep(0.5)
PY

# Ищем alembic.ini (как в app.entrypoint)
ALEMBIC_CONFIG_CANDIDATES="
/app/src/alembic.ini
/app/alembic.ini
/app/src/alembic/alembic.ini
"
ALEMBIC_CFG=""
for p in $ALEMBIC_CONFIG_CANDIDATES; do
  if [ -f "$p" ]; then
    ALEMBIC_CFG="$p"
    break
  fi
done

if [ -n "$ALEMBIC_CFG" ]; then
  echo "[worker] applying alembic migrations using ${ALEMBIC_CFG}…"
  alembic -c "${ALEMBIC_CFG}" upgrade head || {
    echo "[worker] WARNING: alembic upgrade failed; continuing (worker may fail if schema is missing)"
  }
else
  echo "[worker] WARNING: alembic.ini not found — skipping migrations"
fi

# Запуск воркера: логируем в stdout (пусть оркестратор собирает логи)
exec python -m src.app.workers.consumer
