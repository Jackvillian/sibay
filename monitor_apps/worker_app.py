from __future__ import absolute_import, unicode_literals
from models.model import Base ,engine,User,Locations,Doc,Maps
from celery.schedules import crontab
from sqlalchemy.orm import sessionmaker
from celery_config import app
from bs4 import BeautifulSoup
import urllib3
import requests
from skyfield import api
from skyfield import almanac
from pytz import timezone
from datetime import timedelta
from datetime import datetime
import os
import redis
import json
import pickle
import configparser
import os.path
import folium

Session = sessionmaker(bind=engine)
session = Session()
http = urllib3.PoolManager()
config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)
maior_site=config.get('maior_site','doc_url')
maior_site_uri=config.get('maior_site','site')
#REQUEST_KWARGS={
#    'proxy_url': 'socks5://config.get('proxy','host'):config.get('proxy','port')',
#    'urllib3_proxy_kwargs': {
#        'username': 'config.get('proxy','user')',
#        'password': 'config.get('proxy','password')',
#    }
#}

r = redis.StrictRedis(host=config.get('redis','host'), port=config.get('redis','port'), db=1)
s_city = "Sibay,RU"
appid=config.get('openweathermap.org','key')
sess=requests.Session()

def downloader(path,url,name):
    r = requests.get(url)
    with open(path+name, 'wb') as f:
        f.write(r.content)



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
def status_devices():
    for dev in device_list(auth()).keys():
        for p in get_params(dev, auth()):
            print(p['name'])


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
                    tz = timezone('Asia/Yekaterinburg')
                    utc = datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d']))
                    response['time'] = utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
            print(response_list_clear)
    json_objects = json.dumps(response_list_clear)
    r.set('hcl_s', json_objects)
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
                    tz = timezone('Asia/Yekaterinburg')
                    utc = datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d']))
                    response['time'] = utc.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    for resp in response_list:
        if not resp:
            pass
        else:
            response_list_clear.append(resp)
            print(response_list_clear)
    json_objects = json.dumps(response_list_clear)
    r.set('so2_s', json_objects)
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
    ts = datetime.now()
    if r.exists('weather_cache'):
        print("cache exist")
        unpacked_weater = json.loads(r.get('weather_cache').decode('utf8'))
        expired=datetime.strptime(unpacked_weater[1]['expire'], '%Y-%m-%d %H:%M:%S.%f')
        if expired < (ts - timedelta(minutes=60)):
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
            weather_value = [{'presure': presure_mm, 'temp': str(weather['list'][0]['main']['temp']), 'humidity': str(weather['list'][0]['main']['humidity']), 'wind_speed': str(weather['list'][0]['wind']['speed']) , 'wind': wind_comp},{'expire': str(ts)}]
            weather_value = json.dumps(weather_value)
            r.set('123weather_cache', weather_value)
            result_msg = "*Погода Cибай*\n\rТемпература: " + str(weather['list'][0]['main']['temp']) + "\n\rВлажность: " +str(weather['list'][0]['main']['humidity'])+ "\n\rДавление: " + str(round(presure_mm, 2)) + "\n\rВетер: ``` \n\r направление: " + wind_comp+ " \n\r скорость: " + str(weather['list'][0]['wind']['speed']) + "\n\r```"
            print("weather update cache")
            return result_msg

        else:
            print("weather using  cache")
            result_msg="*Погода Cибай*\n\rТемпература: "+unpacked_weater[0]['temp']+"\n\rВлажность: "+unpacked_weater[0]['humidity']+"\n\rДавление: "+str(round(unpacked_weater[0]['presure'],2))+"\n\rВетер: ``` \n\r направление: "+unpacked_weater[0]['wind']+" \n\r скорость: "+unpacked_weater[0]['wind_speed']+"\n\r```"
            return result_msg
    else:
        print("cache not exist")
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
        weather_value = [{'presure': presure_mm, 'temp': str(weather['list'][0]['main']['temp']),
                          'humidity': str(weather['list'][0]['main']['humidity']),
                          'wind_speed': str(weather['list'][0]['wind']['speed']), 'wind': wind_comp},
                         {'expire': str(ts)}]
        weather_value = json.dumps(weather_value)
        r.set('weather_cache', weather_value)
        result_msg = "*Погода Cибай*\n\rТемпература: " + str(
            weather['list'][0]['main']['temp']) + "\n\rВлажность: " + str(
            weather['list'][0]['main']['humidity']) + "\n\rДавление: " + str(
            round(presure_mm, 2)) + "\n\rВетер: ``` \n\r направление: " + wind_comp + " \n\r скорость: " + str(
            weather['list'][0]['wind']['speed']) + "\n\r```"
        print("weather create cache")
        return result_msg

