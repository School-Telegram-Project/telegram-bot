'''
Main module
Основной модуль
'''

import gettext
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from sys import argv, exit

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.error import Forbidden as Telegram_Forbidden
# from telegram.ext import (Application, ContextTypes, CommandHandler,
#                           CallbackQueryHandler, MessageHandler, PicklePersistence)
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, PicklePersistence)

import files
import logs
from constants.main import *
from utils import add_value, value_in_dict

application = None
persistence = None
bot_running = False
main_handlers = None
permanent_handlers = None

def get_translator(lang: str = 'ru'):
    '''
    Find translation for user
    Найти перевод для пользователя
    '''
    trans = gettext.translation('base', localedir=SELF_FOLDER / 'locales', languages=[lang])
    return trans.gettext


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
#         text = f'Error happened when trying to add new user {data[0]}'
#     logs.message(text, level=1)
#     return result

def user_keyboard(user_data):
    '''
    Create keyboard based on user data (what user can do)
    Создать клавиатуру на основе данных пользователя (того, что он может сделать)
    '''
    _keyboard = []
    if bot_running and value_in_dict('replacer', user_data, 1):
        _keyboard.append([VIEW_REPLACEMENTS])
    if bot_running and value_in_dict('dispatcher', user_data, 1):
        # kb.append(['Добавить замены вручную', 'Загрузить файл замен'])
        _keyboard.append([UPLOAD_REPLACEMENTS_FILE])
    # if bot_running and value_in_dict('scheduler', user_data, 1):
    #     kb.append(['Обновить расписание'])
    if value_in_dict('admin', user_data, 1):
        _keyboard.extend([
            [DISABLE_BOT if bot_running else ENABLE_BOT]
            # [DOWNLOAD]
            # [ADD_USER, DELETE_USER]
        ])
    return _keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, reset_user=False) -> None:
    '''
    Start command
    Команда старта
    '''
    _ = get_translator(update.effective_user.language_code)
    if not reset_user:
        logs.message(f'User {update.effective_user.id} sended /start')
    if reset_user or not value_in_dict('users', context.bot_data, update.effective_user.id):
        if 'users' not in context.bot_data:
            context.bot_data['users'] = set()
        logs.message(f'User {update.effective_chat.id} is not active user')
        user_data = files.find_user(update.effective_chat.id)
        if user_data is not None:
            logs.message(f'User {update.effective_chat.id} was found by ID')
            context.bot_data['users'].add(update.effective_chat.id)
            for datatype, value in user_data:
                context.user_data[datatype] = value
        else:
            keyboard = [ [KeyboardButton('Отправить номер', request_contact=True)] ]
            reply_markup = ReplyKeyboardMarkup(keyboard,
                resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                text=_(
                    '<b>Здравствуйте!</b>\n'
                    'Я школьный чат-бот, созданный для отправки информации, '
                    'которая касается только Вас. Вы можете узнать о своих заменах'
                    'с моей помощью. Но перед работой мне нужно получить Ваш '
                    'номер, чтобы занести его в базу данных, пожалуйста, '
                    'подтвердите это действие, нажав на кнопку <i>Отправить номер</i> ниже.'
                ),
                parse_mode=HTML, reply_markup=reply_markup
            )
            return
    context.user_data['state'] = (0, 0)
    await persistence.flush()
    reply_markup = ReplyKeyboardMarkup(user_keyboard(context.user_data), resize_keyboard=True)
    text = _('Выберите действие с помощью кнопок...')
    await update.message.reply_text(text=text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Help menu
    Меню помощи
    '''
    _ = get_translator(update.effective_user.language_code)
    text = _('Используйте команду <i>/start</i> для начала работы с ботом.\n'
             'Используйте клавиатуру команд для выбора действия и сделайте инструкциям.')
    await context.bot.send_message(text=text, chat_id=update.effective_chat.id, parse_mode=HTML)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Reset user's status
    Сбрасывает статус пользователя
    '''
    _ = get_translator(update.effective_user.language_code)
    if not value_in_dict('users', context.bot_data, update.effective_user.id):
        return
    logs.message(f'User {update.effective_user.id} sended /reset')
    context.bot_data['users'].remove(update.effective_user.id)
    context.user_data.clear()
    await start(update, context, reset_user=True)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Contact message
    Сообщение с контактом
    '''
    _ = get_translator(update.effective_user.language_code)
    _contact = update.effective_message.contact
    if update.effective_user.id != _contact.user_id:
        await context.bot.send_message(text=_('Пожалуйста, отправьте <b>свой</b> контакт.'),
                                 chat_id=update.effective_chat.id,
                                 parse_mode=HTML)
        return
    user_data = files.find_user(_contact.user_id, _contact.phone_number)
    if user_data is None:
        logs.message(f'User {update.effective_user.id} was not found')
        text = _('Вы отсутствуете среди списка пользователей.\n'
                 'Пожалуйста, обратитесь к администрации.')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        return
    logs.message(f'User {update.effective_user.id} was found by phone number')
    add_value('users', update.effective_user.id, context.bot_data)
    if not value_in_dict('users', context.bot_data):
        context.bot_data['users'] = {update.effective_chat.id}
    else:
        context.bot_data['users'].add(update.effective_chat.id)
    for datatype, value in user_data:
        context.user_data[datatype] = value
    context.user_data['state'] = (0, 0)
    await persistence.flush()
    await context.bot.send_message(
        text=_('Пользовательские данные сохранены.'),
        chat_id=update.effective_chat.id, reply_markup=user_keyboard(context.user_data)
    )

async def view_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Look for replacements that involve user
    Поиск замен для пользователя
    '''
    if not value_in_dict('replacer', context.user_data, 1):
        return
    _ = get_translator(update.effective_user.language_code)
    logs.message(f'User {update.effective_user.id} has requested their replacements')
    replacements = files.read_replacements(context.user_data['name'])
    if replacements is None:
        text = _('Не удалось прочитать базу данных.')
        await context.bot.send_message(text=text, chat_id = update.effective_chat.id)
        return
    if not replacements:
        text = _('Замены не найдены.')
        await context.bot.send_message(text=text, chat_id=update.effective_chat.id)
        return

    replacements_texts = {}
    for i, repl in enumerate(replacements):
        # teacher, class, lesson, lesson_date, room, replaced, additional
        text = _(
            'Замена у {class_name} класса на {lesson} уроке'
            '{room}'            # в {room} кабинете
            # '{teacher}'         # у {teacher} учителя
            '{additional}'      # (доп. информация)
            ).format(
                class_name = repl[1],
                lesson = repl[2],
                room = ' ' + _('в кабинете {0}').format(repl[4]) if repl[4] is not None else '',
                # teacher = repl[5],
                additional = f'\n{repl[6]}' if repl[6] is not None else ''
            )
        date = datetime(*(int(s) for s in repl[3].split('.')))
        if date not in replacements_texts:
            replacements_texts[date] = [text]
        else:
            replacements_texts[date].append(text)

    for i, date in enumerate(replacements_texts):
        msg = ''
        texts = replacements_texts[date]
        msg += _('Замены на {d}.{m}.{y}:').format(
            d = date.day,
            m = date.month,
            y = date.year
        )
        msg += HORIZONTAL_BAR
        texts_end = len(texts) - 1
        for i, t in enumerate(texts):
            if len(msg) + len(t) + (2 if i < texts_end else 0) > MAX_TEXT_LENGTH:
                await context.bot.send_message(
                    text=msg, chat_id=update.effective_chat.id, parse_mode=HTML
                )
                msg = ''
            else:
                msg += t + ('\n\n' if i < texts_end else '')
        msg += HORIZONTAL_BAR
        await context.bot.send_message(text=msg, chat_id=update.effective_chat.id, parse_mode=HTML)

async def upload_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Upload replacements table
    Загрузить таблицу замен
    '''
    if not value_in_dict('dispatcher', context.user_data, value=1):
        return
    _ = get_translator(update.effective_user.language_code)
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
    context.user_data['state'] = (1, 0)

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Downloading files
    Получение файла
    '''
    if not value_in_dict('dispatcher', context.user_data, 1):
        return
    if context.user_data['state'][0] in [1, 2]:
        _ = get_translator(update.effective_user.language_code)
        _document = update.message.document
        logs.message(f'User {update.effective_user.id} has uploaded file "{_document.file_name}"')
        file_type = _document.file_name.split('.')[-1]
        time = datetime.now().isoformat(sep='.', timespec='seconds').replace(':', '-')
        doc_file = await context.bot.get_file(_document.file_id)
        file_path = SELF_FOLDER / 'downloads' / f'{time}.{file_type}'
        await doc_file.download_to_drive(file_path)
        if context.user_data['state'][0] == 1:
            await context.bot.send_message(
                text=_('Идёт обработка файла, пожалуйста, подождите...'),
                chat_id=update.effective_chat.id
            )
            replacements = files.replacements_from_file(file_path)
            to_save = len(replacements)
            saved = files.save_replacement(replacements)
            text = _('! <b>У вас есть новые замены</b> !')
            for user_id in context.bot_data['users']:
                user_data = application.user_data[user_id]
                if user_data['name'] in replacements and user_id != update.effective_user.id:
                    reply_markup = ReplyKeyboardMarkup(user_keyboard(user_data),
                                                       resize_keyboard=True)
                    try:
                        await context.bot.send_message(
                            chat_id=user_id, text=text, parse_mode=HTML, reply_markup=reply_markup
                        )
                    except Telegram_Forbidden:
                        context.bot_data['users'].remove(user_id)
                        del application.user_data[user_id]
            if saved < to_save:
                text = _('Возникла проблема с сохранением данных, '
                        f'загружено {saved} из {to_save} замен.')
            else:
                text = _('Данные сохранены.')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
        # elif user.state == 2:
        # TODO: расписание
        context.user_data['state'] = (0, 0)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Handles InlineKeyboard presses
    Обрабатывает нажатия InlineKeyboard
    '''
    if not value_in_dict('users', context.bot_data, update.effective_user.id):
        return
    query = update.callback_query
    data = query.data
    await query.answer()
    if not isinstance(data, str) or len(data) < 2:
        return
    _ = get_translator(update.effective_user.language_code)
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
        context.user_data['state'] = (context.user_data['state'][0], int(data[1]))

async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Enable bot for non-admin users by adding main handlers
    Включить бот для не-администраторов, добавив основные обработчики команд
    '''
    if not value_in_dict('admin', context.user_data, 1):
        return
    _ = get_translator(update.effective_user.language_code)
    global bot_running
    if bot_running:
        reply_markup = ReplyKeyboardMarkup(user_keyboard(context.user_data), resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=_('Бот уже запущен.'),
                                       reply_markup=reply_markup)
        return
    application.add_handlers(main_handlers)
    bot_running = True
    reply_markup = ReplyKeyboardMarkup(user_keyboard(context.user_data), resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=_('Бот успешно запущен.'),
                                   reply_markup=reply_markup)
    logs.message('Bot has been enabled', 1)

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Disable bot for non-admin users by removing main handlers
    Выключить бот для не-администраторов, убрав основные обработчики команд
    '''
    if not value_in_dict('admin', context.user_data, 1):
        return
    _ = get_translator(update.effective_user.language_code)
    global bot_running
    if not bot_running:
        reply_markup = ReplyKeyboardMarkup(user_keyboard(context.user_data), resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=_('Бот уже выключен.'), reply_markup = reply_markup)
        return
    for handler in main_handlers[0]:
        application.remove_handler(handler)
    bot_running = False
    reply_markup = ReplyKeyboardMarkup(user_keyboard(context.user_data), resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=_('Бот успешно выключен.'), reply_markup = reply_markup)
    logs.message('Bot has been temporary disabled for users', 1)

async def post_init(app: Application) -> None:
    '''
    Restore pre-reload state
    Восстановить состояние до перезапуска
    '''
    if app.bot_data is not None and 'users' in app.bot_data:
        for user_id in app.bot_data['users']:
            try:
                await app.bot.get_chat(user_id)
            except Telegram_Forbidden:
                app.bot_data['users'].remove(user_id)

if __name__ == '__main__':
    users = []
    # Handlers for non-admin users
    main_handlers = {
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
    permanent_handlers = {
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

    persistence = PicklePersistence(filepath='bot_data')
    application = (Application.builder().token(token).
        persistence(persistence).post_init(post_init).build())
    application.add_handlers(main_handlers | permanent_handlers)
    bot_running = True
    application.run_polling()
