'''
Main module
Основной модуль
'''

from datetime import datetime
from functools import lru_cache as cache
# TODO: Локализация
# import gettext
from pathlib import Path
from sys import argv, exit

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram.constants import PARSEMODE_HTML as HTML

import files
import logs
from user import User, VIEW_REPLACEMENTS, UPLOAD_REPLACEMENTS_FILE

UPDATER = None
SELF_PATH = None
users = []

# def get_translator(lang: str = 'ru'):
#     '''
#     Find translation for user
#     Найти перевод для пользователя
#     '''
#     trans = gettext.translation('', localedir=SELF_PATH/'locale', languages=(lang,))
#     return trans.gettext

@cache()
def auth(user_id: int) -> User: #, update: Update):
    '''
    Find user; not command handler
    Найти пользователя; не является обработчиком команды
    '''
    user = None
    for listed_user in users:
        if listed_user == user_id:
            user = listed_user
    return user

def new_user():
    '''
    Add new user
    Добавить нового пользователя
    '''

def start(update: Update, context: CallbackContext) -> None:
    '''
    Start command
    Команда старта
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    user = auth(update.effective_user.id)
    if user is None:
        data = files.find_user(update.effective_chat.id)
        if data is not None:
            users.append(User(data))
        else:
            keyboard = [ [KeyboardButton('Отправить номер', request_contact=True)] ]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                resize_keyboard=True, one_time_keyboard=True)
            text = _(
                '<b>Здравствуйте!</b>\n'
                'Я школьный чат-бот, созданный для отправки информации, '
                'которая касается только Вас. Вы можете узнать о своих заменах'
                'с моей помощью. Но перед работой мне нужно получить Ваш '
                'номер, чтобы занести его в базу данных, пожалуйста, '
                'подтвердите это действие, нажав на кнопку <i>Отправить номер</i> ниже.'
            )
            update.message.reply_text(text=text, parse_mode=HTML, reply_markup=reply_markup)
            return
    logs.message(f'User {user.id} sended /start')
    user.state = 0
    reply_markup = ReplyKeyboardMarkup(user.keyboard(),
                                        resize_keyboard=True)
    text = _('Выберите действие с помощью клавиатуры...')
    update.message.reply_text(text=text, reply_markup=reply_markup)

def help(update: Update, context: CallbackContext) -> None:
    '''
    Help menu
    Меню помощи
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    text = _('Используйте команду <i>/start</i> для начала работы с ботом. '
             'Используйте клавиатуру команд для выбора действия и сделуйте инструкциям.')
    context.bot.send_message(text=text, chat_id=update.effective_chat.id, parse_mode=HTML)

def contact(update: Update, context: CallbackContext) -> None:
    '''
    Contact message
    Сообщение с контактом
    '''
    ct = update.effective_message.contact
    if update.effective_user.id != ct.user_id:
        context.bot.send_message(text='Пожалуйста, отправьте <b>свой</b> контакт.',
                                 chat_id=update.effective_chat.id,
                                 parse_mode=HTML)
        return
    data = files.find_user(ct.user_id, ct.phone_number)
    if data is None:
        # TODO: Сообщение
        context.bot.send_message(chat_id=update.effective_chat.id, text='нет в базе')
        return
    users.append(User(data))
    start(update, context)

def view_replacements(update: Update, context: CallbackContext) -> None:
    '''
    Look for replacements that involve user
    Поиск замен для пользователя
    '''
    user = auth(update.effective_user.id) #, update)
    if user is None:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    logs.message(f'User {user.id} has requested their replacements')
    replacements = files.read_replacements(user.name)
    if replacements is None:
        text = _('Не удалось прочитать базу данных.')
        context.bot.send_message(chat_id = update.effective_chat.id, text=text)
        return
    if not replacements: # length = 0
        text = _('Замены на сегодня не найдены.')
        context.bot.send_message(text=text, chat_id=update.effective_chat.id)
        return

    text = _('<b>Замены на сегодня:</b>') + '\n\n'
    for repl in replacements:
        text += _('Замена у {0} класса на {1} уроке').format(repl[0], repl[1])
        if repl[2] != 'NULL':
            text += _(' в {0} кабиенете').format(repl[2])
        text += '<s>          </s>'
    text = text.strip('\n')
    context.bot.send_message(text=text, chat_id=update.effective_chat.id, parse_mode=HTML)

def upload_replacements(update: Update, context: CallbackContext) -> None:
    '''
    Upload replacements table
    Загрузить таблицу замен
    '''
    user = auth(update.effective_user.id) # , update)
    if user is None:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    user.state = 1
    text = _('Пожалуйста, загрузите таблицу замен:')
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)

def document(update: Update, context: CallbackContext) -> None:
    '''
    Downloading files
    Получение файла
    '''
    user = auth(update.effective_user.id) # , update)
    if user is None:
        return
    if user.state in [1, 2]:
        # _ = get_translator(update.effective_user.language_code)
        _ = str
        user.state = 0
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
                    text = _('Возникла ошибка, не удалось загрузить часть данных.')
                else:
                    text = _('Данные сохранены.')
            # elif user.state == 2:
            #    logs.message(f'File name: )
        context.bot.send_message(chat_id = update.effective_chat.id, text=text)

def unknown(update: Update, context: CallbackContext) -> None:
    '''
    Unknown/wrong command
    Неизвестная/ошибочная команда
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    context.bot.send_message(chat_id=update.effective_chat.id, text=_('Неизвестная команда.'))

def begin() -> Updater:
    '''
    Start chat-bot
    Запуск чат-бота
    '''
    if len(argv) > 1:
        logs.setup(argv[1])
    else:
        logs.setup()

    try:
        with Path('secret').resolve().open(encoding='UTF-8') as file:
            token = file.readline().strip()
        if token is None or token.strip() == '':
            raise IOError()
    except IOError:
        logs.message('No token file')
        exit(1)

    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)
    contact_handler = MessageHandler(Filters.contact, contact)
    dispatcher.add_handler(contact_handler)
    view_replacements_handler = MessageHandler(Filters.text &
                                               Filters.regex('(?i)' + VIEW_REPLACEMENTS),
                                               view_replacements)
    dispatcher.add_handler(view_replacements_handler)
    upload_replacements_handler = MessageHandler(Filters.text &
                                                 Filters.regex('(?i)' + UPLOAD_REPLACEMENTS_FILE),
                                                 upload_replacements)
    dispatcher.add_handler(upload_replacements_handler)
    document_hanlder = MessageHandler(Filters.document, document)
    dispatcher.add_handler(document_hanlder)
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    updater.start_polling()

    return updater

if __name__ == '__main__':
    SELF_PATH = Path(__file__).resolve()
    UPDATER = begin()
