import requests
from datetime import timedelta
from telegram.ext import Updater
from datetime import datetime

REQUEST_KWARGS={
    'proxy_url': 'socks5://proxy.ec-host.ru:1080',
    'urllib3_proxy_kwargs': {
        'username': 'jackv',
        'password': '00000',
    }
}

updater = Updater(token='0000',request_kwargs=REQUEST_KWARGS, use_context=True)
jobq = updater.job_queue
sess=requests.Session()


def auth():
    au=sess.post('https://api.owencloud.ru/v1/auth/open',json={"login":"sibai3@gmail.ru","password":"111111"})
    return au.json()

def device_list(auth):
    r=sess.post('https://api.owencloud.ru/v1/device/index',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    devs={}
    for devices in r.json():
        devs[devices['id']]=devices['name']
    return devs

def get_params(device,auth):
    urls='https://api.owencloud.ru/v1/device/'+str(device)
    data = sess.post(urls,headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth['token'])})
    return  data.json()['parameters']



def get_data(param):
    payload = {"ids": param}
    data=sess.post('https://api.owencloud.ru/v1/parameters/last-data',headers={'Content-Type':'application/json', 'Authorization': 'Bearer {}'.format(auth()['token'])},json=payload)
    return data.json()

def current_values():

    response_list = []
    for dev in device_list(auth()).keys():
        response = {}
        for p in get_params(dev,auth()):
            if p['name']=='Значение float 1':
                response['street']=device_list(auth())[dev]
                response['value']=get_data(p['id'])[0]['values'][0]['f']
                response['time']=datetime.utcfromtimestamp(int(get_data(p['id'])[0]['values'][0]['d'])).strftime('%Y-%m-%d %H:%M:%S')
        response_list.append(response)
    return response_list

def callback_minute(context):
    context.bot.send_message(chat_id='@AIR_sibay',text='message')






job_minute = jobq.run_repeating(callback_minute, interval=60, first=0)

updater.start_polling()
updater.idle()


