#!/usr/bin/env bash
tag=$1
cd docker/celery_app
docker build -t celery_app .
docker tag celery_app jacvmos/celery_app:$tag
docker push jacvmos/celery_app
cd ../../docker/push_app
docker build -t push_app .
docker tag push_app jacvmos/push_app:$tag
docker push jacvmos/push_app
cd ../../docker/bot_app
docker build -t bot_app .
docker tag bot_app jacvmos/bot_app:$tag
docker push jacvmos/bot_app
