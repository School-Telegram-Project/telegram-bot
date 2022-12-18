'''
All constants for main.py
Все константы для main.py
'''

from telegram.ext.filters import (TEXT as TEXT_FILTER, Regex as _RegexFilter,
                                  Document as _DocumentFilter, CONTACT as CONTACT_FILTER,
                                  COMMAND as COMMAND_FILTER, BaseFilter as _BaseFilter)
import telegram.ext.filters as _filters
import telegram.constants as _constants
from dataclasses import dataclass
import gettext



# Folder of program
# Папка программы
SELF_FOLDER = None

# INI section
# Секция INI
INI_SECTION = 'telegram-replacements-bot'

# Message-related constants
# Константы, относящиеся к сообщениям
HTML = _constants.ParseMode.HTML
MAX_TEXT_LENGTH = _constants.MessageLimit.MAX_TEXT_LENGTH
HORIZONTAL_BAR = '\n<s>---------</s>\n'

@dataclass()
class LanguageDependentConstants:
    translation: gettext.GNUTranslations
    _: gettext.gettext

    def __init__(self, translation):
        self.translation = translation
        self._ = translation.gettext
    
    @property
    def TRUE(self) -> str:
        return self._('Да')
    @property
    def FALSE(self) -> str:
        return self._('Нет')
    def TRANSLATE_BOOL(self, x: bool) -> str:
        return self.TRUE if x else self.FALSE

    # Command messages
    # Сообщения-команды
    @property
    def VIEW_REPLACEMENTS(self) -> str:
        return self._('Посмотреть мои замены')
    
    @property
    def UPLOAD_REPLACEMENTS_FILE(self) -> str:
        return self._('Загрузить файл замен')
    
    @property
    def ENABLE_BOT(self) -> str:
        return self._('Запустить бот')
    @property
    def DISABLE_BOT(self) -> str:
        return self._('Выключить бот')
    @property
    def DOWNLOAD_LOGS(self) -> str:
        return self._('Скачать последний лог-файл')
    
    @property
    def ADD_USER(self) -> str:
        return self._('Добавить нового пользователя')
    @property
    def AU_EDIT_NAME(self) -> str:
        return self._('Изменить имя пользователя')
    @property
    def AU_CHANGE_USER_REPLACEMENTS(self) -> str:
        return self._('Заменяющий')
    @property
    def AU_CHANGE_USER_DISPATCHER(self) -> str:
        return self._('Диспетчер')
    @property
    def AU_CHANGE_USER_ADMIN(self) -> str:
        return self._('Администратор')
    
    @property
    def DELETE_USER(self) -> str:
        return self._('Удалить пользователя')
    @property
    def DU_NAME(self) -> str:
        return self._('Использовать имя')
    @property
    def DU_PHONE(self) -> str:
        return self._('Использовать номер телефона')
    
    @property
    def SAVE(self) -> str:
        return self._('Сохранить')
    @property
    def CANCEL(self) -> str:
        return self._('Отменить')

    # Telegram filters for command-messages
    # Фильтры Телеграмма для сообщений-команд
    @property
    def TRUE_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.TRUE}')
    @property
    def FALSE_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.FALSE}')

    @property
    def DOCUMENT_FILTER(self) -> _BaseFilter:
        return _DocumentFilter.FileExtension('doc') | _DocumentFilter.FileExtension('docx')
    @property
    def VIEW_REPLACEMENTS_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.VIEW_REPLACEMENTS}')
    @property
    def UPLOAD_REPLACEMENTS_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.UPLOAD_REPLACEMENTS_FILE}')
    @property
    def ENABLE_BOT_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.ENABLE_BOT}')
    @property
    def DISABLE_BOT_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.DISABLE_BOT}')
    # DOWNLOAD_FILTER = (_filters.TEXT &
    #                    _filters.Regex('(?i)' + DOWNLOAD))

    @property
    def ADD_USER_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.ADD_USER}')
    @property
    def DELETE_USER_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.DELETE_USER}')

    @property
    def SAVE_FILTER(self) -> _BaseFilter:
        return TEXT_FILTER & _RegexFilter(f'(?i){self.SAVE}')
    @property
    def CANCEL_FILTER(self) -> _BaseFilter:
        return _RegexFilter(f'(?i){self.CANCEL}') | _RegexFilter('(?i)cancel')

USERNAME_FILTER = TEXT_FILTER & _RegexFilter(r'\w+\s+\w\s+\w')
PHONE_FILTER = TEXT_FILTER & _RegexFilter(r'(?:\+{0,1})(?P<num>[\d \-]{11,})')
