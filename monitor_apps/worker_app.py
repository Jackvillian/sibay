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
from geopy.geocoders import Nominatim
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
geolocator = Nominatim(user_agent="sibay air monitoring")


app.conf.beat_schedule = {
    "document_check": {
        "task": "worker_app.doc_downloader",
        "schedule": crontab(minute="*/30")
    },
    "archive_documents": {
        "task": "worker_app.archive_docs",
        "schedule": crontab(hour="*/8")
    },
    "generate_maps": {
        "task": "worker_app.generate_map",
        "schedule": crontab(hour="*/3")
    },
    "archive_maps": {
        "task": "worker_app.archive_maps",
        "schedule": crontab(hour="*/1")
    }

}




r = redis.StrictRedis(host=config.get('redis','host'), port=config.get('redis','port'), db=1)
s_city = "Sibay,RU"
appid=config.get('openweathermap.org','key')
sess=requests.Session()

def downloader(path,url,name):
    r = requests.get(url)
    with open(path+name, 'wb') as f:
        f.write(r.content)

def localtime():
    ts = datetime.utcnow()
    tz = timezone('Asia/Yekaterinburg')
    ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
    return ts

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
def get_map(arg):
    print("get_map",arg)
    if arg == "call_push_app":
        try:
            maps = session.query(Maps).filter_by(archive=0, publish=0).all()
            if maps is not None:
                for map in maps:
                    print(map.path)
                    map.publish=1
                    session.commit()
                return map.path
        except:
            print("no new maps")

    if arg == "call_bot_app":
        try:
            last_map = session.query(Maps).filter_by(archive=0).all()
            for map in last_map:
                print(map.path)
            return map.path
        except:
            print('get map error')
            session.close()

@app.task
def generate_map():
    expire_point=6
    m = folium.Map(location=[config.get('geolocation', 'center_latitude'), config.get('geolocation', 'center_longitude')], zoom_start=config.get('geolocation', 'start_zoom'))
    HCL = 'Хлороводород'
    H2S = 'Сероводород'
    SO2 = 'Диоксид серы'
    lgnsph = 'ЛИГНОСУЛЬФОНАТ'
    ts = localtime()
    tsdate = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    try:
        so2_stat = json.loads(r.get('so2_s').decode("utf8"))
        for so2 in so2_stat:
            i = so2['street'].split(" ")
            if len(i) > 1:
                street = "сибай " + i[0] + i[1]
                location = geolocator.geocode(street)
                print(location.latitude, location.longitude)
                value=float(so2['value']) * 2
                if value < 0:
                    value=0.0
                popup = '<i>Данные прибора: '+str(value) +'(ПДК) добавлено в ' + str(so2['time']).split(" ")[1] + '</i>'
                folium.CircleMarker([location.latitude, location.longitude], radius=10, popup=popup, tooltip='прибор SO2', line_color='red',
                    fill_color='red').add_to(m)
    except:
        print('no cached data')
    try:
        hcl_stat = json.loads(r.get('hcl_s').decode("utf8"))
        for hcl in hcl_stat:
            i = hcl['street'].split(" ")
            if len(i) > 1:
                street = "сибай " + i[0] + i[1]
                location = geolocator.geocode(street)
                print(location.latitude, location.longitude)
                value = float(hcl['value']) * 2
                if value < 0:
                    value=0.0
                popup = '<i>Данные прибора: ' + str(value) + '(ПДК) добавлено в ' + str(so2['time']).split(" ")[1] + '</i>'
                folium.CircleMarker([location.latitude, location.longitude], radius=10, popup=popup, tooltip='прибор HCL',
                                line_color='green',
                                fill_color='green').add_to(m)
    except:
        print('no cached data')
    find_hcl_locations = session.query(Locations).filter_by(context='#HCL', archive=0).all()
    if find_hcl_locations is not None:
        for hcl_loc in find_hcl_locations:
            popup='<i>метка пользователя по HCL добавлено в '+str(hcl_loc.timestamp).split(" ")[1]+'</i>'
            folium.Marker([hcl_loc.latitude, hcl_loc.longitude], popup=popup, tooltip=HCL, icon=folium.Icon(color='green')).add_to(m)
            db_ts = datetime.strptime(hcl_loc.timestamp, '%Y-%m-%d %H:%M:%S')
            if db_ts < (tsdate - timedelta(hours=expire_point)):
                hcl_loc.archive = 1
                session.commit()
    find_h2s_locations = session.query(Locations).filter_by(context='#H2S', archive=0).all()
    if find_h2s_locations is not None:
        for h2s_loc in find_h2s_locations:
            popup = '<i>метка пользователя по H2S добавлено в ' + str(h2s_loc.timestamp).split(" ")[1] + '</i>'
            folium.Marker([h2s_loc.latitude, h2s_loc.longitude], popup=popup, tooltip=H2S,
                      icon=folium.Icon(color='blue')).add_to(m)
            db_ts = datetime.strptime(h2s_loc.timestamp, '%Y-%m-%d %H:%M:%S')
            if db_ts < (tsdate - timedelta(hours=expire_point)):
                h2s_loc.archive = 1
                session.commit()
    find_so2_locations = session.query(Locations).filter_by(context='#SO2', archive=0).all()
    if find_so2_locations is not None:
        for so2_loc in find_so2_locations:
            popup = '<i>метка пользователя по SO2 добавлено в ' + str(so2_loc.timestamp).split(" ")[1] + '</i>'
            folium.Marker([so2_loc.latitude, so2_loc.longitude], popup=popup, tooltip=SO2,
                      icon=folium.Icon(color='purple')).add_to(m)
            db_ts = datetime.strptime(so2_loc.timestamp, '%Y-%m-%d %H:%M:%S')
            if db_ts < (tsdate - timedelta(hours=expire_point)):
                so2_loc.archive = 1
                session.commit()
    find_lgnsph_locations = session.query(Locations).filter_by(context='#lgnsph', archive=0).all()
    if find_lgnsph_locations is not None:
        for lgnsph_loc in find_lgnsph_locations:
            popup = '<i>метка пользователя по ЛИГНОСУЛЬФОНАТ добавлено в ' + str(lgnsph_loc.timestamp).split(" ")[1] + '</i>'
            folium.Marker([lgnsph_loc.latitude, lgnsph_loc.longitude], popup=popup, tooltip=lgnsph,
                      icon=folium.Icon(color='gray')).add_to(m)
            db_ts = datetime.strptime(lgnsph_loc.timestamp, '%Y-%m-%d %H:%M:%S')
            if db_ts < (tsdate - timedelta(hours=expire_point)):
                lgnsph_loc.archive = 1
                session.commit()
    ts = localtime()
    path = "data/maps/" + str(ts).replace(" ", "_") + "_map.html"
    map_insert = Maps(path, ts, 0, 0)
    session.add(map_insert)
    session.commit()
    session.close()
    m.save(path)
    print('map generated...')


