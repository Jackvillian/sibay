from telegram.ext import Updater, CommandHandler, MessageHandler,Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
from models.model import Base ,engine,User
from sqlalchemy.orm import sessionmaker
import os
import configparser
import sqlalchemy
Session = sessionmaker(bind=engine)
session = Session()
#vasiaUser = User("vasia", "Vasiliy", "vasia2000")
#session.add(vasiaUser)
#session.commit()

config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_path)


updater = Updater(config.get('telegram','botapikey'), use_context=True)
dispatcher = updater.dispatcher



def start(update, context):
    print(update)
    location_keyboard = KeyboardButton(text="Создать метку", request_location=True)

    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.message.chat_id, text="Хотите запросить отчет или хотите создать метку на карте?", reply_markup=reply_markup)



def echo(update, context):
    print(update.message.location, update.message.chat)

    context.bot.send_message(chat_id=update.message.chat_id, text="Метка установлена!")

def generate():
    pass

start_handler = CommandHandler('start', start)
generate_handler = CommandHandler('generate', generate)
echo_handler = MessageHandler(Filters.location, echo)
dispatcher.add_handler(echo_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(generate_handler)

updater.start_polling()
updater.idle()