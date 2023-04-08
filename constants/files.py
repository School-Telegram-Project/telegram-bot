'''
All constants for files.py
Все константы для files.py
'''

from dataclasses import dataclass
import gettext


__all__ = (
    'NULL',
    'Headers',
    'TEACHER_PATTERN',
    'ADDITIONAL_PATTERN',
    'USER_DATATYPES'
)

# SQLite-related constants
# Константы, связанные с SQLite
NULL = "NULL"

@dataclass()
class Headers:
    translation: gettext.GNUTranslations
    _: gettext.gettext

    def __init__(self, localedir, language):
        self.translation = gettext.translation('headers', localedir=localedir, languages=[language])
        self._ = self.translation.gettext

    # Table headers
    # Заголовки таблицы
    @property
    def REPLACING_TEACHER(self):
        return self._('заменяющий учитель')
    @property
    def LESSON(self):
        return self._('№ урока')
    @property
    def CLASS_NAME(self):
        return self._('класс')
    @property
    def ROOM(self):
        return self._('кабинет')
    @property
    def REPLACEMENT_NECESSARY_TYPES(self):
        return (self.REPLACING_TEACHER, self.LESSON, self.CLASS_NAME)
    @property
    def REPLACEMENT_DATATYPES(self):
        return (*self.REPLACEMENT_NECESSARY_TYPES, self.ROOM)

    # Date constants
    # Константы дат
    @property
    def DATE_PATTERN(self):
        return self._(
        r'(?P<d>0?[1-9]|[12][0-9]|3[01])'
        r'\s*'
        r'(?P<m>янв(?:аря)?|фев(?:раля)?|мар(?:та)?|апр(?:еля)?|'
        r'ма(?:я)|июн(?:я)?|июл(?:я)?|авг(?:уста)?|сен(?:тября)?|'
        r'окт(?:ября)?|ноя(?:бря)?|дек(?:абря)?)'
        r'\s*'
        r'(?P<y>[0-9]+)'
    )
    @property
    def MONTHS(self):
        return [self._('янв'), self._('фев'),
                self._('мар'), self._('апр'), self._('ма'),
                self._('июн'), self._('июл'), self._('авг'),
                self._('сен'), self._('окт'), self._('ноя'),
                self._('дек')]

# "Replacing teacher" field patterns
# Шаблоны для поля "Заменяющий учитель"
TEACHER_PATTERN = r'(\w+)[\s]*(\w*)[\s.]*(\w*)'
ADDITIONAL_PATTERN = r'\(+[\w\s]+\)+'
# ADDITIONAL_PATTERNS = (
#     r'(?P<percent>(\d+))\s*%+|'
#     r'\(+\s*(?:'
#     r'(?P<whole>ве[сc]ь\s*кла[сc]{1,3})|'
#     r'(?P<group>(\d+))\s*груп|'
#     r'\s*вме[сc]то\s*(?P<instead>\d+[\w ]+)|'
#     r'\s*вме[сc]те\s*[сc]\s*(?P<with>\d+[\w ]+)'
#     r')\s*\w*\)+'
# )
# ADDITIONAL_TYPES = (
#     'percent',
#     'whole',
#     'group',
#     'instead',
#     'with'
# )

# User data constants
# Константы, связанные с данными пользователей
# USER_DATATYPES = ('name', 'replacer', 'scheduler', 'dispatcher', 'admin')
USER_DATATYPES = ('name', 'replacer', 'dispatcher', 'admin')
