from telegram.ext import Updater, CommandHandler, MessageHandler,Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
from models.model import Base ,engine,User,Locations, Doc, Maps,Log
from worker_app import sensors_task_SO2, sensors_task_HCL, weather_task, solar_time, status_devices,get_doc,get_map
from geopy.distance import geodesic
from sqlalchemy.orm import sessionmaker
from pytz import timezone
import os.path
import sqlalchemy
import celery_config
from datetime import datetime, timedelta
import os
import configparser
import redis
import json

Session = sessionmaker(bind=engine)
session = Session()
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)

r = redis.StrictRedis(host=config.get('redis','host'), port=config.get('redis','port'), db=1)

updater = Updater(config.get('telegram','bot2apikey'), use_context=True)
dispatcher = updater.dispatcher

def check_user(userid,step):
    find_user = session.query(User).filter_by(userid=userid, chattype="private").first()

    if find_user is None:
        return 1
    else:
        log_insert = Log(userid, step)
        session.add(log_insert)
        session.commit()
    session.close()



def start(update, context):
    user_data=update.message.chat
    find_user=session.query(User).filter_by(userid=user_data['id'], chattype="private").first()
    session.close()
    if find_user is not None:
        home_keyboard = KeyboardButton(text="/home")
        custom_keyboard = [[home_keyboard]]
        print(find_user.first_name)
        text_message="Привет "+find_user.first_name+" ! я рад что тебе неравнодушен наш город !\n\rчтобы начать нажми: /home"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home")
        custom_keyboard = [[home_keyboard]]
        tg_us = User(user_data['first_name'],user_data['last_name'],user_data['username'],user_data['id'], user_data['type'])
        session.add(tg_us)
        session.commit()
        session.close()
        text_message = "Привет новичек я помогу тебе разобраться !\n\rчтобы начать нажми: /home \n\r далее выбери раздел помощь"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message , reply_markup=reply_markup)



