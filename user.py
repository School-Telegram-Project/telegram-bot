'''
Module for User class
Модуль для класса User
'''

from dataclasses import dataclass


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
    scheduler: bool = False
    state: int = 0

    def __init__(self, id:int, args: list):
        self.id = id
        self.name = args[0]
        if isinstance(args[1], str):
            self.full_name = args[1]
        self.replacer = bool(args[2])
        self.dispatcher = bool(args[3])
        self.scheduler = bool(args[4])
        self.state = 0

    def __eq__(self, o):
        return (isinstance(o, User) and o.id == self.id) or (isinstance(o, int) and o == self.id)

    def __str__(self):
        return str(self.id)

    def keyboard(self):
        '''
        Create Telegram keyboard markup based on user's privileges
        Создать набор клавиш на основе привелегий пользователя
        '''
        keyboard = []
        if self.replacer:
            keyboard.append(['Посмотреть замены'])
        if self.dispatcher:
            # keyboard.append(['Добавить замены вручную', 'Загрузить файл замен'])
            keyboard.append(['Загрузить файл замен'])
        if self.scheduler:
            keyboard.append(['Обновить расписание'])
        return keyboard
