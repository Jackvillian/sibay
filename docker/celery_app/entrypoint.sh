#!/usr/bin/env bash
set -e

if [ "$1" = 'migrate' ]; then
    cd /usr/src/app && alembic revision --autogenerate -m "Migrations"
    cd /usr/src/app && alembic upgrade head
    echo "Execute Migrations ..."
fi
cd /usr/src/app && exec celery  -A worker_app worker -E