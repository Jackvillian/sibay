import requests
from celery import Celery,task
from telegram.ext import Updater, CommandHandler
from datetime import datetime
from pytz import timezone
import sys
import os
import celery_config
import configparser
from worker_app import print_hello, sensors_task_SO2, sensors_task_HCL, weather_task, solar_time, doc_downloader, generate_map



config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)


updater = Updater(token=config.get('telegram','botapikey'),use_context=True)
jobq = updater.job_queue

def hello(bot, update):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))


def callback_every_1_minutes(context):
    sol = solar_time.delay()
    sol = sol.get(timeout=100)
    print(sol)

def callback_HCL_5_minutes(context):
    sens = sensors_task_HCL.delay()
    sens = sens.get(timeout=400)
    for message in sens:
        overload = float(message['value']) * 10
        if float(message['value']) >= 0.1:
               #context.bot.send_message(chat_id='@AIR_sibay',text="*Опасность Превышение ПДК (Хлороводород) в " + str(round(overload,2)) + " раз !!!* \n\r" + message['street'] + "\n\r``` Текущее значение прибора:" + message['value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ",parse_mode='MARKDOWN')
               print("*Опасность Превышение ПДК (Хлороводород) в " + str(round(overload,2)) + " раз !!!* \n\r" + message['street'] + "\n\r``` Текущее значение прибора:" + message['value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ")
        else:
            pass

def callback_SO2_5_minutes(context):
    sens=sensors_task_SO2.delay()
    sens=sens.get(timeout=400)
    for message in sens:
        overload = float(message['value']) * 2
        if float(message['value'])>= 0.6:
            #context.bot.send_message(chat_id='@AIR_sibay',text="*Внимание Превышение ПДК (Диоксид Серы) в " + str(round(overload,2)) + " раз !!!* \n\r" + message['street'] + "\n\r``` Текущее значение прибора:" + message['value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ",parse_mode='MARKDOWN')
            print("*Внимание Превышение ПДК (Диоксид Серы) в " + str(round(overload,2)) + " раз !!!* \n\r" + message['street'] + "\n\r``` Текущее значение прибора:" + message['value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ")
        else:
            pass





def callback_weather_6_hours(context):
    messagetext=weather_task.delay()
    messagetext=messagetext.get(timeout=300)
    print(messagetext)
    #context.bot.send_message(chat_id='@AIR_sibay', text=messagetext,parse_mode='MARKDOWN')
    messagetext="*узнать погоду можно при помощи бота t.me/air_sibay_bot\n\r"
    # context.bot.send_message(chat_id='@AIR_sibay', text=messagetext,parse_mode='MARKDOWN')

def callback_docs_1_hours(context):
    doclist = doc_downloader.delay()
    doclist = doclist.get(timeout=2700)
    if not doclist:
        print('empty no new documents')
    else:
        messagetext = "*Получены новые документы от\n\rмежведомственного оперативного штаба\n\r"
        for msg in doclist:
            messagetext=messagetext+msg+"\n\r"
        messagetext=messagetext+"\n\rзагрузить документы можно при помощи бота t.me/air_sibay_bot\n\r"
        print(messagetext)
        #context.bot.send_message(chat_id='@AIR_sibay', text=messagetext, parse_mode='MARKDOWN')


def callback_maps_3_hours(context):
    map = generate_map.delay()
    map = map.get(timeout=2700)
    print(map)
    messagetext = "*Создана новая карта\n\r вы можете создавать метки при помощи бота t.me/air_sibay_bot"
    #context.bot.send_message(chat_id='@AIR_sibay', text=messagetext, parse_mode='MARKDOWN')
    #context.bot.sendDocument(chat_id='@AIR_sibay', document=open(map, 'rb'))




job_hour = jobq.run_repeating(callback_maps_3_hours, interval=300, first=0)
#job_hour = jobq.run_repeating(callback_docs_1_hours, interval=300, first=0)
job_minute = jobq.run_repeating(callback_SO2_5_minutes, interval=300, first=0)
job_minute = jobq.run_repeating(callback_HCL_5_minutes, interval=300, first=0)
#job_hours = jobq.run_repeating(callback_weather_6_hours, interval=7200, first=0)

print("push_app is started...")
updater.start_polling()
updater.idle()