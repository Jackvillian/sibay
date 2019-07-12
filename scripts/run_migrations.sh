#!/usr/bin/env bash
cd monitor_apps
~/sibay/bin/alembic revision --autogenerate -m "update all tables"
~/sibay/bin/alembic upgrade head