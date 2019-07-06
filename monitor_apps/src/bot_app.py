from telegram.ext import Updater, CommandHandler, MessageHandler,Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
from models.model import Base ,engine,User,Locations
from worker_app import print_hello, sensors_task_SO2, sensors_task_HCL, weather_task, solar_time, status_devices
from geopy.distance import geodesic
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import celery_config
from datetime import datetime, timedelta
import os
import configparser
import redis

Session = sessionmaker(bind=engine)
session = Session()


config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)

r = redis.StrictRedis(host=config.get('redis','host'), port=config.get('redis','port'), db=1)

updater = Updater(config.get('telegram','botapikey'), use_context=True)
dispatcher = updater.dispatcher



def start(update, context):
    #print(update)
    user_data=update.message.chat
    find_user=session.query(User).filter_by(userid=user_data['id'], chattype="private").first()
    session.close()
    if find_user is not None:
        print(find_user.first_name)
        text_message="Привет "+find_user.first_name+" ! я рад что тебе неравнодушен наш город !\n\rчтобы начать набери: /home"

        context.bot.send_message(chat_id=update.message.chat_id, text=text_message)
    else:
        tg_us = User(user_data['first_name'],user_data['last_name'],user_data['username'],user_data['id'], user_data['type'])
        session.add(tg_us)
        session.commit()
        session.close()
        text_message = "Привет новичек я помогу тебе разобраться !\n\rчтобы начать набери:: /home"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message)


def create_point(update, context):
    hcl_keyboard = KeyboardButton(text="#HCL")
    so2_keyboard = KeyboardButton(text="#SO2")
    h2s_keyboard = KeyboardButton(text="#H2S")
    lgpt_keyboard = KeyboardButton(text="#lgnsph")
    custom_keyboard = [[hcl_keyboard, so2_keyboard, h2s_keyboard, lgpt_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    context.bot.send_message(chat_id=update.message.chat_id,text="чем по вашему пахнет:\n\rкнопка #HCL - Хлороводород (пахнет хлоркой)\n\rкнопка #SO2 - Диоксид Серы (пахнет женными спичками)\n\rкнопка #H2S - Сероводород (пахнет тухлыми яйцами)\n\rкнопка #lgnsph -  ЛИГНОСУЛЬФОНАТ (пахнет жаренными семечками)",reply_markup=reply_markup)


def req_location(update, context):
    user_data = update.message.chat
    r.set(user_data['id'],update.message.text )
    print("req location", user_data['id'])
    find_last = session.query(Locations).filter_by(userid=user_data['id']).order_by(Locations.id.desc()).first()
    session.close()
    if find_last is None:
        location_keyboard = KeyboardButton(text="Cоздать Метку", request_location=True)
        custom_keyboard = [[location_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text="Не забудьте включить геолокацию!", reply_markup=reply_markup)
    else:
        last_ts=find_last.timestamp
        last_ts= datetime.strptime(last_ts, '%Y-%m-%d %H:%M:%S.%f')
        curr_ts = datetime.now()
    if last_ts < (curr_ts - timedelta(minutes=1)):
        location_keyboard = KeyboardButton(text="Cоздать Метку",request_location=True)
        custom_keyboard = [[location_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text="Не забудьте включить геолокацию!",reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        delta=curr_ts-last_ts
        spl_delta=str(delta).split('.')
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_msg="можно создать только 1 метку в час , с момента создания метки прошло : "+spl_delta[0]
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)

def resp_location(update, context):
    user_data = update.message.chat
    home_keyboard = KeyboardButton(text="/home Вернуться в начало")
    custom_keyboard = [[home_keyboard]]
    print(update.message.location, r.get(user_data['id']).decode("utf-8"),user_data['id'])
    geo_center = (config.get('geolocation','center_latitude'),config.get('geolocation','center_longitude') )
    geo_user=(update.message.location.latitude,update.message.location.longitude)
    distance=geodesic(geo_center, geo_user).kilometers
    if distance > config.get('geolocation','max_distance'):
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        messagetext="Ух... как вы далеко забрались!\n\rК сожалению радиус меток "+config.get('geolocation','max_distance')+" км"
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext, reply_markup=reply_markup)
        print("distance to long ",user_data['id'], "distance", distance)
    else:
        ts = datetime.now()
        db_loc = Locations(str(user_data['id']), str(update.message.location.longitude), str(update.message.location.latitude), str(ts) , str(r.get(user_data['id']).decode("utf-8")))
        session.add(db_loc)
        session.commit()
        print("point writed for userid ",user_data['id'], "distance", distance)
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text="метка принята", reply_markup=reply_markup)


def report():
    pass


def home(update, context):
    status_keyboard = KeyboardButton(text="/status")
    weather_keyboard = KeyboardButton(text="/weather")
    camera_keyboard = KeyboardButton(text="/camera")
    map_keyboard = KeyboardButton(text="/map")
    generate_keyboard = KeyboardButton(text="/report")
    help_keyboard = KeyboardButton(text="/help")
    custom_keyboard = [[status_keyboard, weather_keyboard, camera_keyboard, map_keyboard, generate_keyboard,help_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    text_message = "С помощью бота можно узнать:\n\rв каком состоянии сейчас общественные датчики: /status \n\rсводку погоды: /weather \n\rполучить ссылки на камеры установленные на бортах: /camera \n\r Также если вы почувствовали какой то запах вы можете создать собственную метку на карте и она будет опубликована: /map\n\r получить выгрузку со всех датчиков за сутки: /report\n\r помощь /help "

    context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)

def weather_resp(update, context):
    messagetext = weather_task.delay()
    messagetext2 = messagetext.get(timeout=300)
    home_keyboard = KeyboardButton(text="/home Вернуться в начало")
    custom_keyboard = [[home_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    context.bot.send_message(chat_id=update.message.chat_id, text=messagetext2, reply_markup=reply_markup,parse_mode='MARKDOWN')

def status(update, context):
    messagetext = status_devices.delay()
    messagetext2 = messagetext.get(timeout=300)

start_handler = CommandHandler('start', start)
status_handler = CommandHandler('status', status)
weather_handler=CommandHandler('weather', weather_resp)
help_handler = CommandHandler('help', help)
home_handler = CommandHandler('home', help)
map_handler= CommandHandler('map', create_point)
report_handler = CommandHandler('report', report)
req_handler = MessageHandler(Filters.entity("hashtag"), req_location)
resp_handler = MessageHandler(Filters.location, resp_location)
dispatcher.add_handler(weather_handler)
dispatcher.add_handler(req_handler)
dispatcher.add_handler(resp_handler)
dispatcher.add_handler(map_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(status_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(home_handler)
dispatcher.add_handler(report_handler)
print("bot is started ...")
updater.start_polling()
updater.idle()