def map(update, context):
    if check_user(update.message.chat['id'],"map")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        new_keyboard = KeyboardButton(text="/new создать новую метку")
        last_keyboard = KeyboardButton(text="/last  загрузить")
        custom_keyboard = [[new_keyboard, last_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_message = "вы можете создать новую метку на карте или загрузить уже сгенерированую карту"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)

def create_point(update, context):
    if check_user(update.message.chat['id'],"check_point")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        hcl_keyboard = KeyboardButton(text="#HCL")
        so2_keyboard = KeyboardButton(text="#SO2")
        h2s_keyboard = KeyboardButton(text="#H2S")
        lgpt_keyboard = KeyboardButton(text="#lgnsph")
        custom_keyboard = [[hcl_keyboard, so2_keyboard, h2s_keyboard, lgpt_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,text="чем, по вашему пахнет:\n\rкнопка #HCL - Хлороводород (пахнет хлоркой)\n\rкнопка #SO2 - Диоксид Серы (пахнет женными спичками)\n\rкнопка #H2S - Сероводород (пахнет тухлыми яйцами)\n\rкнопка #lgnsph -  ЛИГНОСУЛЬФОНАТ (пахнет жаренными семечками)",reply_markup=reply_markup)


def req_location(update, context):
    user_data = update.message.chat
    r.set(user_data['id'],update.message.text )
    r.expire(user_data['id'], 60)
    find_last = session.query(Locations).filter_by(userid=str(user_data['id']), archive=False).order_by(Locations.id.desc()).first()
    print("req location", user_data['id'])
    if find_last is None:
        location_keyboard = KeyboardButton(text="Cоздать Метку", request_location=True)
        custom_keyboard = [[location_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text="Не забудьте включить геолокацию!", reply_markup=reply_markup)
    else:
        last_ts=find_last.timestamp
        last_ts= datetime.strptime(last_ts, '%Y-%m-%d %H:%M:%S')
        ts = datetime.utcnow()
        tz = timezone('Asia/Yekaterinburg')
        curr_ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
        curr_ts = datetime.strptime(curr_ts, '%Y-%m-%d %H:%M:%S')
        print(curr_ts-timedelta(minutes=int(config.get('geolocation','max_time'))))

    if last_ts < (curr_ts - timedelta(minutes=int(config.get('geolocation','max_time')))):
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
        text_msg="можно создать только 1 метку в течении" +config.get('geolocation','max_time')+" минут, с момента создания метки прошло : "+spl_delta[0]
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)
    session.close()


def resp_location(update, context):
    print("resp location")
    user_data = update.message.chat
    home_keyboard = KeyboardButton(text="/home Вернуться в начало")
    last_map_keyboard = KeyboardButton(text="/last  загрузить предыдущую карту")
    custom_keyboard = [[home_keyboard, last_map_keyboard]]
    if r.exists(user_data['id']):
        print(update.message.location, r.get(user_data['id']).decode("utf-8"),user_data['id'])
        geo_center = (config.get('geolocation','center_latitude'),config.get('geolocation','center_longitude') )
        geo_user=(update.message.location.latitude,update.message.location.longitude)
        distance=geodesic(geo_center, geo_user).kilometers
        max_d=config.get('geolocation','max_distance')
        if float(distance) > float(max_d):
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            messagetext="Ух... как вы далеко забрались!\n\rК сожалению радиус меток "+config.get('geolocation','max_distance')+" км"
            context.bot.send_message(chat_id=update.message.chat_id, text=messagetext, reply_markup=reply_markup)
            print("distance to long ",user_data['id'], "distance", distance)
        else:
            print("catch point")
            ts = datetime.utcnow()
            tz = timezone('Asia/Yekaterinburg')
            ts = ts.replace(tzinfo=timezone('UTC')).astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
            print(ts)
            db_loc = Locations(str(user_data['id']), str(update.message.location.longitude), str(update.message.location.latitude), str(ts) , str(r.get(user_data['id']).decode("utf-8")),0)
            session.add(db_loc)
            session.commit()
            print("point writed for userid ",user_data['id'], "distance", distance)
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            context.bot.send_message(chat_id=update.message.chat_id, text="метка принята. Карта с вашей меткой будет опубликованна в основном канале", reply_markup=reply_markup)
    else:
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        messagetext = "Упс! что то пошло не так, попробуйте снова позже"
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext, reply_markup=reply_markup)


def report(update, context):
    if check_user(update.message.chat['id'],"report")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,text="Результаты исследования проб воздуха(официальные данные)", reply_markup=reply_markup)
        doclist = get_doc.s("call_bot_app").delay()
        doclist = doclist.get(timeout=2700)
        if not doclist:
            print('empty no new documents')
            context.bot.send_message(chat_id=update.message.chat_id,text="новых документов пока нет",reply_markup=reply_markup)
        else:
            for msg in doclist:
                context.bot.sendDocument(chat_id=update.message.chat_id, document=open(msg, 'rb'))


def state(update, context):
    if check_user(update.message.chat['id'],"state")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        status_keyboard = KeyboardButton(text="/sensors")
        graph_keyboard = KeyboardButton(text="/graphs")
        home_keyboard = KeyboardButton(text="/home")
        custom_keyboard = [[status_keyboard, graph_keyboard,home_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_message ="/sensors текущее состояние датчиков \n\r/graph отчет ввиде графиков\n\r/home вернуться в начало"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)



def home(update, context):
    if check_user(update.message.chat['id'],"home")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        status_keyboard = KeyboardButton(text="/state")
        weather_keyboard = KeyboardButton(text="/weather")
        camera_keyboard = KeyboardButton(text="/camera")
        map_keyboard = KeyboardButton(text="/map")
        generate_keyboard = KeyboardButton(text="/report")
        help_keyboard = KeyboardButton(text="/help")
        custom_keyboard = [[status_keyboard, weather_keyboard, camera_keyboard, map_keyboard, generate_keyboard,help_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_message = "С помощью бота можно узнать:\n\rв каком состоянии сейчас общественные датчики: /state \n\rсводку погоды: /weather \n\rполучить ссылки на камеры установленные на бортах: /camera \n\r Также если вы почувствовали какой то запах вы можете создать собственную метку на карте и она будет опубликована: /map\n\r загрузить официальные результаты замеров: /report\n\r помощь /help "
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)

def weather_resp(update, context):
    if check_user(update.message.chat['id'],"weather")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        messagetext = weather_task.delay()
        messagetext2 = messagetext.get(timeout=300)
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext2, reply_markup=reply_markup,parse_mode='MARKDOWN')

def sensors(update, context):
    if check_user(update.message.chat['id'],"sensors")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        messagetext="Последние полученные данные:"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext)
        try:
            so2_stat = json.loads(r.get('so2_s').decode("utf8"))
            for so2 in so2_stat:
                message=so2['street']+": "+so2['value']+"\n\rдата : "+so2['time']
                context.bot.send_message(chat_id=update.message.chat_id, text=message,parse_mode='MARKDOWN')
        except:
            message="Датчики SO2 недоступны"
            context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='MARKDOWN')
        try:
            hcl_stat = json.loads(r.get('hcl_s').decode("utf8"))
            for hcl in hcl_stat:
                message=hcl['street']+": "+hcl['value']+"\n\rдата : "+hcl['time']
                context.bot.send_message(chat_id=update.message.chat_id, text=message,parse_mode='MARKDOWN')
        except:
            message = "Датчики HCL недоступны"
            context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='MARKDOWN')
        messagetext = "/home Вернуться в начало"
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext, reply_markup=reply_markup,parse_mode='MARKDOWN')


