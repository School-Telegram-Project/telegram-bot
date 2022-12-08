'''
Module for working with replacements
Модуль обработки замен
'''
from dataclasses import dataclass, field
from datetime import datetime


@dataclass()
class Replacement:
    '''
    Replacement dataclass
    Структура замены
    '''
    replaced_teacher: str
    replacing_teacher: str
    lesson: int
    class_name: str
    date: datetime
    room = ''
    additional: tuple = field(default_factory=tuple)

    def __init__(self, replaced_teacher, lesson, class_name, date, room, additional):
        self.replaced_teacher = replaced_teacher
        self.lesson = lesson
        self.class_name = class_name
        self.date = date
        self.room = room
        self.additional = additional
