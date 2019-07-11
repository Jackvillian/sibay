#!/usr/bin/env bash
cd ../monitor_aps
~/sibay/bin/alembic revision --autogenerate -m "update all tables"
~/sibay/bin/alembic upgrade head