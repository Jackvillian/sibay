cd celery_app
docker build -t celery_app .
docker tag celery_app jacvmos/celery_app:0.0.7
docker push jacvmos/celery_app
cd ..
cd push_app
docker build -t push_app .
docker tag push_app jacvmos/push_app:0.0.7
docker push jacvmos/push_app
cd ..
cd bot_app
docker build -t bot_app .
docker tag bot_app jacvmos/bot_app:0.0.7
docker push jacvmos/bot_app
cd ..
