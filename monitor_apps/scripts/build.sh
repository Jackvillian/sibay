tag=$1
cd ../celery_app
docker build -t celery_app .
docker tag celery_app jacvmos/celery_app:$tag
docker push jacvmos/celery_app
cd ../push_app
docker build -t push_app .
docker tag push_app jacvmos/push_app:$tag
docker push jacvmos/push_app
cd ../bot_app
docker build -t bot_app .
docker tag bot_app jacvmos/bot_app:$tag
docker push jacvmos/bot_app
cd ..
