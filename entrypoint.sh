#!/usr/bin/env sh
set -e

# migrate
if [ "$1" = "migrate" ]; then
  echo "Running migrations…"
  alembic upgrade head
  exit 0
fi

# seed
if [ "$1" = "seed" ]; then
  echo "Running all seeders…"
  python app/seeders/run_all_seeders.py
  exit 0
fi


exec "$@"
