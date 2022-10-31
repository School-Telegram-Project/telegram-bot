'''
Main module
Основной модуль
'''

from datetime import datetime

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

import files
import logs
import vars

def start(update: Update, context: CallbackContext):
    '''
    Start command
    Команда старта
    '''

    keyboard = [
        [ 'Замена' ],
        [ 'Собрание' ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    logs.message(f'User {update.effective_user.id} sended /start')
    update.message.reply_text('Тип сообщения:', reply_markup=reply_markup)
    vars.state = [0, 1]

# TODO: улучшенное меню помощи
def help(update: Update, context: CallbackContext):
    '''
    Help menu
    Меню помощи
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text='Используйте /start для старта')

def plain_text(update: Update, context: CallbackContext):
    '''
    Message with no command
    Сообщение без команды (/...)
    '''

    text = update.message.text.lower()
    if vars.state == [0, 0]:
        start(update=update, context=context)
    elif text == 'замена':
        context.bot.send_message(chat_id=update.effective_chat.id, text='Отправьте файл замен:')
        vars.state = [1, 0]
    elif text == 'собрание':
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        vars.state = [2, 0]
        

def document(update: Update, context: CallbackContext):
    '''
    Downloading files
    Получение файла
    '''
    if vars.state == [1, 0]:
        logs.message(f'File name: {update.message.document.file_name}')
        file_type = update.message.document.file_name.split('.')[-1]
        time = datetime.now().time()
        file_name = f'/mnt/data/Programming/telegram-bot/downloads/{time}.{file_type}'
        with open(file_name, 'wb') as file:
            logs.message(f'Download name: {file_name}')
            context.bot.get_file(update.message.document).download(out=file)
            errors = files.save_replacements_from_docx(file_name)
            if errors > 0:
                t = f'Возникла ошибка, не удалось загрузить {errors} строк'
                context.bot.send_message(chat_id = update.effective_chat.id, text=t)
        
def look(update: Update, context: CallbackContext):
    # TODO: Закончить интерфейс учителя
    '''
    Read replacements from database
    Takes teacher as argument
    Считывает замены с базы данных
    Получает учителя в качестве аргумента
    '''
    teacher = update.message.text.replace('/look ', '')
    replacements = files.read_replacements(teacher)
    if not isinstance(replacements, list):
        t = 'Не удалось прочитать базу данных'
        context.bot.send_message(chat_id = update.effective_chat.id, text=t)
        return
    t = '-------\n'
    for r in replacements:
        t += f'Замена у {r[0]} класса на {r[1]} уроке'
        if r[2] != 'NULL':
            t += f' в {r[2]} кабиенете'
        t += '\n---\n'
    t = t.strip('\n')
    context.bot.send_message(chat_id=update.effective_chat.id, text=t)

def unknown(update: Update, context: CallbackContext):
    '''
    Unknown/wrong command
    Неизвестная/ошибочная команда
    '''
    context.bot.send_message(chat_id=update.effective_chat.id, text='Неизвестная команда')

def begin():
    '''
    Start chat-bot
    Запуск чат-бота
    '''
    with open('secret', 'r') as file:
        token = file.readline()
    if token is None or token == '' or token.isspace():
        exit()
    vars.updater = Updater(token=token)
    vars.dispatcher = vars.updater.dispatcher
    vars.state = [0, 0]
    start_handler = CommandHandler('start', start)
    vars.dispatcher.add_handler(start_handler)
    plain_text_handler = MessageHandler(Filters.text & (~Filters.command), plain_text)
    vars.dispatcher.add_handler(plain_text_handler)
    document_hanlder = MessageHandler(Filters.document, document)
    vars.dispatcher.add_handler(document_hanlder)
    look_handler = CommandHandler('look', look)
    vars.dispatcher.add_handler(look_handler)
    unknown_handler = MessageHandler(Filters.command, unknown)
    vars.dispatcher.add_handler(unknown_handler)

    vars.updater.start_polling()

if __name__ == '__main__':
    logs.setup()
    begin()
