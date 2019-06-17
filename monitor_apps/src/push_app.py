import requests
from celery import Celery,task
from telegram.ext import Updater, CommandHandler
from datetime import datetime
from pytz import timezone
import sys
import os
import celery_config
import configparser

from worker_app import print_hello, sensors_task_SO2, sensors_task_HCL, weather_task, solar_time



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

def callback_every_55_minutes(context):
    sens = sensors_task_HCL.delay()
    sens = sens.get(timeout=100)
    for message in sens:
        overload = float(message['value']) * 10
        if float(message['value']) >= 0.1:
               context.bot.send_message(chat_id='@AIR_sibay',
                                        text="*Опасность Превышение ПДК (Хлороводород) в " + str(round(overload,2)) + " раз !!!* \n\r" + message[
                                            'street'] + "\n\r``` Текущее значение прибора:" + message[
                                                 'value'] + "\n\rДата фиксации:" + message['time'] + "``` ",
                                        parse_mode='MARKDOWN')
               print("*Опасность Превышение ПДК (Хлороводород) в " + str(round(overload,2)) + " раз !!!* \n\r" + message[
                    'street'] + "\n\r``` Текущее значение прибора:" + message[
                      ' value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ")
        else:
            pass

def callback_every_5_minutes(context):
    sens=sensors_task_SO2.delay()
    sens=sens.get(timeout=100)
    for message in sens:

        overload = float(message['value']) * 2
        if float(message['value'])>= 0.6:

            context.bot.send_message(chat_id='@AIR_sibay',
                                     text="*Внимание Превышение ПДК (Диоксид Серы) в " + str(round(overload,2)) + " раз !!!* \n\r" + message[
                                           'street'] + "\n\r``` Текущее значение прибора:" + message[
                                              'value'] + "\n\rДата фиксации:" + message['time'] + "``` ",
                                     parse_mode='MARKDOWN')


            print("*Внимание Превышение ПДК (Диоксид Серы) в " + str(round(overload,2)) + " раз !!!* \n\r" + message[
                                         'street'] + "\n\r``` Текущее значение прибора:" + message[
                                              'value'] + "\n\rВремя местное (Сибай):" + message['time'] + "``` ")

        else:
            pass





def callback_every_2_hours(context):
    messagetext=weather_task.apply_async()

    #context.bot.send_message(chat_id='@AIR_sibay', text=messagetext,
    #                                parse_mode='MARKDOWN')
    print(messagetext.get(timeout=100))

job_minute = jobq.run_repeating(callback_every_55_minutes, interval=300, first=0)
job_minute = jobq.run_repeating(callback_every_5_minutes, interval=300, first=0)
job_minute = jobq.run_repeating(callback_every_1_minutes, interval=60, first=0)
job_hour = jobq.run_repeating(callback_every_2_hours, interval=7200, first=0)
updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.start_polling()
updater.idle()