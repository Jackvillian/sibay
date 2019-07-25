#!/usr/bin/env bash
set -e
if [[ ${MIGRATIONS}==1]]; then
    echo "Execute Migrations ..."
    cd /usr/src/app && alembic upgrade head
fi
/usr/bin/supervisord -n -c /etc/supervisor/supervisor.conf