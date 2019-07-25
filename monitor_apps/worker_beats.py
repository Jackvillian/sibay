from __future__ import absolute_import, unicode_literals
from models.model import Base ,engine,User,Locations,Doc,Maps
from celery.schedules import crontab
from sqlalchemy.orm import sessionmaker
from celery_config import app
from bs4 import BeautifulSoup
import urllib3
import requests
import geopy
from datetime import timedelta
from datetime import datetime
from pytz import timezone
import os
import redis
import json
import configparser
import os.path
import folium
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="sibay air monitoring")
from jsonmerge import merge



Session = sessionmaker(bind=engine)
session = Session()
http = urllib3.PoolManager()
config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)
maior_site=config.get('maior_site','doc_url')
maior_site_uri=config.get('maior_site','site')

r = redis.StrictRedis(host=config.get('redis','host'), port=config.get('redis','port'), db=1)
s_city = "Sibay,RU"
appid=config.get('openweathermap.org','key')
sess=requests.Session()

def auth():
    au=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":config.get('owencloud','user'),"password":config.get('owencloud','password')})
    return au.json()

def device_list(auth):
    r=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    devs={}
    for devices in r.json():
        devs[devices['id']]=devices['name']
    return devs

def device_status(auth):
    r=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    status={}
    for devices in r.json():
        uri='https://api.owencloud.ru/v1/device/'+str(devices['id'])
        r2 = sess.post(uri,headers={'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})


    return r2.json()

def get_data(param):
    payload = {"ids": param}
    data=sess.post('https://api.owencloud.ru/v1/parameters/last-data',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth()['token'])},json=payload)
    return data.json()

def get_params(device,auth):
    urls='https://api.owencloud.ru/v1/device/'+str(device)
    data = sess.post(urls,headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    return  data.json()['parameters']


so2_stat = json.loads(r.get('so2_s').decode("utf8"))
print(so2_stat)
for so2 in so2_stat:
    i=so2['street'].split(" ")
    if len(i) > 1:
        street="сибай "+i[0]+i[1]
        print(street)
        location = geolocator.geocode(street)
        print(location.latitude, location.longitude)


hcl_stat = json.loads(r.get('hcl_s').decode("utf8"))
for so2 in hcl_stat:
    i=so2['street'].split(" ")
    if len(i) > 1:
        street="сибай "+i[0]+i[1]
        print(street)