def help(update, context):
    if check_user(update.message.chat['id'],"state")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        main_keyboard = KeyboardButton(text="/help_main")
        bot_keyboard = KeyboardButton(text="/help_bot")
        emerg_keyboard = KeyboardButton(text="/help_emerg")
        home_keyboard = KeyboardButton(text="/home")
        custom_keyboard = [[main_keyboard, bot_keyboard,emerg_keyboard,home_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_message ="/help_main faq (часто задаваемые вопросы) \n\r/help_bot информация о том как пользоваться ботом \n\r/help_emerg информация об экстренных слубах и номера телефонов \n\r/home вернуться в начало"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)

def help_emerg(update, context):
    if check_user(update.message.chat['id'],"cam")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        help_keyboard = KeyboardButton(text="/help Вернуться в начало")
        custom_keyboard = [[help_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_msg = "Контакты и телефоны экстренных служб города \n\r 112 служба спасения \n\r 101 пожарная \n\r 102 полиция \n\r 103 скорая помощь \n\r 104 газовая служба"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)

def help_main(update, context):
    if check_user(update.message.chat['id'],"cam")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        help_keyboard = KeyboardButton(text="/help Вернуться в начало")
        custom_keyboard = [[help_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_msg = "Q: Что отображается на карте \n\rA: при загрузке карты вы увидите что круглыми значками отображаются данные с датчиков , флажками отмечаются метки пользователей \n\r"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        text_msg = "Q: что за значение в разделе sensors \n\rA: это сырые данные получаемые с прибора это значение нужно умножить на 2 чтобы получить значение в пдк"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        text_msg = "Q: как часто обновляются данные \n\r A: данные от приборов запрашиваются раз в 5 минут \n\r официальные отчеты запрашиваются раз в 30 минут а затем ротируются раз в 10 часов \n\r карты создаются раз в 3 часа а затем ротируются раз в 6 часов"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        text_msg = "/help вернуться в предыдущее меню"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)

def help_bot(update, context):
    if check_user(update.message.chat['id'],"cam")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/help Вернуться")
        custom_keyboard = [[home_keyboard]]
        text_msg = "Q: Начало работы с ботом для IOS и Android нажмите Start \n\rA: кнопка Start выделена овалом"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/ios/start_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/android/start_android.jpg", 'rb'))
        # context.bot.send_media_group(chat_id=update.message.chat_id, media = [types.InputMediaPhoto("data/images/ios/start_ios.jpg"),open("data/images/android/start_android.jpg",'rb')])
        text_msg = "Q: Первый экран Приветсвие \n\rA: у вас появится новая кнопка home (главное меню ) текст выденный синим так же работает  как кнопка"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/ios/first_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/android/first_android.jpg", 'rb'))
        text_msg = "Q: что делать если у вас не отображается клавиатура внизу экрана\n\rA: нажмите на значок выделенный овалом и клавитура снова окажется внизу экрана "
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id,
                              photo=open("data/images/ios/hidden_keyboard_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id,
                              photo=open("data/images/android/hidden_keyboard_android.jpg", 'rb'))
        text_msg = "Q: что делать если у вас не корректно отображается клавиатура внизу экрана\n\rA: пропробуйте расположить устройство в горизонтально(скорее всего это связанно с малым размером дисплея)"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/ios/horizontal_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id,
                              photo=open("data/images/android/horizontal_android.jpg", 'rb'))
        text_msg = "Q: как отключить звук для бота или канала \n\rA: выберите меню чата в верхнем правом углу чата затем выберите пункт Notification "
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/ios/notification_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id,
                              photo=open("data/images/android/notification_android.jpg", 'rb'))
        text_msg = "Затем выберите время на которое хотите отключить звуковые уведомления"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg)
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/ios/mute_ios.jpg", 'rb'))
        context.bot.sendPhoto(chat_id=update.message.chat_id, photo=open("data/images/android/mute_android.jpg", 'rb'))
        text_msg = "/help вернуться в предыдущее меню"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)




