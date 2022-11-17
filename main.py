'''
Main module
Основной модуль
'''

from datetime import datetime
from sys import argv, exit

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

import files
import logs
from user import User

users = []

def active_user(tg_id, update: Update, context: CallbackContext):
    '''
    Find user, or call /start if user wasn't found
    Can not be called by user themself
    Найти пользователя, или вызвать /start если пользователь не был найден
    Не может быть вызвано самим пользователем
    '''
    user = None
    for u in users:
        if u == tg_id:
            user = u
    if user is None:
        start(update=update, context=context)
        return active_user(tg_id, update=update, context=context)
    return user

def start(update: Update, context: CallbackContext):
    '''
    Start command
    Команда старта
    '''
    tg_id = update.effective_user.id
    data = files.find_user(tg_id)
    if data is None:
        reply =  'Не удалось найти пользователя в базе данных.\n'
        reply += 'Пожалуйста, обратитесь к администрации.'
        update.message.reply_text(reply)
    else:
        user = User(tg_id, data)
        if user not in users:
            users.append(user)
            logs.message(f'User {tg_id} sended /start')
        else:
            user.state = 0
            logs.message(f'User {tg_id} repeats /start')
        reply_markup = ReplyKeyboardMarkup(user.keyboard(),
                                           resize_keyboard=True)

        update.message.reply_text('Действие:', reply_markup=reply_markup)

def help(update: Update, context: CallbackContext):
    '''
    Help menu
    Меню помощи
    '''
    text = '''
    Используйте команду /start для начала работы с ботом.
    Используйте клавиатуру команд для выбора действия и сделуйте инструкциям.
    '''.strip().replace('    ', '')
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# TODO: удалить полностью
def plain_text(update: Update, context: CallbackContext):
    '''
    Message with no slash command.
    Сообщение без команды /...
    '''
    user = active_user(update.effective_user.id, update, context)
    text = update.message.text.strip()

    if user.state == 0:
        # elif text.lower() == 'добавить замены вручную':
        #     pass

        if text.lower() == 'обновить расписание':
            # user.state = 2
            # text = 'Пожалуйста, загрузите таблицу расписаний:'
            text = 'сделаю потом'
            context.bot.send_message(chat_id=update.effective_chat.id, text=text)

        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Неизвестная команда.')

def view_replacements(update: Update, context: CallbackContext):
    '''
    "Просмотр замен"
    Look for replacements that involve user
    Поиск замен для пользователя
    '''
    user = active_user(update.effective_user.id, update, context)

    logs.message(f'User {user.id} has requested their replacements')
    replacements = files.read_replacements(user.name)
    if not isinstance(replacements, list):
        text = 'Не удалось прочитать базу данных.'
        context.bot.send_message(chat_id = update.effective_chat.id, text=text)
        return

    text = '-------\n'
    for repl in replacements:
        text += f'Замена у {repl[0]} класса на {repl[1]} уроке'
        if repl[2] != 'NULL':
            text += f' в {repl[2]} кабиенете'
        text += '\n---\n'
    text = text.strip('\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def upload_replacements(update: Update, context: CallbackContext):
    '''
    Upload replacements table
    Загрузить таблицу замен
    '''
    user = active_user(update.effective_user.id, update, context)
    user.state = 1
    text = 'Пожалуйста, загрузите таблицу замен:'
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def document(update: Update, context: CallbackContext):
    '''
    Downloading files
    Получение файла
    '''
    user = active_user(update.effective_user.id, update, context)

    if user.state in [1, 2]:
        file_name = update.message.document.file_name
        logs.message(f'User {user.id} has uploaded file {file_name}')
        file_type = file_name.split('.')[-1]
        time = datetime.now().time()
        file_name = f'/mnt/data/Programming/telegram-bot/downloads/{time}.{file_type}'
        logs.message(f'Download name: {file_name}')
        with open(file_name, 'wb') as file:
            context.bot.get_file(update.message.document).download(out=file)
            if user.state == 1:
                result = files.save_replacements_from_docx(file_name)
                if result < 0:
                    text = 'Возникла ошибка, не удалось загрузить часть данных.'
                else:
                    text = 'Данные сохранены.'
            # elif user.state == 2:
            #    logs.message(f'File name: )
        context.bot.send_message(chat_id = update.effective_chat.id, text=text)

def unknown(update: Update, context: CallbackContext):
    '''
    Unknown/wrong command
    Неизвестная/ошибочная команда
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text='Неизвестная команда.')

def begin():
    '''
    Start chat-bot
    Запуск чат-бота
    '''
    with open('secret', 'r') as file:
        token = file.readline().strip()
    if token is None or token == '' or token.isspace():
        exit()
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    view_replacements_handler = MessageHandler(Filters.text &
                                               Filters.regex('(?i)посмотреть замены'),
                                               view_replacements)
    dispatcher.add_handler(view_replacements_handler)
    upload_replacements_handler = MessageHandler(Filters.text &
                                                 Filters.regex('(?i)загрузить файл замен'),
                                                 upload_replacements)
    dispatcher.add_handler(upload_replacements_handler)
    plain_text_handler = MessageHandler(Filters.text & (~Filters.command), plain_text)
    dispatcher.add_handler(plain_text_handler)
    document_hanlder = MessageHandler(Filters.document, document)
    dispatcher.add_handler(document_hanlder)
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

if __name__ == '__main__':
    if len(argv) > 1:
        logs.setup(argv[1])
    else:
        logs.setup()
    begin()
