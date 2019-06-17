from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram import KeyboardButton, ReplyKeyboardMarkup
updater = Updater('878214304:AAE9u2Lym2llC3FEsag0pu5mXeD96AQf1XA', use_context=True)
dispatcher = updater.dispatcher



def start(update, context):
    print(update)
    location_keyboard = KeyboardButton(text="создать метку", request_location=True)

    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(chat_id=update.message.chat_id, text="Would you mind sharing your location and contact with me?", reply_markup=reply_markup)

    #context.bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def location(bot, update):
    message = None
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    current_pos = (message.location.latitude, message.location.longitude)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)






updater.start_polling()