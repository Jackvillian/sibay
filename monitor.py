import requests
from datetime import timedelta
from telegram.ext import Updater
from datetime import datetime
REQUEST_KWARGS={
    'proxy_url': 'socks5://proxy.ec-host.ru:1080',
    'urllib3_proxy_kwargs': {
        'username': 'jackv',
        'password': '00000000',
    }
}

updater = Updater(token='878214304:AAGZJPvnRGHOFf2lQMnRUFUVJx-R16eXcg4', use_context=True,request_kwargs=REQUEST_KWARGS)
jobq = updater.job_queue

sess=requests.Session()

auth=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":"sibai3@gmail.ru","password":"111111"})
r=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth.json()['token'])})
devs={}
events={}
for devices in r.json():
    devs[devices['id']]=devices['name']
print(devs)
lts = datetime.now() - timedelta(minutes=+5)
r4 = sess.post('https://api.owencloud.ru//v1/device/events-log-backward/63934',headers={'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(auth.json()['token'])},json={"end": lts.strftime('%Y-%m-%d %H:%M:%S'), "limit": "10"})
print(lts.strftime('%Y-%m-%d %H:%M:%S'))
last_event = r4.json()
print(last_event)
ts = int(last_event[0]['start_dt'])
print(devs[last_event[0]['device_id']], last_event[0]['message'], last_event[0]['data'][0]['v'],
              datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))




def callback_minute(context):
    context.bot.send_message(chat_id='@AIR_sibay',text=str(devs[last_event[0]['device_id']])+"\n"+str(last_event[0]['message'])+"\nТекущее значение :"+str(last_event[0]['data'][0]['v'])+"\n"+str(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')))

job_minute = jobq.run_repeating(callback_minute, interval=60, first=0)

#updater.start_polling()
#updater.idle()