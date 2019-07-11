#!/usr/bin/env bash
cd /usr/src/app && alembic revision --autogenerate -m "Migrations"
cd /usr/src/app && alembic upgrade head
echo "Migrations ..."
cd /usr/src/app && exec celery  -A worker_app worker -E