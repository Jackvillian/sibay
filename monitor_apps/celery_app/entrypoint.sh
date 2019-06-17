#!/usr/bin/env bash
cd /usr/src/app && exec celery  -A worker_app worker -E