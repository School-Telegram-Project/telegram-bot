'''
Main module
Основной модуль
'''

# pylint: disable=locally-disabled, undefined-variable, redefined-builtin, wildcard-import, global-statement, invalid-name

import gettext
import re
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from sys import argv, exit
from warnings import filterwarnings

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.error import Forbidden as Telegram_Forbidden
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          PicklePersistence)
from telegram.ext.filters import COMMAND as COMMAND_FILTER
from telegram.ext.filters import CONTACT as CONTACT_FILTER
from telegram.warnings import PTBUserWarning

import files
import logs
from constants.main import *
from utils import add_value, value_in_dict

application = None
persistence = None
bot_running = False
logger = None
# Language-dependent constants
# Зависящие от языка константы
commands = None
st_names = None

def user_keyboard(user_data) -> ReplyKeyboardMarkup:
    '''
    Create keyboard based on user permissions

    Создать клавиатуру на основе прав пользователя
    '''
    _keyboard = []
    if bot_running and value_in_dict('replacer', user_data, 1):
        _keyboard.append([commands.VIEW_REPLACEMENTS])
    if bot_running and value_in_dict('dispatcher', user_data, 1):
        # kb.append(['Добавить замены вручную', 'Загрузить файл замен'])
        _keyboard.append([commands.UPLOAD_REPLACEMENTS_FILE])
    # if bot_running and value_in_dict('scheduler', user_data, 1):
    #     kb.append(['Обновить расписание'])
    if value_in_dict('admin', user_data, 1):
        _keyboard.extend([
            [commands.DISABLE_BOT if bot_running else commands.ENABLE_BOT],
            # [DOWNLOAD]
            [commands.ADD_USER, commands.DELETE_USER]
        ])
    _keyboard.append([commands.SETTINGS])
    return ReplyKeyboardMarkup(_keyboard, resize_keyboard=True)

