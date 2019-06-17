from celery import Celery,task
from celery.schedules import crontab
app = Celery('task', broker='redis://redisdb:6379/0', backend='redis://redisdb:6379/0')
result_backend = 'redis://redisdb:6379/0'
result_persistent = True
task_result_expires = None
send_events = True