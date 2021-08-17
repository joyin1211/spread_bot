import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import config
import logging
import word_parser
import json
from telegram import ReplyKeyboardMarkup

help_text = 'Чтобы использовать бота в личном чате: зайдите в участников группы, найдите бота, нажмите на него,\n' \
            'нажмите на кнопку отправить сообщение или send message, после этого начните работу.\n' \
            'У бота есть две команды: /HelpMe и /ICan.\n' \
            '/HelpMe + слово/словосочетание: Бот выдает всех людей, которые могут помочь с <слово>. Если Вы\n' \
            'пишете эту команду без тега, то бот попросит вас ввести тег следующим сообщением. Если вы не\n' \
            'захотите вводить тег после этого, то напишите команду /stop и продолжайт пользоваться ботом.\n' \
            '/ICan + слово/словосочетание: Бот выдает всех людей, которым нужна Ваша помощь с этим словом. \n' \
            'Инструкция пользования та же, что и с /HelpMe \n' \
            '/help: Инструкция по использованию бота\n' \
            'Приятного пользования! \n' \
            'надеюсь это сработает.'
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = config.TOKEN
bot = telegram.Bot(TOKEN)


# команда start
def start(update, context):
    reply_keyboard = [['/HelpMe', '/ICan'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Используйте /help, чтобы узнать команды бота.', reply_markup=markup)


# команда help
def help(update, context):
    reply_keyboard = [['/HelpMe', '/ICan'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    global help_text
    update.message.reply_text(help_text, reply_markup=markup)


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# получаем информацию с таблицы
def getinfo():
    # Авторизуемся и получаем service — экземпляр доступа к API
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        config.CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth, cache_discovery=False)
    values = service.spreadsheets().values().get(
        spreadsheetId=config.SPREADSHEET_ID,
        range='A1:G1000',
        majorDimension='ROWS'
    ).execute()
    return values["values"]


# шаблон для основных команд
def commandTemplate(update, kol):
    from word_parser import tagFormsList
    msg: telegram.Message = update.message
    data = getinfo()
    # строим tag
    if msg.text[0] == '/':
        tag = ' '.join(msg.text.split()[1:])
    else:
        tag = msg.text
    # если tag пустой, то возращаем сообщение об ошибке
    if tag == '':
        return "Вы не ввели тег, по которому будет идти поиск"
    tag = tag.lower()
    print(tag)
    new_message = tag + ' : '
    users = []
    forms = tagFormsList(tag)
    print(forms)
    # во всех формах заменяем ё на е
    for flist in range(len(forms)):
        for form in range(len(forms[flist])):
            forms[flist][form] = forms[flist][form].replace('ё', 'е')
    # производим поиск по данным нам столбцам, если находим нужного пользователя,
    # добавляем в список его ФИО и номер телефона указанные в таблице
    for num in kol:
        for i in data:
            if len(i) == 0:
                break
            if len(i) < num:
                continue
            if word_parser.find(i[num - 1].lower(), forms):
                users.append(i[1] + ' (' + i[2] + ')')
    # удаляем повторяющиеся фамилии
    from itertools import groupby
    new_users = [el for el, _ in groupby(users)]
    new_message += '\n'.join(new_users)
    return new_message


def table(update, context):
    msg: telegram.Message = update.message
    data = getinfo()
    msg.reply_text(data[0])


# WE KICKED A KID - UNITED
# функция отвечающая за поиск в 4,5,6 столбцах
def united(update, context):
    msg: telegram.Message = update.message
    user = msg.from_user
    print(msg.text)
    # если текст сообщения - команда и не /helpme, то выдаем текст помощи, иначе - достаем тэг
    if msg.text[0] == '/':
        com = msg.text.split()[0]
        com = com.lower()
        if com[:7] == '/helpme':
            tag = ' '.join(msg.text.split()[1:])
        else:
            reply_keyboard = [['/HelpMe', '/ICan'],
                              ['/start', '/help']]
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            global help_text
            msg.reply_text(help_text, reply_markup=markup)
            return ConversationHandler.END
    else:
        tag = msg.text
    # если тэг пустой, то просим ввести следющим сообщением
    if tag == '':
        reply_keyboard = [['/HelpMe', '/ICan'],
                          ['/start', '/help', '/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        msg.reply_text("Введите тег, по которому будет вести поиск", reply_markup=markup)
        return 1
    # выдаем пользоваетелей и заканчиваем диалог
    reply_keyboard = [['/HelpMe', '/ICan'],
                      ['/start', '/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    new_message = commandTemplate(update, [4, 5, 6])
    try:
        user.send_message(new_message)
    except Exception:
        msg.reply_text(new_message, reply_markup=markup)
    return ConversationHandler.END


# функция отвечающая за поиск в 7 столбце, та же структура что и в united
def getUserByNeed(update, context):
    msg: telegram.Message = update.message
    user = msg.from_user
    if msg.text[0] == '/':
        com = msg.text.split()[0]
        com = com.lower()
        if com[:5] == '/ican':
            tag = ' '.join(msg.text.split()[1:])
        else:
            reply_keyboard = [['/HelpMe', '/ICan'],
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
        reply_keyboard = [['/HelpMe', '/ICan'],
                          ['/start', '/help', '/stop']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        msg.reply_text("Введите тег, по которому будет вести поиск", reply_markup=markup)
        return 1
    reply_keyboard = [['/HelpMe', '/ICan'],
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
    # обработчик команды /helpme. ConversationHandler, из-за возможности ввести тэг следующим сообщением
    needhelp_handler = ConversationHandler(
        entry_points=[CommandHandler('HelpMe', united)],
        states={
            1: [MessageHandler(Filters.text, united)],
        },

        fallbacks=[]
    )
    # обработчик команды /ican
    myhelp_handler = ConversationHandler(
        entry_points=[CommandHandler('ICan', getUserByNeed)],
        states={
            1: [MessageHandler(Filters.text, getUserByNeed)],
        },

        fallbacks=[]
    )
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(needhelp_handler)
    dp.add_handler(myhelp_handler)

    dp.add_handler(CommandHandler("start", start))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