@app.task
def archive_docs():
    try:
        find_docs_archive = session.query(Doc).filter_by(archive=0,publish=1).all()
        ts = localtime()
        tsdate = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        if find_docs_archive is not None:
            for arch in find_docs_archive:
                print(arch.name)
                db_ts = datetime.strptime(arch.timestamp, '%Y-%m-%d %H:%M:%S')
                if db_ts < (tsdate - timedelta(hours=6)):
                    print("archive old docs")
                    arch.archive = 1
                    session.commit()
    except:
        print("error archive docs")
        session.close()


@app.task
def archive_maps():
    try:
        non_archive_last_map = session.query(Maps).filter_by(archive=0, publish=1).all()
        if non_archive_last_map is not None:
            for to_archive in non_archive_last_map:
                to_archive.archive = 1
                session.commit()
            session.close()
    except:
        session.close()
        print("archive map error")



@app.task
def get_doc(arg):
    print("get_doc",arg)
    if arg == "call_push_app":
        try:
            find_docs = session.query(Doc).filter_by(archive=0,publish=0).all()
            docs=[]
            if find_docs is not None:
                for doc in find_docs:
                    doc.publish=1
                    session.commit()
                    docs.append(doc.name)
                print(docs)
                session.close()
                return docs
        except:
            print("get_doc error")
            session.close()
    if arg == "call_bot_app":
        try:
            find_docs = session.query(Doc).filter_by(archive=0).all()
            docs = []
            if find_docs is not None:
                for doc in find_docs:
                    docs.append(doc.path)
                print(docs)
                session.close()
                return docs
        except:
            print("get_doc error")
            session.close()


@app.task
def doc_downloader():
    response = http.request('GET', maior_site)
    soup = BeautifulSoup(response.data, 'html.parser')
    upload_list = soup.find_all('span', {'class': 'news__info-value'}, 'a')
    doc_list=[]
    for upl in upload_list:
        if upl.a is not None:
            find_docs = session.query(Doc).filter_by(name=upl.a['title']).first()
            if find_docs is None:
                if os.path.exists('init.txt'):
                    ts = localtime()
                    doc_insert = Doc(upl.a['href'], upl.a['title'],ts , "data/docs/"+upl.a['title'],0,0)
                    session.add(doc_insert)
                    session.commit()
                    downloader("data/docs/",maior_site_uri+upl.a['href'],upl.a['title'])
                    print("working ",maior_site_uri+upl.a['href'])
                    doc_list.append(upl.a['title'])
                else:
                    ts = localtime()
                    doc_insert = Doc(upl.a['href'], upl.a['title'], ts, "data/docs/" + upl.a['title'], 1,1)
                    session.add(doc_insert)
                    session.commit()
                    downloader("data/docs/", maior_site_uri + upl.a['href'], upl.a['title'])
                    print("working init ", maior_site_uri + upl.a['href'])
    f = open('init.txt', 'tw', encoding='utf-8')
    f.close()
    session.close()
    print(doc_list)





