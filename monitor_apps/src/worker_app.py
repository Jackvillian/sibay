from __future__ import absolute_import, unicode_literals
from celery_config import app
import requests
from skyfield import api
from skyfield import almanac
from pytz import timezone
from datetime import timedelta
from telegram.ext import Updater
from datetime import datetime
import sys
import os
import configparser


config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)

#REQUEST_KWARGS={
#    'proxy_url': 'socks5://config.get('proxy','host'):config.get('proxy','port')',
#    'urllib3_proxy_kwargs': {
#        'username': 'config.get('proxy','user')',
#        'password': 'config.get('proxy','password')',
#    }
#}
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

def get_data(param):
    payload = {"ids": param}
    data=sess.post('https://api.owencloud.ru/v1/parameters/last-data',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth()['token'])},json=payload)
    return data.json()

def get_params(device,auth):
    urls='https://api.owencloud.ru/v1/device/'+str(device)
    data = sess.post(urls,headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    return  data.json()['parameters']

@app.task
def print_hello():
    print('hello there')
    return("lol")

@app.task
def solar_time():
    result=[]
    ts = api.load.timescale()
    e = api.load('de421.bsp')
    bluffton = api.Topos('52.4143 N', '58.3816 E')

    tz = timezone('Asia/Yekaterinburg')
    t0 = ts.utc(2019, 5, 5, 4)
    t1 = ts.utc(2019, 5, 6, 4)
    t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, bluffton))

    dusk_utc = datetime.strptime(t.utc_iso()[0], '%Y-%m-%dT%H:%M:%SZ')
    sunset_utc = datetime.strptime(t.utc_iso()[1], '%Y-%m-%dT%H:%M:%SZ')

    print(dusk_utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'))
    print(sunset_utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'))
    result.append(dusk_utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'))
    result.append(sunset_utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S'))
    return result



@app.task
def sensors_task_HCL():
    response_list = []
    response_list_clear = []
    for dev in device_list(auth()).keys():
        response = {}
        for p in get_params(dev, auth()):
            if p['name'] == 'Значение float 2':
                if not "Ошибка" in get_data(p['id'])[0]['values'][0]['f']:
                    response['street'] = device_list(auth())[dev]
                    response['value'] = get_data(p['id'])[0]['values'][0]['f']
                    response['time'] = datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d'])).strftime('%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
            print(response_list_clear)
    return response_list_clear

@app.task
def sensors_task_SO2():
    response_list = []
    response_list_clear = []
    for dev in device_list(auth()).keys():
        response = {}
        for p in get_params(dev, auth()):
            if p['name'] == 'Значение float 1':
                if not "Ошибка" in get_data(p['id'])[0]['values'][0]['f']:
                    response['street'] = device_list(auth())[dev]
                    response['value'] = get_data(p['id'])[0]['values'][0]['f']
                    response['time'] = datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d'])).strftime('%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
            print(response_list_clear)
    return response_list_clear

@app.task
def dnn(f):
    print(f)
    print("dnn is work))))")

@app.task
def weather_task():
    wr = requests.get("http://api.openweathermap.org/data/2.5/find",
                      params={'q': s_city, 'type': 'like', 'units': 'metric', 'APPID': appid})
    weather=wr.json()
    wind = weather['list'][0]['wind']['deg']
    if wind > 0.00 and wind <= 22.30:
        wind_comp = "С-С-В"
    if wind > 22.30 and wind <= 45.0:
        wind_comp = "С-В"
    if wind > 45.0 and wind <= 67.30:
        wind_comp = "В-В-С"
    if wind > 67.30 and wind <= 90.0:
        wind_comp = "В"
    if wind > 90.0 and wind <= 112.30:
        wind_comp = "В-Ю-В"
    if wind > 112.30 and wind <= 135.0:
        wind_comp = "Ю-В"
    if wind > 135.0 and wind <= 157.30:
        wind_comp = "Ю-Ю-В"
    if wind > 157.30 and wind <= 180:
        wind_comp = "Ю"
    if wind > 180.0 and wind <= 202.30:
        wind_comp = "Ю-Ю-З"
    if wind > 202.30 and wind <= 225.0:
        wind_comp = "Ю-З"
    if wind > 225.0 and wind <= 247.30:
        wind_comp = "З-Ю-З"
    if wind > 247.30 and wind <= 270.0:
        wind_comp = "З"
    if wind > 270.0 and wind <= 292.30:
        wind_comp = "З-С-З"
    if wind > 292.30 and wind <= 315.00:
        wind_comp = "С-З"
    if wind > 315.00 and wind <= 337.30:
        wind_comp = "С-С-З"
    if wind > 337.30 and wind <= 360.00:
        wind_comp = "С"
    presure_mm = float(weather['list'][0]['main']['pressure']) * float(0.750063755419211)
    result_msg="*Погода Cибай*\n\rТемпература: "+str(weather['list'][0]['main']['temp'])+"\n\rВлажность: "+str(weather['list'][0]['main']['humidity'])+"\n\rДавление: "+str(round(presure_mm,2))+"\n\rВетер: ``` \n\r направление: "+wind_comp+" \n\r скорость: "+str(weather['list'][0]['wind']['speed'])+"\n\r```"
    return result_msg