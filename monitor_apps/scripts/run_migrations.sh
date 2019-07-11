#!/usr/bin/env bash
cd ../src
~/sibay/bin/alembic revision --autogenerate -m "Added account table"
~/sibay/bin/alembic upgrade head