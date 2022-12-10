'''
All constants for files.py
Все константы для files.py
'''

__all__ = (
    'NULL',
    'REPLACING_TEACHER',
    'LESSON',
    'CLASS_NAME',
    'ROOM',
    'REPLACEMENT_NECESSARY_TYPES',
    'REPLACEMENT_DATATYPES',
    'DATE_PATTERN',
    'MONTHS',
    'TEACHER_PATTERN',
    'ADDITIONAL_PATTERN',
    # 'ADDITIONAL_PATTERNS',
    # 'ADDITIONAL_TYPES',
    'USER_DATATYPES'
)

# SQLite-related constants
# Константы, связанные с SQLite
NULL = "NULL"

# Table headers
# Заголовки таблицы
REPLACING_TEACHER = 'заменяющий учитель'
LESSON = '№ урока'
CLASS_NAME = 'класс'
ROOM = 'кабинет'
REPLACEMENT_NECESSARY_TYPES = (REPLACING_TEACHER, LESSON, CLASS_NAME)
REPLACEMENT_DATATYPES = (*REPLACEMENT_NECESSARY_TYPES, ROOM)

# Date constants
# Константы дат
DATE_PATTERN = (
    r'(?P<d>0?[1-9]|[12][0-9]|3[01])'
    r'\s*'
    r'(?P<m>янв(?:аря)?|фев(?:раля)?|мар(?:та)?|апр(?:еля)?|'
    r'ма(?:я)|июн(?:я)?|июл(?:я)?|авг(?:уста)?|сен(?:тября)?|'
    r'окт(?:ября)?|ноя(?:бря)?|дек(?:абря)?)'
    r'\s*'
    r'(?P<y>[0-9]+)'
)
MONTHS = ('янв', 'фев', 'мар', 'апр', 'ма', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек')

# "Replacing teacher" field patterns
# Шаблоны для поля "Заменяющий учитель"
TEACHER_PATTERN = r'([А-ЯЁ][а-яё]+)[\s]*([А-ЯЁа-яё]*)[\s.]*([А-ЯЁа-яё]*)'
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
