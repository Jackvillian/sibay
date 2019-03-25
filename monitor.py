import requests
import substring
from datetime import datetime
sess=requests.Session()
r=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":"sibai3@gmail.ru","password":"111111"})

r2=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(r.json()['token'])})

def all_stats():
    r3=sess.post('https://api.owencloud.ru/v1/event/list',headers={'Content-Type':'application/json','Authorization': 'Bearer {}'.format(r.json()['token'])})
    for device in r3.json():
        ts = int(device['last_update'])
        for street in r2.json():
            if device['device_id']== street['id']:
                print(street['name'])
        print(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
        print(device['message'])
        print("\n\r")
        print(device)

all_stats()
