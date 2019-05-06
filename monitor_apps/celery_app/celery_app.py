from celery import Celery
from celery import Celery
from celery.schedules import crontab
import requests
from skyfield import api
from skyfield import almanac
from pytz import timezone
from datetime import timedelta
from telegram.ext import Updater
from datetime import datetime

REQUEST_KWARGS={
    'proxy_url': 'socks5://host:port',
    'urllib3_proxy_kwargs': {
        'username': 'user',
        'password': 'password',
    }
}
s_city = "Sibay,RU"
appid='d2c11e3e139b14618c0c05992dad10d5'
sess=requests.Session()
app = Celery('tasks', broker='redis://127.0.0.1:6379/0')


def auth():
    au=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":"login","password":"111111"})
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

@app.task
def solar_time():
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
    print(y)
    return t,y


@app.task
def sensors_task():
    response_list = []
    for dev in device_list(auth()).keys():
        response = {}
        for p in get_params(dev, auth()):
            if p['name'] == 'Значение float 1':
                response['street'] = device_list(auth())[dev]
                response['value'] = get_data(p['id'])[0]['values'][0]['f']
                response['time'] = datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d'])).strftime(
                    '%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    return response_list


@app.task
def weather_task():
    wr = requests.get("http://api.openweathermap.org/data/2.5/find",
                      params={'q': s_city, 'type': 'like', 'units': 'metric', 'APPID': appid})
    return wr.json()