def cams(update, context):
    if check_user(update.message.chat['id'],"cam")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        sol=solar_time.delay()
        sol = sol.get(timeout=2700)
        print(sol)
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]

        messagetext = "Cеверный борт:"
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext)
        context.bot.send_message(chat_id=update.message.chat_id, text=config.get('cams', 'cam_north'))
        messagetext = "Южный борт:"
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext)
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=config.get('cams', 'cam_south'))
        messagetext = "учитывайте cветлое время суток при просмотре видео с камер тк в ночное время почти ничего не видно\n\r "
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext)
        messagetext="расчетное время заката : "+sol[0]+"\n\r"+"расчетное время рассвета : "+sol[1]
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext, reply_markup=reply_markup)
def graph(update, context):
    if check_user(update.message.chat['id'],"graph")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        text_msg = "раздел пока еще не сформирован"
        context.bot.send_message(chat_id=update.message.chat_id, text=text_msg, reply_markup=reply_markup)

def last(update, context):
    if check_user(update.message.chat['id'],"last")==1:
        start_keyboard = KeyboardButton(text="/start")
        custom_keyboard = [[start_keyboard]]
        text_message = "Чтобы начать нажмите /start"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=text_message, reply_markup=reply_markup)
    else:
        home_keyboard = KeyboardButton(text="/home Вернуться в начало")
        custom_keyboard = [[home_keyboard]]
        map = get_map.s("call_bot_app").delay()
        map = map.get(timeout=2700)
        messagetext = "последнее"
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id, text=messagetext,reply_markup=reply_markup)
        context.bot.sendDocument(chat_id=update.message.chat_id, document=open(map, 'rb'))




start_handler = CommandHandler('start', start)
new_handler = CommandHandler('new', create_point)
sensors_handler = CommandHandler('sensors', sensors)
state_handler = CommandHandler('state', state)
graph_handler = CommandHandler('graph', graph)
weather_handler=CommandHandler('weather', weather_resp)
help_handler = CommandHandler('help', help)
help_main_handler = CommandHandler('help_main', help_main)
help_bot_handler = CommandHandler('help_bot', help_bot)
home_handler = CommandHandler('home', home)
last_handler = CommandHandler('last', last)
cams_handler = CommandHandler('camera', cams)
map_handler= CommandHandler('map', map)
report_handler = CommandHandler('report', report)
req_handler = MessageHandler(Filters.entity("hashtag"), req_location)
resp_handler = MessageHandler(Filters.location, resp_location)
dispatcher.add_handler(last_handler)
dispatcher.add_handler(cams_handler)
dispatcher.add_handler(new_handler)
dispatcher.add_handler(weather_handler)
dispatcher.add_handler(req_handler)
dispatcher.add_handler(resp_handler)
dispatcher.add_handler(map_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(sensors_handler)
dispatcher.add_handler(state_handler)
dispatcher.add_handler(help_main_handler)
dispatcher.add_handler(help_bot_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(graph_handler)
dispatcher.add_handler(home_handler)
dispatcher.add_handler(report_handler)
print("bot_app is started ...")
updater.start_polling()
updater.idle()