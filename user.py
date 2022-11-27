'''
Module for User class
Модуль для класса User
'''

from dataclasses import dataclass

VIEW_REPLACEMENTS = 'Посмотреть мои замены'
UPLOAD_REPLACEMENTS_FILE = 'Загрузить файл замен'
ENABLE_BOT = 'Запустить бота'
DISABLE_BOT = 'Выключить бота'
DOWNLOAD = 'Скачать последний лог-файл'
# ADD_USER = 'Добавить нового пользователя'
# DELETE_USER = 'Удалить пользователя'

@dataclass
class User:
    '''
    User's data
    Данные пользователя
    '''
    name: str
    replacer: bool
    scheduler: bool
    # dispatcher: bool = False
    admin: bool
    state: int = 0

    def __init__(self, args: tuple):
        # if len(args) < 5:
        if len(args) < 4:
            raise ValueError()
        self.name = args[0]
        self.replacer = bool(args[1])
        self.scheduler = bool(args[2])
        # self.dispatcher = bool(args[3])
        # self.admin = bool(agrs[4])
        self.admin = bool(args[3])
        self.state = 0

    def keyboard(self, bot_running: bool) -> list:
        '''
        Create Telegram keyboard markup based on user's privileges
        Создать набор клавиш на основе привелегий пользователя
        '''
        _keyboard = []
        if bot_running and self.replacer:
            _keyboard.append([VIEW_REPLACEMENTS])
        if bot_running and self.scheduler:
            # kb.append(['Добавить замены вручную', 'Загрузить файл замен'])
            _keyboard.append([UPLOAD_REPLACEMENTS_FILE])
        # if bot_running and self.dispatcher:
        #     kb.append(['Обновить расписание'])
        if self.admin:
            _keyboard.extend([
                [DISABLE_BOT if bot_running else ENABLE_BOT]
                # [DOWNLOAD]
                # [ADD_USER, DELETE_USER]
            ])
        return _keyboard
