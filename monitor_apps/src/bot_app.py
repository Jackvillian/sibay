from telegram.ext import Updater, CommandHandler, MessageHandler,Filters
from telegram import KeyboardButton, ReplyKeyboardMarkup
import configparser

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
    context.bot.send_message(chat_id=update.message.chat_id, text="Хотите создать метку на карте?", reply_markup=reply_markup)

def location

start_handler = CommandHandler('start', start)
dispatcher.add_handler(MessageHandler(Filters.text, location))
dispatcher.add_handler(start_handler)

updater.start_polling()