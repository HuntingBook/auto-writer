#!/bin/sh
set -e

cd /app
export PYTHONPATH=/app

if [ "${AUTO_WRITER_SKIP_MIGRATIONS:-0}" != "1" ]; then
  try=0
  until alembic upgrade head; do
    try=$((try+1))
    if [ "$try" -ge 30 ]; then
      exit 1
    fi
    sleep 1
  done

  python -c "from app.db.init_db import run_seed; run_seed()"
fi

exec "$@"