# Everyone's commands
# Общедоступные команды

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, reset_user=False) -> None:
    '''
    Start command

    Команда старта
    '''
    if not reset_user:
        logger.info('User %s sended /start', update.effective_user.id)
    if reset_user or not value_in_dict('users', context.bot_data, update.effective_user.id):
        if 'users' not in context.bot_data:
            context.bot_data['users'] = set()
        logger.info('User %s is not active user', update.effective_chat.id)
        user_data = files.find_user(update.effective_chat.id)
        if user_data is not None:
            logger.info('User %s was found by ID', update.effective_chat.id)
            context.bot_data['users'].add(update.effective_chat.id)
            for datatype, value in user_data:
                context.user_data[datatype] = value
        else:
            reply_markup = ReplyKeyboardMarkup(
                [ [ KeyboardButton('Отправить номер', request_contact=True) ] ],
                resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(
                text=_(
                    '<b>Здравствуйте!</b>\n'
                    'Я школьный чат-бот, созданный для отправки информации, '
                    'которая касается только Вас. Вы можете узнать о своих заменах '
                    'с моей помощью. Но перед работой мне нужно получить Ваш '
                    'номер, чтобы занести его в базу данных, пожалуйста, '
                    'подтвердите это действие, нажав на кнопку <i>Отправить номер</i> ниже.'
                ),
                parse_mode=HTML, reply_markup=reply_markup
            )
            return
    context.user_data['state'] = (0, 0)
    await persistence.flush()
    text = _('Выберите действие с помощью кнопок...')
    await update.message.reply_text(text=text, reply_markup=user_keyboard(context.user_data))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Help menu

    Меню помощи
    '''
    await update.message.reply_text(
        text=(_('/start - Начать работу с ботом') + '\n' +
              _('/reset - Перезайти') + '\n' +
              _('/help - Меню помощи') + '\n' +
              _('/cancel - Отмена (для действий, поддерживающих эту функцию)') + '\n' +
              _('Используйте клавиатуру команд для выбора действий.') + '\n' +
              _('Если клавиатура не появляется, используйте /start или /reset')
             )
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Reset user's status

    Сбрасывает статус пользователя
    '''
    if not value_in_dict('users', context.bot_data, update.effective_user.id):
        return
    logger.info('User %s sended /reset', update.effective_user.id)
    context.bot_data['users'].remove(update.effective_user.id)
    context.user_data.clear()
    await start(update, context, reset_user=True)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Contact message

    Сообщение с контактом
    '''
    _contact = update.effective_message.contact
    if update.effective_user.id != _contact.user_id:
        await update.message.reply_text(
            text=_('Пожалуйста, отправьте <b>свой</b> контакт.'), parse_mode=HTML
        )
        return
    user_data = files.find_user(_contact.user_id, _contact.phone_number)
    if user_data is None:
        logger.info('User %s was not found', update.effective_user.id)
        await update.message.reply_text(
            text=_('Вы отсутствуете среди списка пользователей.\n'
                   'Пожалуйста, обратитесь к администрации.')
        )
        return
    logger.info('User %s was found by phone number', update.effective_user.id)
    add_value('users', update.effective_user.id, context.bot_data)
    if not value_in_dict('users', context.bot_data):
        context.bot_data['users'] = {update.effective_chat.id}
    else:
        context.bot_data['users'].add(update.effective_chat.id)
    for datatype, value in user_data:
        context.user_data[datatype] = value
    context.user_data['state'] = (0, 0)
    context.user_data['settings'] = {'file_action': 0, 'notif': 2}
    await persistence.flush()
    await update.message.reply_text(
        text=_('Пользовательские данные сохранены.'), reply_markup=user_keyboard(context.user_data)
    )

# async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Settings menu

#     Меню настроек
#     '''
#     _settings = user_data['settings']
#     _keyboard = []
#     text = _('Настройки:') + '\n\t'
#     if value_in_dict('replacer', user_data, 1):
#         text += (st_names.NOTIF_NAME + ': '
#                  + st_names.NOTIF_OPTIONS[_settings.send_new_replacements]
#                  + '\n\t')
#         _keyboard.append([commands.ST_NOTIFY])
#     if value_in_dict('dispatcher', user_data, 1):
#         text += (st_names.FILE_ACTION_NAME + ': '
#                  + st_names.FILE_ACTION_OPTIONS[_settings.file_upload_action]
#                  + '\n\t')
#         _keyboard.append([commands.ST_FILE])
#     text = text.strip('\n\t')
#     if 'Change_settings' not in context.user_data:
#         _keyboard.append([commands.SAVE])
#     _keyboard.append([commands.CANCEL])

#     await update.message.reply_text(
#         text=text,
#         reply_markup=ReplyKeyboardMarkup(_keyboard, resize_keyboard=True)
#     )
#     return 0

# async def st_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Change default file action

#     Изменить действие по умолчанию при загрузке файла
#     '''
#     await update.message.reply_text(
#         text=st_names.FILE_ACTION_NAME + ':',
#         reply_markup=ReplyKeyboardMarkup(
#             [ st_names.FILE_ACTION_OPTIONS,
#               commands.CANCEL ],
#             resize_keyboard=True
#         )
#     )
#     return 1

# async def st_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Change notification for new replacements

#     Изменить тип уведомления
#     '''
#     await update.message.reply_text(
#         text=st_names.NOTIF_NAME + ':',
#         reply_markup=ReplyKeyboardMarkup(
#             [ st_names.NOTIF_OPTIONS,
#               commands.CANCEL ],
#             resize_keyboard=True
#         )
#     )
#     return 1

# async def st_change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Change settings

#     Изменить настройки
#     '''
#     setting = update.message.text.strip().capitalize()
#     if 'Change_settings' not in context.user_data:
#         context.user_data['Change_settings'] = {}
#     if setting in st_names.FILE_ACTION_OPTIONS:
#         context.user_data['Change_settings']['file'] = st_names.FILE_ACTION_OPTIONS.index(setting)
#     elif setting in st_names.NOTIF_OPTIONS:
#         context.user_data['Change_settings']['notif'] = st_names.NOTIF_OPTIONS.index(setting)
#     return setting_command(update, context)

# async def st_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Save changes to settings

#     Сохранить изменения настроек
#     '''
#     if 'Change_settings' not in context.user_data:
#         await update.message.reply_text(
#             text=_('Настройки не были изменены'),
#             reply_markup=user_keyboard(context.user_data)
#         )
#     else:
#         if 'file' in context.user_data['Change_settings']:
#             context.user_data['settings']['file'] = context.user_data['Change_settings']['file']
#         if 'notif' in context.user_data['Change_settings']:
#             context.user_data['settings']['notif'] = context.user_data['Change_settings']['notif']
#         await update.message.reply_text(
#             text=_('Настройки сохранены'),
#             reply_markup=user_keyboard(context.user_data)
#         )
#     return ConversationHandler.END

# Teachers' commands
# Команды учителей

async def view_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Look for replacements that involve user

    Поиск замен для пользователя
    '''
    if not value_in_dict('replacer', context.user_data, 1):
        return
    if not bot_running:
        await update.message.reply_text(text=_('Бот был временно выключен администрацией.'))
        return
    logger.info('User %s has requested their replacements', update.effective_user.id)
    replacements = files.read_replacements(context.user_data['name'])
    if replacements is None:
        await update.message.reply_text(text=_('Не удалось прочитать базу данных.'))
        return
    if not replacements:
        await update.message.reply_text(text=_('Замены не найдены.'))
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
                await update.message.reply_text(text=msg, parse_mode=HTML)
                msg = ''
            else:
                msg += t + ('\n\n' if i < texts_end else '')
        msg += HORIZONTAL_BAR
        await update.message.reply_text(text=msg, parse_mode=HTML)

# Dispatchers' commands
# Команды диспетчеров

async def upload_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Upload replacements table

    Загрузить таблицу замен
    '''
    if not value_in_dict('dispatcher', context.user_data, value=1):
        return ConversationHandler.END
    if not bot_running:
        await update.message.reply_text(text=_('Бот был временно выключен администрацией.'))
        return ConversationHandler.END
    # keyboard = [ [ InlineKeyboardButton(_('Обновить существующие замены'), callback_data='01')] ]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    # text = (
    #     _('Пожалуйста, загрузите таблицу замен.') + '\n'
    #     _('Режим: ')
    #     )
    # text += _('Добавить новые замены')
    # await update.message.reply_text(text=text, reply_markup=reply_markup)
    await update.message.reply_text(text=_('Пожалуйста, загрузите таблицу замен.'))
    context.user_data['state'] = (1, 0)
    return 0

# async def replacements_edit_modes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     '''
#     Changes mode for editing replacements

#     Меняет режим изменения замен
#     '''
#     if not value_in_dict('users', context.bot_data, update.effective_user.id):
#         return
#     query = update.callback_query
#     mode = query.data
#     await query.answer()
#     text = (_('Пожалуйста, загрузите таблицу замен.')
#           + _('Режим: '))
#     if mode == 0:
#         text += _('Добавить новые замены')
#         keyboard = [[InlineKeyboardButton(_('Обновить существующие замены'), callback_data=1)]]
#     else:
#         text += _('Обновить существующие замены')
#         keyboard = [[InlineKeyboardButton(_('Добавить новые замены'), callback_data=0)]]
#     await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
#     context.user_data['state'] = (1, int(mode[1]))
#     return 0

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Downloading files

    Получение файла
    '''
    if not value_in_dict('dispatcher', context.user_data, 1):
        return ConversationHandler.END
    if not bot_running:
        await update.message.reply_text(text=_('Бот был временно выключен администрацией.'))
        return ConversationHandler.END
    if context.user_data['state'][0] in [1, 2]:
        _document = update.message.document
        logger.info('User %s has uploaded file "%s"', update.effective_user.id, _document.file_name)
        file_type = _document.file_name.split('.')[-1]
        time = datetime.now().isoformat(sep='.', timespec='seconds').replace(':', '-')
        doc_file = await context.bot.get_file(_document.file_id)
        file_path = SELF_FOLDER / 'downloads' / f'{time}.{file_type}'
        await doc_file.download_to_drive(file_path)
        if context.user_data['state'][1] == 0:
            await update.message.reply_text(
                text=_('Идёт обработка файла, пожалуйста, подождите...')
            )
            replacements = files.replacements_from_file(file_path)
            to_save = len(replacements)
            saved = files.save_replacement(replacements)
            text = _('! <b>У вас есть новые замены</b> !')
            for user_id in context.bot_data['users']:
                user_data = application.user_data[user_id]
                if user_data['name'] in replacements and user_id != update.effective_user.id:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id, text=text, parse_mode=HTML,
                            reply_markup=user_keyboard(user_data)
                        )
                    except Telegram_Forbidden:
                        context.bot_data['users'].remove(user_id)
                        del application.user_data[user_id]
            if saved < to_save:
                await update.message.reply_text(
                    text=_('Возникла проблема с сохранением данных, '
                          f'загружено {saved} из {to_save} замен.')
                )
            else:
                await update.message.reply_text(text=_('Данные сохранены.'))
        # elif user.state == 2:
        # TODO: расписание
        context.user_data['state'] = (0, 0)
    return ConversationHandler.END

# Admins' commands
# Команды администраторов

async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Enable bot for non-admin users

    Включить бот для не-администраторов
    '''
    if not value_in_dict('admin', context.user_data, 1):
        return
    global bot_running
    if bot_running:
        await update.message.reply_text(
            text=_('Бот уже запущен.'), reply_markup=user_keyboard(context.user_data)
        )
        return
    bot_running = True
    await update.message.reply_text(
        text=_('Бот успешно запущен.'),
        reply_markup=user_keyboard(context.user_data)
    )
    logger.warning('Bot has been enabled')

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Disable bot for non-admin users

    Выключить бот для не-администраторов
    '''
    if not value_in_dict('admin', context.user_data, 1):
        return
    global bot_running
    if not bot_running:
        await update.message.reply_text(
            text=_('Бот уже выключен.'), reply_markup = user_keyboard(context.user_data)
        )
        return
    bot_running = False
    await update.message.reply_text(
        text=_('Бот успешно выключен.'), reply_markup = user_keyboard(context.user_data)
    )
    logger.warning('Bot has been temporary disabled for users')

#   Add user conversation
#   Диалог для добавления пользователя

async def add_user_begin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    Begin conversation
    Начать диалог
    '''
    await update.message.reply_text(
        text=(_('Пожалуйста, введите ФИО пользователя в формате "Иванов А Б".') + '\n' +
              _('Для отмены введите "Отмена" или /cancel')),
        reply_markup=ReplyKeyboardRemove()
    )
    logger.info('Admin %s is adding new user', update.effective_user.id)
    return 0

async def au_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    (Part of "add user" conversation)
    Enter username

    (Часть диалога "добавить пользователя")
    Ввести имя пользователя
    '''
    name = update.message.text.strip()
    logger.info('%s: new user, "%s"', update.effective_user.id, name)
    context.user_data['Add_user'] = {
        'name': name, 'replacer': True, 'dispatcher': False, 'admin': False
    }
    msg = await update.message.reply_text(
        text=_('Сохранено имя пользователя: {0}.').format(name) + '\n' +
             _('Пожалуйста выберите права для пользователя. (Кнопки меняют состояние)') + '\n' +
             _('Права на данный момент: заменяющий - да, диспетчер - нет, администратор - нет.'))
    context.user_data['Add_user']['msg_id'] = msg.id
    await msg.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [ InlineKeyboardButton(commands.AU_EDIT_NAME, callback_data='AU_edit_username') ],
            [
                InlineKeyboardButton(commands.AU_CHANGE_USER_REPLACEMENTS,
                                     callback_data='AU_replacer'),
                InlineKeyboardButton(commands.AU_CHANGE_USER_DISPATCHER,
                                     callback_data='AU_dispatcher'),
                InlineKeyboardButton(commands.AU_CHANGE_USER_ADMIN,
                                     callback_data='AU_admin')
            ]
        ])
    )
    await update.message.reply_text(text=_('Укажите номер телефона (+7 123 456 78 90):'))
    return 1

async def au_name_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    (Part of "add user" conversation)
    Incorrect username was entered

    (Часть диалога "добавить пользователя")
    Некорректное имя пользователя было введено
    '''
    await update.message.reply_text(
        text=_('Неправильное имя пользователя, пожалуйста, введите имя снова.')
    )
    return 0

async def au_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    (Part of "add user" conversation)
    Edit username or permissions

    (Часть диалога "добавить пользователя")
    Изменить имя или права пользователя
    '''
    query = update.callback_query
    data = query.data[3:]
    await query.answer()
    if data == 'edit_username':
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            text=_('Пожалуйста, введите имя пользователя:'),
            chat_id=update.effective_chat.id
        )
        return 0
    context.user_data['Add_user'][data] = not context.user_data['Add_user'][data]
    await query.edit_message_text(
        (_('Сохранено имя пользователя: {n}.') + '\n'
       + _('Пожалуйста выберите права для пользователя. (Кнопки меняют состояние)') + '\n'
       + _('Права на данный момент: заменяющий - {r}, диспетчер - {d}, администратор - {a}.')
        ).format(
            n=context.user_data['Add_user']['name'],
            r=commands.TRANSLATE_BOOL(context.user_data['Add_user']['replacer']),
            d=commands.TRANSLATE_BOOL(context.user_data['Add_user']['dispatcher']),
            a=commands.TRANSLATE_BOOL(context.user_data['Add_user']['admin'])
        ),
    )
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [ InlineKeyboardButton(commands.AU_EDIT_NAME, callback_data='AU_edit_username') ],
            [
                InlineKeyboardButton(commands.AU_CHANGE_USER_REPLACEMENTS,
                                     callback_data='AU_replacer'),
                InlineKeyboardButton(commands.AU_CHANGE_USER_DISPATCHER,
                                     callback_data='AU_dispatcher'),
                InlineKeyboardButton(commands.AU_CHANGE_USER_ADMIN,
                                     callback_data='AU_admin')
            ]
        ])
    )
    return 1

async def au_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''
    (Part of "add user" conversation)
    Set phone number

    (Часть диалога "добавить пользователя")
    Указание номера телефона
    '''
    logger.info(
        '%s: user permissions: %s\n%s\n%s',
        update.effective_user.id,
        int(context.user_data["Add_user"]["replacer"]),
        int(context.user_data["Add_user"]["dispatcher"]),
        int(context.user_data["Add_user"]["admin"])
    )
    phone_num = int(re.sub(r'[\s\-]', '', context.match.group('num')))
    logger.info('%s: user phone is %s', update.effective_user.id, phone_num)
    context.user_data['Add_user']['phone'] = phone_num
    await context.bot.edit_message_reply_markup(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['Add_user']['msg_id'],
        reply_markup=None
    )
    await update.message.reply_text(
        text=_('Номер телефона: {0}').format(phone_num) + '\n' + _('Сохранить?'),
        reply_markup=ReplyKeyboardMarkup(
            [[ commands.TRUE, commands.FALSE ]],
            resize_keyboard=True
        )
    )
    return 2


async def au_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    (End of "add user" conversation)
    Save new user to database

    (Конец диалога "добавить пользователя")
    Сохранить нового пользователя в базу данных
    '''
    logger.info('%s: saving new user', update.effective_user.id)
    result = files.add_user(context.user_data['Add_user'])
    if result > 0:
        await update.message.reply_text(
            text=_('Данные сохранены'), reply_markup=user_keyboard(context.user_data)
        )
        return ConversationHandler.END

    if result == 0:
        await update.message.reply_text(
            text=_('Ошибка: Пользователь с таким номером телефона уже находится в базе данных'),
            reply_markup=user_keyboard(context.user_data)
        )
        del context.user_data['Add_user']
        return ConversationHandler.END

    await update.message.reply_text(
        text=_('Возникла ошибка при записи в базу данных. Повторить?'),
    )
    return 2

#   ---

#   Delete user conversation
#   Диалог для удаления пользователя

async def delete_user_begin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Begin conversation

    Начать диалог
    '''
    context.user_data['Delete_user'] = {'mode': True}
    await update.message.reply_text(
        text=_('Укажите номер телефона пользователя:') + '\n' +
             _('Для отмены введите "Отмена" или /cancel'),
        reply_markup=InlineKeyboardMarkup(
            [[ InlineKeyboardButton(commands.DU_NAME, callback_data='DU_name') ]]
        )
    )
    return 0

async def du_switch_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    (Part of "delete user" conversation)
    Change input mode for user selection

    (Часть диалога "удалить пользователя")
    Сменить режим ввода для выбора пользователя
    '''
    query = update.callback_query
    data = query.data[3:]
    await query.answer()
    if data == 'name':
        query.edit_message_text(
            text=(_('Укажите имя пользователя:') + '\n'
                + _('Для отмены введите "Отмена" или /cancel'))
        )
        context.user_data['Delete_user']['mode'] = False
        query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [[ InlineKeyboardButton(commands.DU_PHONE, callback_data='DU_phone') ]]
            )
        )
    else:
        query.edit_message_text(
            text=(_('Укажите номер телефона пользователя:') + '\n'
                + _('Для отмены введите "Отмена" или /cancel'))
        )
        context.user_data['Delete_user']['mode'] = True
        query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [[ InlineKeyboardButton(commands.DU_NAME, callback_data='DU_name') ]]
            )
        )
    return 0

async def du_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    (Part of "delete user" conversation)
    Confirm deletion of user

    (Часть диалога "удалить пользователя")
    Подтвердить удаление пользователя
    '''
    if context.user_data['Delete_user']['mode']:
        inputs = int(re.sub(r'[\s\-]', '', update.effective_message.text))
        user_data = files.find_user(phone_num=inputs)
    else:
        inputs = update.effective_message.text
        user_data = files.find_user(name=inputs)
    if user_data is None:
        await update.message.reply_text(
            text=_('Пользователь не был найден'),
            reply_markup=user_keyboard(context.user_data)
        )
        return ConversationHandler.END
    context.user_data['Delete_user']['phone'] = inputs
    context.user_data['Delete_user']['data'] = dict(user_data)
    await update.message.reply_text(
        text=_('Удалить пользователя?'),
        reply_markup=ReplyKeyboardMarkup(
            [[ commands.TRUE, commands.FALSE ]],
            resize_keyboard=True
        )
    )
    return 1

async def du_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    (End of "delete user" conversation)
    Delete user

    (Конец диалога "удалить пользователя")
    Удалить пользователя
    '''
    user_data = context.user_data['Delete_user']['data']
    if 'tg_id' in user_data and user_data['tg_id'] in application.user_data:
        del application.user_data[user_data[1]]
    if files.delete_user(context.user_data['Delete_user']['phone']):
        del context.user_data['Delete_user']
        await update.message.reply_text(
            text=_('Пользователь успешно удалён'),
            reply_markup=user_keyboard(context.user_data)
        )
        return ConversationHandler.END
    await update.message.reply_text(
        text=_('Возникла ошибка при записи в базу данных. Повторить?')
    )
    return 1

#   ---

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    End of conversation with no changes applied

    Конец диалога, не принимая изменений
    '''
    logger.info('%s: operation canceled', update.effective_user.id)
    await update.message.reply_text(
        text=_('Операция отменена'), reply_markup=user_keyboard(context.user_data)
    )
    if 'Add_user' in context.user_data:
        del context.user_data['Add_user']
    if 'Delete_user' in context.user_data:
        del context.user_data['Delete_user']
    if 'Change_settings' in context.user_data:
        del context.user_data['Change_settings']
    return ConversationHandler.END

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    '''
    Unknown command

    Неизвестная команда
    '''
    await update.message.reply_text(text=_('Неизвестная команда'))


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

def main() -> None:
    '''
    Main function

    Основная функция
    '''
    # Ignore CallbackQueryHandler 'per_message=False' warning
    filterwarnings(action='ignore', message=r'.*CallbackQueryHandler', category=PTBUserWarning)

    global SELF_FOLDER, application, persistence, bot_running, logger, commands, st_names

    SELF_FOLDER = Path.cwd()

    if len(argv) < 2:
        print('No settings file specified, using default location (.\\settings.ini)')
        settings_path = SELF_FOLDER / 'settings.ini'
    else:
        settings_path = argv[1]
    config = ConfigParser()
    config.read(SELF_FOLDER / 'settings.ini')
    if INI_SECTION not in config.sections():
        print(f'No {INI_SECTION} in settings file found, exiting...')
        exit(1)
    settings = config[INI_SECTION]
    if 'token' in settings:
        token = settings['token']
    else:
        print('No token entry in settings found, exiting...')
        exit(1)
    logs_path = settings.get('logs_folder')
    logs_debug = settings.get('logs_debug', fallback='False') == 'True'
    if logs_path == 'Console':
        logs.setup(debug=logs_debug)
    else:
        logs.setup(logs_path=logs_path, debug=logs_debug)
    logger = logs.logger('Main')
    locales = Path(settings.get('locales', 'locales')).resolve()
    language = settings.get('language', 'ru')
    save_interval = float(settings.get('save_interval', '10.0'))

    gettext.translation('base', localedir=locales, languages=[language]).install()
    commands = Commands(localedir=locales, language=language)
    files.setup_translation(localedir=locales, language=language)
#    st_names = SettingsNames(localedir=locales, language=language)

    persistence = PicklePersistence(filepath='bot_data', update_interval=save_interval)
    application = (Application.builder().token(token).
        persistence(persistence).post_init(post_init).build())
    application.add_handlers((
        MessageHandler(commands.ENABLE_BOT_FILTER, enable_bot),
        MessageHandler(commands.DISABLE_BOT_FILTER, disable_bot),

        CommandHandler('start', start),
        CommandHandler('help', help_command),
        CommandHandler('reset', reset),
        MessageHandler(CONTACT_FILTER, contact),
        # ConversationHandler(
        #     entry_points=[MessageHandler(commands.SETTINGS_FILTER, settings_command, block=False)],
        #     states={
        #         0: [
        #             MessageHandler(commands.ST_FILE_FILTER, st_file, block=False),
        #             MessageHandler(commands.ST_NOTIFY_FILTER, st_notify, block=False)
        #         ],
        #         1: [
        #             MessageHandler(commands.CANCEL_FILTER, settings_command, block=False),
        #             MessageHandler(TEXT_FILTER, st_change)
        #         ]
        #     },
        #     fallbacks=[
        #         MessageHandler(commands.SAVE, st_save),
        #         MessageHandler(TEXT_FILTER, cancel, block=False)
        #     ]),

        MessageHandler(commands.VIEW_REPLACEMENTS_FILTER, view_replacements),

        MessageHandler(commands.UPLOAD_REPLACEMENTS_FILTER, upload_replacements),
        MessageHandler(commands.DOCUMENT_FILTER, document),
        # ConversationHandler(
        #     entry_points = [
        #         MessageHandler(commands.UPLOAD_REPLACEMENTS_FILTER, upload_replacements)
        #     ],
        #     states = { 0: [
        #         CallbackQueryHandler(replacements_edit_modes),
        #         MessageHandler(commands.DOCUMENT_FILTER, document),
        #     ]},
        #     fallbacks = [MessageHandler(None, cancel, block=False)]
        # ),

        ConversationHandler(
            name='add_user', persistent=True,
            entry_points=[MessageHandler(commands.ADD_USER_FILTER, add_user_begin,
                          block=False)],
            states={
                0: [
                    MessageHandler(USERNAME_FILTER, au_name, block=False),
                    MessageHandler(commands.CANCEL_FILTER, cancel, block=False),
                    MessageHandler(TEXT_FILTER, au_name_error, block=False)
                ],
                1: [
                    CallbackQueryHandler(au_edit, 'AU', block=False),
                    MessageHandler(PHONE_FILTER, au_phone, block=False),
                    MessageHandler(commands.CANCEL_FILTER, cancel, block=False)
                ],
                2: [
                    MessageHandler(commands.TRUE_FILTER | commands.SAVE_FILTER, au_save,
                                   block=False),
                    MessageHandler(commands.FALSE_FILTER | commands.CANCEL_FILTER, cancel,
                                   block=False)
                ]
            },
            fallbacks=[
                MessageHandler(commands.SAVE, au_save, block=False),
                MessageHandler(TEXT_FILTER, cancel, block=False)
            ]
        ),
        ConversationHandler(
            entry_points=[MessageHandler(commands.DELETE_USER_FILTER, delete_user_begin,
                          block=False)],
            states={
                0: [
                    MessageHandler(commands.CANCEL_FILTER, cancel, block=False),
                    CallbackQueryHandler(du_switch_input, 'DU_phone', block=False),
                    CallbackQueryHandler(du_switch_input, 'DU_name', block=False),
                    MessageHandler(TEXT_FILTER, du_confirm, block=False)
                ],
                1: [
                    MessageHandler(commands.TRUE_FILTER | commands.SAVE_FILTER, du_save,
                                   block=False),
                    MessageHandler(commands.FALSE_FILTER | commands.CANCEL_FILTER, cancel,
                                   block=False)
                ]
            },
            fallbacks=[
                MessageHandler(commands.SAVE, du_save, block=False),
                MessageHandler(TEXT_FILTER, cancel, block=False)
            ]
        ),

        MessageHandler(TEXT_FILTER | COMMAND_FILTER, unknown, block=False)
    ))
    bot_running = True
    application.run_polling()

if __name__ == '__main__':
    main()
