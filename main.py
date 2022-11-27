'''
Main module
Основной модуль
'''

from datetime import datetime
import re
# TODO: Локализация
# import gettext
from pathlib import Path
from sys import argv, exit

from telegram import (KeyboardButton, ReplyKeyboardMarkup,
                      InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (Application, ContextTypes, CommandHandler,
                          CallbackQueryHandler, MessageHandler)
from telegram.ext.filters import (TEXT as TEXT_FILTER, Regex as Regex_filter,
                                  CONTACT as CONTACT_FILTER,
                                  Document as Document_filter, COMMAND as COMMAND_FILTER)
from telegram.constants import ParseMode

import files
import logs
from user import (User, VIEW_REPLACEMENTS, UPLOAD_REPLACEMENTS_FILE,
                  ENABLE_BOT, DISABLE_BOT, DOWNLOAD)

SELF_FOLDER = None
MAIN_HANDLERS = None
PERMANENT_HANDLERS = None
DOCUMENT_FILTER = Document_filter.FileExtension('doc') | Document_filter.FileExtension('docx')
VIEW_REPLACEMENTS_FILTER = TEXT_FILTER & Regex_filter('(?i)' + VIEW_REPLACEMENTS)
UPLOAD_REPLACEMENTS_FILTER = TEXT_FILTER & Regex_filter('(?i)' + UPLOAD_REPLACEMENTS_FILE)
ENABLE_BOT_FILTER = TEXT_FILTER & Regex_filter('(?i)' + ENABLE_BOT)
DISABLE_BOT_FILTER = TEXT_FILTER & Regex_filter('(?i)' + DISABLE_BOT)
# DOWNLOAD_FILTER = TEXT_FILTER & Regex_filter('(?i)' + DOWNLOAD)
# ADD_USER_FILTER = TEXT_FILTER & Regex_filter('(?i)' + ADD_USER)
# DELETE_USER_FILTER = TEXT_FILTER & Regex_filter('(?i)' + DELETE_USER)
HTML = ParseMode.HTML

application = None
users = None
bot_running = False

# def get_translator(lang: str = 'ru'):
#     '''
#     Find translation for user
#     Найти перевод для пользователя
#     '''
#     trans = gettext.translation('', localedir=SELF_PATH/'locale', languages=(lang,))
#     return trans.gettext

def auth(user_id) -> User:
    '''
    Find user or return None
    Найти пользователя или вернуть None
    '''
    if user_id in users.keys():
        result = users[user_id]
    else:
        result = None
    return result

# def new_user(data: tuple) -> int:
#     '''
#     Add new user
#     Returns success (1 = added, 0 = already in DB, -1 = error)
#     Добавить нового пользователя
#     Возвращает результат (1 = добавлен, 0 = уже в базе, -1 = ошибка)
#     '''
#     if len(data) < 7:
#         return -1
#     try:
#         user = User(data[1:])
#     except ValueError as error:
#         logs.message(f'Could not add new user {data[0]}: {error}')
#         return -1
#     result = files.add_user(data)
#     if result:
#         text = f'User {data[0]} was added to database'
#         users[user.id] = user
#     elif result == 0:
#         text = f'Tried to add user {data[0]} (id={data[1]}), who is already in database'
#     else:
#         text = f'Error happend when trying to add new user {data[0]}'
#     logs.message(text, level=1)
#     return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user = None) -> None:
    '''
    Start command
    Команда старта
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    logs.message(f'User {update.effective_user.id} sended /start')
    user = auth(update.effective_user.id)
    if user is None:
        logs.message(f'User {update.effective_chat.id} is not active user')
        user = files.find_user(update.effective_chat.id)
        if user is not None:
            logs.message(f'User {update.effective_chat.id} was found by ID')
            users[update.effective_user.id] = user
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
            await update.message.reply_text(text=text, parse_mode=HTML, reply_markup=reply_markup)
            return
    user.state = 0
    reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
    text = _('Выберите действие с помощью кнопок...')
    await update.message.reply_text(text=text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Help menu
    Меню помощи
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    text = _('Используйте команду <i>/start</i> для начала работы с ботом.\n'
             'Используйте клавиатуру команд для выбора действия и сделуйте инструкциям.')
    await context.bot.send_message(text=text, chat_id=update.effective_chat.id, parse_mode=HTML)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Reset user's status
    Сбрасывает статус пользователя
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    user = auth(update.effective_user.id)
    if user is None:
        return
    users.pop(update.effective_user.id)
    await start(update, context)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Contact message
    Сообщение с контактом
    '''
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    ct = update.effective_message.contact
    if update.effective_user.id != ct.user_id:
        await context.bot.send_message(text=_('Пожалуйста, отправьте <b>свой</b> контакт.'),
                                 chat_id=update.effective_chat.id,
                                 parse_mode=HTML)
        return
    user = files.find_user(ct.user_id, ct.phone_number)
    if user is None:
        logs.message(f'User {update.effective_user.id} was not found')
        text = _('Вы отсутствуете среди списка пользователей.\n'
                 'Пожалуйста, обратитесь к администрации.')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return
    logs.message(f'User {update.effective_user.id} was found by phone number')
    users[update.effective_user.id] = user
    await start(update, context, user)

async def view_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Look for replacements that involve user
    Поиск замен для пользователя
    '''
    user = auth(update.effective_user.id)
    if user is None:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    logs.message(f'User {update.effective_user.id} has requested their replacements')
    replacements = files.read_replacements(user.name)
    if replacements is None:
        text = _('Не удалось прочитать базу данных.')
        await context.bot.send_message(chat_id = update.effective_chat.id, text=text)
        return
    if not replacements: # len(replacements) == 0
        text = _('Замены на сегодня не найдены.')
        await context.bot.send_message(text=text, chat_id=update.effective_chat.id)
        return

    text = _('<b>Замены на сегодня:</b>') + '\n\n'
    for repl in replacements:
        text += _('Замена у {0} класса на {1} уроке').format(repl[0], repl[1])
        if repl[2] != 'NULL':
            text += _(' в {0} кабиенете').format(repl[2])
        text += '\n<s>---------</s>\n'
    text = text[:-18]
    await context.bot.send_message(text=text, chat_id=update.effective_chat.id, parse_mode=HTML)

async def upload_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE, user = None) -> None:
    '''
    Upload replacements table
    Загрузить таблицу замен
    '''
    user = auth(update.effective_user.id)
    if user is None:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    # keyboard = [ [ InlineKeyboardButton(_('Обновить существующие замены'), callback_data='01')] ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    # text = (
    #     _('Пожалуйста, загрузите таблицу замен.') + '\n'
    #     _('Режим: ')
    #     )
    # text += _('Добавить новые замены')
    text = _('Пожалуйста, загрузите таблицу замен.')
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    user.state = (1, 0)

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Downloading files
    Получение файла
    '''
    user = auth(update.effective_user.id)
    if user is None:
        return
    if user.state[0] in [1, 2]:
        # _ = get_translator(update.effective_user.language_code)
        _ = str
        document = update.message.document
        logs.message(f'User {update.effective_user.id} has uploaded file {document.file_name}')
        file_type = document.file_name.split('.')[-1]
        time = datetime.now().time().isoformat('seconds')
        filename = f'/mnt/data/Programming/telegram-bot/downloads/{time}.{file_type}'
        logs.message(f'Download name: {filename}')
        doc_file = await context.bot.get_file(document.file_id)
        file_path = SELF_FOLDER / 'downloads' / f'{time}.{file_type}'
        await doc_file.download_to_drive(file_path)
        if user.state[0] == 1:
            teachers, data = files.replacements_from_file(file_path)
            unsaved = files.save_replacement(data)
            text = _('! <b>У вас есть новые замены</b> !')
            reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
            for __, usr_id in enumerate(users):
                usr = users[usr_id]
                if usr.name in teachers and usr_id != update.effective_user.id:
                    await context.bot.send_message(chat_id=usr_id, text=text,
                                                   parse_mode=HTML, reply_markup=reply_markup)
            text = _('Данные сохранены.')
            #     if result:
            #         text = _('Возникла ошибка, не удалось загрузить часть данных.')
            # # elif user.state == 2:
            # #    logs.message(f'File name: )
            #     text += f'\n{result}'
            #     await context.bot.send_message(chat_id = update.effective_chat.id, text=text)
        user.state = 0

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Handles InlineKeyboard presses
    Обрабатывает нажатия InlineKeyboard
    '''
    user = auth(update.effective_user.id)
    query = update.callback_query
    data = query.data
    await query.answer()
    if not isinstance(data, str) or len(data) < 2:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    text = query.message.text
    if data[0] == '0':
        text = _(
        'Пожалуйста, загрузите таблицу замен.' + '\n'
        'Режим: '
        )
        if data[1] == '0':
            text += _('Добавить новые замены')
            keyboard = [[InlineKeyboardButton(_('Обновить существующие замены'), callback_data='01')]]
        else:
            text += _('Обновить существующие замены')
            keyboard = [[InlineKeyboardButton(_('Добавить новые замены'), callback_data='00')]]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        user.state = (user.state[0], int(data[1]))

async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Enable bot for non-admin users by adding main handlers
    Включить бота для не-администаторов, добавив основные обработчики комманд
    '''
    user = auth(update.effective_user.id)
    if user is None or not user.admin:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    global bot_running
    if bot_running:
        reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=_('Бот уже запущен.'),
                                       reply_markup=reply_markup)
        return
    application.add_handlers(MAIN_HANDLERS)
    bot_running = True
    reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=_('Бот успешно запущен.'),
                                   reply_markup=reply_markup)

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Disable bot for non-admin users by removing main handlers
    Выключить бота для не-адмнинстраторов, убрав основные обработчики комманд
    '''
    user = auth(update.effective_user.id)
    if user is None or not user.admin:
        return
    # _ = get_translator(update.effective_user.language_code)
    _ = str
    global bot_running
    if not bot_running:
        reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=_('Бот уже выключен.'), reply_markup = reply_markup)
        return
    for handler in MAIN_HANDLERS[0]:
        application.remove_handler(handler)
    bot_running = False
    reply_markup = ReplyKeyboardMarkup(user.keyboard(bot_running), resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=_('Бот успешно выключен.'), reply_markup = reply_markup)

if __name__ == '__main__':
    users = {}
    # Handlers for non-admin users
    MAIN_HANDLERS = {
        0: [
        MessageHandler(CONTACT_FILTER, contact),
        MessageHandler(VIEW_REPLACEMENTS_FILTER, view_replacements),
        MessageHandler(UPLOAD_REPLACEMENTS_FILTER, upload_replacements),
        # CallbackQueryHandler(button),
        MessageHandler(DOCUMENT_FILTER, document)
        ]
    }
    # Handlers for admin users and other handlers that should always be active
    # (like start handler)
    PERMANENT_HANDLERS = {
        -1: [
            CommandHandler('start', start), CommandHandler('help', help_command),
            CommandHandler('reset', reset),
            MessageHandler(ENABLE_BOT_FILTER, enable_bot),
            MessageHandler(DISABLE_BOT_FILTER, disable_bot),
        ]
    }
    SELF_FOLDER = Path(__file__).resolve().cwd()

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
    application = Application.builder().token(token).build()
    application.add_handlers(MAIN_HANDLERS | PERMANENT_HANDLERS)
    bot_running = True
    application.run_polling()
