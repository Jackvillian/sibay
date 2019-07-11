tag=$1
cd ../celery_app
docker build -t celery_app .
docker tag celery_app jacvmos/celery_app:$tag
docker tag jacvmos/celery_app:$tag jacvmos/celery_app:latest
docker push jacvmos/celery_app
cd ../push_app
docker build -t push_app .
docker tag push_app jacvmos/push_app:$tag
docker tag jacvmos/push_app:$tag jacvmos/push_app:latest
docker push jacvmos/push_app
cd ../bot_app
docker build -t bot_app .
docker tag bot_app jacvmos/bot_app:$tag
docker tag jacvmos/bot_app:$tag jacvmos/bot_app:latest
docker push jacvmos/bot_app
cd ..
