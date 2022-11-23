'''
Module for User class
Модуль для класса User
'''

from dataclasses import dataclass

VIEW_REPLACEMENTS = 'Посмотреть мои замены'
UPLOAD_REPLACEMENTS_FILE = 'Загрузить файл замен'

@dataclass
class User:
    '''
    User's data
    Данные пользователя
    '''
    id: int
    name: str
    full_name: str = ''
    replacer: bool = True
    dispatcher: bool = False
    # scheduler: bool = False
    state: int = 0

    def __init__(self, args: tuple):
        # if len(args) < 6:
        if len(args) < 5:
            raise ValueError()
        self.id = args[0]
        self.name = args[1]
        if isinstance(args[2], str):
            self.full_name = args[2]
        self.replacer = bool(args[3])
        self.dispatcher = bool(args[4])
        # self.scheduler = bool(args[5])
        self.state = 0

    def __eq__(self, o):
        return (isinstance(o, User) and o.id == self.id) or (isinstance(o, int) and o == self.id)

    def __str__(self):
        return str(self.id)

    def _keyboard(self) -> list:
        kb = []
        if self.replacer:
            kb.append([VIEW_REPLACEMENTS])
        if self.dispatcher:
            # kb.append(['Добавить замены вручную', 'Загрузить файл замен'])
            kb.append([UPLOAD_REPLACEMENTS_FILE])
        # if self.scheduler:
        #     kb.append(['Обновить расписание'])
        return kb

    @property
    def keyboard(self) -> list:
        '''
        Create Telegram keyboard markup based on user's privileges
        Создать набор клавиш на основе привелегий пользователя
        '''
        return self._keyboard()
