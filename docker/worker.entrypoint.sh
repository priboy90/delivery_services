#!/usr/bin/env sh
set -eu

echo "[worker] starting…"

export PYTHONPATH="/app:/app/src:${PYTHONPATH:-}"

PG_HOST="${POSTGRES_HOST:-db}"
PG_PORT="${POSTGRES_PORT:-5432}"
echo "[worker] waiting for postgres at ${PG_HOST}:${PG_PORT}…"

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

exec python -m src.app.workers.consumer