@app.task
def generate_map():

    m = folium.Map(location=[config.get('geolocation', 'center_latitude'), config.get('geolocation', 'center_longitude')], zoom_start=config.get('geolocation', 'start_zoom'))
    HCL = 'Хлороводород'
    H2S = 'Сероводород'
    SO2 = 'Диоксид серы'
    lgnsph = 'ЛИГНОСУЛЬФОНАТ'
    session.expire_all()
    find_new_poins=session.query(Locations).filter_by(archive=0).all()
    ts = datetime.utcnow()
    tz = timezone('Asia/Yekaterinburg')
    ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
    tsdate=datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    for point in find_new_poins:
        db_ts = datetime.strptime(point.timestamp, '%Y-%m-%d %H:%M:%S')
        if db_ts < (tsdate - timedelta(hours=6)):
            point.archive = 1
            session.commit()

    find_hcl_locations = session.query(Locations).filter_by(context='#HCL', archive=0).all()
    for hcl_loc in find_hcl_locations:
        popup='<i>метка пользователя по HCL добавлено в '+str(hcl_loc.timestamp).split(" ")[1]+'</i>'
        folium.Marker([hcl_loc.latitude, hcl_loc.longitude], popup=popup, tooltip=HCL, icon=folium.Icon(color='green')).add_to(m)
    find_h2s_locations = session.query(Locations).filter_by(context='#H2S', archive=0).all()
    for h2s_loc in find_h2s_locations:
        popup = '<i>метка пользователя по H2S добавлено в ' + str(h2s_loc.timestamp).split(" ")[1] + '</i>'
        folium.Marker([h2s_loc.latitude, h2s_loc.longitude], popup=popup, tooltip=H2S,
                      icon=folium.Icon(color='blue')).add_to(m)
    find_so2_locations = session.query(Locations).filter_by(context='#SO2', archive=0).all()
    for so2_loc in find_so2_locations:
        popup = '<i>метка пользователя по SO2 добавлено в ' + str(so2_loc.timestamp).split(" ")[1] + '</i>'
        folium.Marker([so2_loc.latitude, so2_loc.longitude], popup=popup, tooltip=SO2,
                      icon=folium.Icon(color='purple')).add_to(m)
    find_lgnsph_locations = session.query(Locations).filter_by(context='#lgnsph', archive=0).all()
    for lgnsph_loc in find_lgnsph_locations:
        popup = '<i>метка пользователя по ЛИГНОСУЛЬФОНАТ добавлено в ' + str(lgnsph_loc.timestamp).split(" ")[1] + '</i>'
        folium.Marker([lgnsph_loc.latitude, lgnsph_loc.longitude], popup=popup, tooltip=lgnsph,
                      icon=folium.Icon(color='gray')).add_to(m)
    archive_last_map = session.query(Maps).filter_by(archive=0).first()
    if archive_last_map is not None:
        archive_last_map.archive=1
        session.commit()
    ts = datetime.utcnow()
    tz = timezone('Asia/Yekaterinburg')
    ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
    path="data/maps/"+str(ts).replace(" ", "_")+"_map.html"
    map_insert = Maps(path,ts,0)
    session.add(map_insert)
    session.commit()
    session.close()
    m.save(path)
    print('map generated...')
    return path

@app.task
def doc_downloader():
    session.expire_all()
    response = http.request('GET', maior_site)
    soup = BeautifulSoup(response.data, 'html.parser')
    upload_list = soup.find_all('span', {'class': 'news__info-value'}, 'a')
    doc_list=[]
    for upl in upload_list:
        if upl.a is not None:
            find_docs = session.query(Doc).filter_by(name=upl.a['title']).first()
            if find_docs is None:
                if os.path.exists('init.txt'):
                    ts = datetime.utcnow()
                    tz = timezone('Asia/Yekaterinburg')
                    ts=ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
                    doc_insert = Doc(upl.a['href'], upl.a['title'],ts , "data/docs/"+upl.a['title'],0)
                    session.add(doc_insert)
                    session.commit()
                    downloader("data/docs/",maior_site_uri+upl.a['href'],upl.a['title'])
                    print("working ",maior_site_uri+upl.a['href'])
                    doc_list.append(upl.a['title'])
                else:
                    ts = datetime.utcnow()
                    tz = timezone('Asia/Yekaterinburg')
                    ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
                    doc_insert = Doc(upl.a['href'], upl.a['title'], ts, "data/docs/" + upl.a['title'], 1)
                    session.add(doc_insert)
                    session.commit()
                    downloader("data/docs/", maior_site_uri + upl.a['href'], upl.a['title'])
                    print("working init ", maior_site_uri + upl.a['href'])


        else:
            find_docs_archive = session.query(Doc).filter_by(archive=0).all()
            ts = datetime.utcnow()
            tz = timezone('Asia/Yekaterinburg')
            ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            startts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0)
            stopts = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=10, second=0)
            print(startts,ts)
            for arch in find_docs_archive:
                db_ts=datetime.strptime(arch.timestamp, '%Y-%m-%d %H:%M:%S')
                if db_ts > startts and db_ts < stopts:
                    print("archive old docs")
                    arch.archive=1
                    session.commit()
    f = open('init.txt', 'tw', encoding='utf-8')
    f.close()
    session.close()
    print(doc_list)
    return doc_list





