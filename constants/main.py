'''
All constats for main.py
Все константы для main.py
'''

import telegram.ext.filters as _filters
import telegram.constants as _constants

__all__ = (
    'SELF_FOLDER',
    'VIEW_REPLACEMENTS',
    'UPLOAD_REPLACEMENTS_FILE',
    'ENABLE_BOT',
    'DISABLE_BOT',
    # 'DOWNLOAD',
    # 'ADD_USER',
    # 'DELETE_USER',
    'DOCUMENT_FILTER',
    'VIEW_REPLACEMENTS_FILTER',
    'UPLOAD_REPLACEMENTS_FILTER',
    'ENABLE_BOT_FILTER',
    'DISABLE_BOT_FILTER',
    # 'DOWNLOAD_FILTER',
    # 'ADD_USER_FILTER',
    # 'DELETE_USER_FILTER',
    'CONTACT_FILTER',
    'HTML',
    'MAX_TEXT_LENGTH',
    'HORIZONTAL_BAR'
)

# Folder of program
# Папка программы
SELF_FOLDER = None

# Command messages
# Сообщения-команды
VIEW_REPLACEMENTS = 'Посмотреть мои замены'
UPLOAD_REPLACEMENTS_FILE = 'Загрузить файл замен'
ENABLE_BOT = 'Запустить бот'
DISABLE_BOT = 'Выключить бот'
# DOWNLOAD = 'Скачать последний лог-файл'
# ADD_USER = 'Добавить нового пользователя'
# DELETE_USER = 'Удалить пользователя'

# Telegram filters for command-messages
# Фильтры Телеграмма для сообщений-команд
DOCUMENT_FILTER = (_filters.Document.FileExtension('doc') |
                   _filters.Document.FileExtension('docx'))
VIEW_REPLACEMENTS_FILTER = (_filters.TEXT &
                            _filters.Regex('(?i)' + VIEW_REPLACEMENTS))
UPLOAD_REPLACEMENTS_FILTER = (_filters.TEXT &
                              _filters.Regex('(?i)' + UPLOAD_REPLACEMENTS_FILE))
ENABLE_BOT_FILTER = (_filters.TEXT &
                     _filters.Regex('(?i)' + ENABLE_BOT))
DISABLE_BOT_FILTER = (_filters.TEXT &
                      _filters.Regex('(?i)' + DISABLE_BOT))
# DOWNLOAD_FILTER = (_filters.TEXT &
#                    _filters.Regex('(?i)' + DOWNLOAD))
# ADD_USER_FILTER = (_filters.TEXT &
#                    _filters.Regex('(?i)' + ADD_USER))
# DELETE_USER_FILTER = (_filters.TEXT &
#                       _filters.Regex('(?i)' + DELETE_USER))
CONTACT_FILTER = _filters.CONTACT

# Message-related constants
# Константы, относящиеся к сообщениям
HTML = _constants.ParseMode.HTML
MAX_TEXT_LENGTH = _constants.MessageLimit.MAX_TEXT_LENGTH
HORIZONTAL_BAR = '\n<s>---------</s>\n'
