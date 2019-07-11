from celery import Celery,task
from celery.schedules import crontab
import os
import configparser
config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)
redis_param="redis://"+config.get('redis','host')+":"+config.get('redis','port')+"/0"
app = Celery('task', broker=redis_param, backend=redis_param)
result_backend = redis_param
result_persistent = True
task_result_expires = None
send_events = True