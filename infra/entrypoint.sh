#!/bin/sh
# Gnana web container entry point:
#   1. wait for Postgres to accept connections
#   2. apply migrations
#   3. seed demo users (idempotent)
#   4. exec whatever command comes in (default: runserver)
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "[web] waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."
python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        time.sleep(2)
else:
    sys.exit(f"Postgres at {host}:{port} never became reachable")
PY

echo "[web] Postgres is up."
echo "[web] applying migrations ..."
python manage.py migrate --noinput

echo "[web] seeding demo users ..."
python manage.py seed_demo_users

echo "[web] starting: $*"
exec "$@"
