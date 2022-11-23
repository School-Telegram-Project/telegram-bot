'''
Remote control module
Allows to enable or disable bot and download log file
Модуль дистанционного управления
Позволяет включить/выключить бота и скачать последний лог-файл
'''

import re
import functools
from sys import argv, exit
from pathlib import Path

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram.constants import PARSEMODE_HTML as HTML

from main import begin as main_begin, UPDATER as main_updater

users = []
# 0 = Did not begin, 1 = Stopped, 2 = Working
# 0 = Не запущен, 1 = Остановлен, 2 = Работает
state = 0

def keyboard(self) -> list:
    '''
    Generate main keyboard
    Создать основную клавиатуру
    '''
    keyboard = [
        [f'{"Выключить бота" if self.state < 2 else "Запустить бота"}'],
        ['Скачать последний лог-файл'],
        ['Добавить нового пользователя', 'Удалить пользователя']
    ]

@functools.lru_cache(maxsize=8)
def auth(user_id: int):
    '''
    User authentication
    Аунтефикация пользователя
    '''
    if users and user_id in users:
        return True
    admins = []
    with open('rc_users', encoding='UTF-8') as rc_users:
        for l in rc_users.readlines():
            admins.extend(l.split(','))
    if str(user_id) in admins:
        users.append(user_id)
        return True
    return False

def start(update: Update, context: CallbackContext):
    '''
    Start command
    Команда старта
    '''
    tg_id = update.effective_user.id
    if not auth(tg_id):
        update.message.reply_text('Пользователь не найден')
        return
    if tg_id not in users:
        users.append(tg_id)
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Действие:', reply_markup=reply_markup)

def enable(update: Update, context: CallbackContext):
    '''
    Enable bot
    Включить бота
    '''
    global main_updater, state
    if not auth(update.effective_user.id):
        update.message.reply_text('Пользователь не найден')
        return
    if state > 1:
        context.bot.send_message(chat_id = update.effective_chat.id, text='Бот уже запущен')
        return
    if state < 1:
        main_updater = main_begin()
        main_updater.dispatcher.add_error_handler(error_handler)
    else:
        main_updater.start_polling()
    state = 2
    keyboard = [['Выключить бота'],
                ['Скачать лог-файл']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Выполнено', reply_markup=reply_markup)

def disable(update: Update, context: CallbackContext):
    '''
    Disable bot
    Выключить бота
    '''
    global state
    if not auth(update.effective_user.id):
        update.message.reply_text('Пользователь не найден')
        return
    if state < 2:
        context.bot.send_message(chat_id = update.effective_chat.id, text='Бот ещё не запущен')
        return
    main_updater.stop()
    state = 1
    keyboard = [['Запустить бота'],
                ['Скачать последний лог-файл']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Выполнено', reply_markup=reply_markup)

def date_sort(a: Path, b: Path):
    '''
    Function for sorting log files by date
    Функция сортировки лог-файлов по дате
    '''
    a_i = int(a.stem.replace('.', '')[:8])
    b_i = int(b.stem.replace('.', '')[:8])
    # return 1 if a_i >= b_i, else return -1
    return 1 - 2 * int(a_i < b_i)

def download(update: Update, context: CallbackContext):
    '''
    Download log files
    Загрузить лог-файлы
    '''
    if not auth(update.effective_user.id):
        update.message.reply_text('Пользователь не найден')
        return
    path = Path(argv[0]).resolve().cwd() / 'logs'
    files = []
    for f in path.iterdir():
        if f.is_file() and re.findall(r'[0-9]{4}-[0-9]{2}-[0-9]{2}\.txt', f.stem):
            files.append(f)
    if len(files) < 1:
        text = 'Файлов логирования не найдено'
        context.bot.send_message(chat_id = update.effective_chat.id, text=text)
    file_path = sorted(files, functools.cmp_to_key(date_sort))[0]
    with file_path.open(encoding='UTF-8') as file:
        context.bot.send_document(chat_id = update.effective_chat.id, document=file)

def add_user(update: Update, context: CallbackContext):
    '''
    Add new user to main bot
    Добавить нового пользователя через бота
    '''
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
         "Возникла ошибка при работе основного бота\n"
        f"<pre>Событие: {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
         "</pre>\n\n"
        f"<pre>Данные чата: {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>Данные пользователя: {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    for user_id in users:
        context.bot.send_message(text=message,chat_id=user_id,parse_mode=HTML)

def unknown(update: Update, context: CallbackContext):
    '''
    Unknown/wrong command
    Неизвестная/ошибочная команда
    '''
    context.bot.send_message(text='Неизвестная команда', chat_id=update.effective_chat.id)

def error_handler(update: Update, context: CallbackContext) -> None:
    '''
    Error handler that redirects errors from main bot to RC users
    Обработчик ошибок, который пересылает ошибки с основного бота пользователям удалённого управления
    '''

def begin():
    '''
    Start RC bot
    Запустить бота удалённого управления
    '''
    try:
        with open('rc_secret', encoding='UTF-8') as file:
            token = file.readline().strip()
        if token is None or token.strip() == '':
            raise IOError()
    except IOError:
        print('No token file')
        exit(1)
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    enable_handler = MessageHandler(Filters.text &
                                    Filters.regex('(?i)запустить бота'),
                                    enable)
    dispatcher.add_handler(enable_handler)
    disable_handler = MessageHandler(Filters.text &
                                    Filters.regex('(?i)выключить бота'),
                                    disable)
    dispatcher.add_handler(disable_handler)
    download_handler = MessageHandler(Filters.text &
                                      Filters.regex('(?i)скачать последний лог-файл'),
                                      download)
    dispatcher.add_handler(download_handler)
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

if __name__ == '__main__':
    begin()
