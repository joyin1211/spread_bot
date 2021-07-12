## -*- coding: utf-8 -*-
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import config
import logging
import word_parser
import json
from telegram import ReplyKeyboardMarkup
import sys
import codecs

help_text = 'Чтобы использовать бота в личном чате: зайдите в участников группы, найдите бота, нажмите на него,\n' \
            'нажмите на кнопку отправить сообщение или send message, после этого начните работу.\n' \
            'У бота есть две команды: /HelpMe и /HelpFromMe.\n' \
            '/HelpMe + слово/словосочетание: Бот выдает всех людей, которые связаны с <слово>. Если Вы\n' \
            'пишете эту команду без тега, то бот попросит вас ввести тег следующим сообщением. Если вы не\n' \
            'захотите вводить тег после этого, то напишите команду /stop и продолжайт пользоваться ботом.\n' \
            '/ICanHelp + слово/словосочетание: Бот выдает всех людей, которым нужна Ваша помощь с этим словом. \n' \
            'Инструкция пользования та же, что и с /HelpMe \n' \
            '/help: Инструкция по использованию бота\n' \
            'Приятного пользования! \n' \
            'надеюсь это сработает.'
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = config.TOKEN
bot = telegram.Bot(TOKEN)
def start(update, context):
    reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Используйте /help, чтобы узнать команды бота. Также Дамир очень '
                              'извиняется за долгое ожидание', reply_markup=markup)


def help(update, context):
    reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    global help_text
    update.message.reply_text(help_text, reply_markup=markup)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def getinfo():
    # Авторизуемся и получаем service — экземпляр доступа к API
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config.CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth, cache_discovery=False)
    values = service.spreadsheets().values().get(
        spreadsheetId=config.spreadsheet_id,
        range='A1:G1000',
        majorDimension='ROWS'
    ).execute()
    return values["values"]


def commandTemplate(update, kol):
    from word_parser import tagFormsList
    msg: telegram.Message = update.message
    tag1 = msg.text
    data = getinfo()
    if msg.text[0] == '/':
        tag = ' '.join(msg.text.split()[1:])
    else:
        tag = msg.text
    if tag == '':
        return "Вы не ввели тег, по которому будет идти поиск"
    tag = tag.lower()
    print(tag)
    new_message = tag + ' : '
    users = []
    forms = tagFormsList(tag)
    print(forms)
    if forms[0] == -1:
        return "Полученный тег не удовлетворяет условиям"
    for flist in range(len(forms)):
        for form in range(len(forms[flist])):
            forms[flist][form] = forms[flist][form].replace('ё', 'е')
    for num in kol:
        for i in data:
            if len(i) == 0:
                break
            if len(i) < num:
                continue
            if word_parser.find(i[num - 1].lower(), forms):
                users.append(i[1] + ' (' + i[2] + ')')
    from itertools import groupby
    new_users = [el for el, _ in groupby(users)]
    new_message += '\n'.join(new_users)
    return new_message


def table(update, context):
    msg: telegram.Message = update.message
    data = getinfo()
    msg.reply_text(data[0])


def united(update, context):
    msg: telegram.Message = update.message
    user = msg.from_user
    print(msg.text)
    if msg.text[0] == '/':
        com = msg.text.split()[0]
        com = com.lower()
        if com[:7] == '/helpme':
            tag = ' '.join(msg.text.split()[1:])
        else:
            reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                              ['/start', '/help']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            global help_text
            try:
                user.send_message(help_text)
            except Exception:
                msg.reply_text(help_text, reply_markup=markup)
            return ConversationHandler.END
    else:
        tag = msg.text
    if tag == '':
        reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                          ['/start', '/help', '/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        try:
            user.send_message("Введите тег, по которому будет вести поиск")
        except Exception:
            msg.reply_text("Введите тег, по которому будет вести поиск", reply_markup=markup)
        return 1
    reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    new_message = commandTemplate(update, [4, 5, 6])
    try:
        user.send_message(new_message)
    except Exception:
        msg.reply_text(new_message, reply_markup=markup)
    return ConversationHandler.END


def getUserByNeed(update, context):
    msg: telegram.Message = update.message
    user = msg.from_user
    if msg.text[0] == '/':
        com = msg.text.split()[0]
        com = com.lower()
        if com[:11] == '/helpfromme':
            tag = ' '.join(msg.text.split()[1:])
        else:
            reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                              ['/start', '/help']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            global help_text
            try:
                user.send_message(help_text)
            except Exception:
                msg.reply_text(help_text, reply_markup=markup)
            return ConversationHandler.END
    else:
        tag = msg.text
    if tag == '':
        reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                          ['/start', '/help', '/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        try:
            user.send_message("Введите тег, по которому будет вести поиск")
        except Exception:
            msg.reply_text("Введите тег, по которому будет вести поиск", reply_markup=markup)
        return 1
    reply_keyboard = [['/HelpMe', '/HelpFromMe'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    new_message = commandTemplate(update, [7])
    try:
        user.send_message(new_message)
    except Exception:
        msg.reply_text(new_message, reply_markup=markup)
    return ConversationHandler.END


def main():
    updater = Updater(config.TOKEN, use_context=True)

    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('HelpMe', united)],
        states={
            1: [MessageHandler(Filters.text, united)],
        },

        fallbacks=[]
    )
    myhelp_handler = ConversationHandler(
        entry_points=[CommandHandler('HelpFromMe', getUserByNeed)],
        states={
            1: [MessageHandler(Filters.text, getUserByNeed)],
        },

        fallbacks=[]
    )
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(conv_handler)
    dp.add_handler(myhelp_handler)

    dp.add_handler(CommandHandler("start", start))
    # dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
