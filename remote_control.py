'''
Remote control module
Allows to enable or disable bot and download log file
Модуль дистанционного управления
Позволяет включить/выключить бота и скачать лог-файл
'''

import os
from platform import system
from queue import Queue
from sys import argv, exit
from threading import Thread

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

users = []
state = False
bot_path = ''
shell = ''

class Bot(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.queue = Queue

    def run(self):
        os.system(f'{shell}')

def start(update: Update, context: CallbackContext):
    '''
    Start command
    Команда старта
    '''
    tg_id = update.effective_user.id
    if tg_id not in users:
        with open('rc_users', 'r') as rc_users:
            admins = rc_users.split(',')
            if tg_id not in admins:
                update.message.reply_text('Пользователь не найден.')
                return
        users.append(tg_id)
    # Включить бота  |  Выключить бота
    # Скачать лог-файл
    if state:
        keyboard = [ 'Выключить бота' ]
    else:
        keyboard = [ 'Запустить бота' ]
    keyboard.append('Скачать лог-файл')
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text('Действие: ', reply_markup=reply_markup, resize_keyboard=True)

def enable(update: Update, context: CallbackContext):
    '''
    Enable bot
    Включить бота
    '''
    pass

if __name__ == '__main__':
    if len(argv) > 1:
        bot_path = argv[1]
    else:
        bot_path = 'main.py'

    if len(argv) > 2:
        shell = argv[2]
    else:
        sys_type = system()
        if sys_type == 'Windows':
            shell = 'cmd'
        elif sys_type == 'Linux':
            shell = '/bin/bash'
        else:
            print('Error: unknown system')
            exit()
