'''
All constats for files.py
Все константы для files.py
'''

__all__ = (
    'NULL',
    'DATE_PATTERN',
    'MONTHS',
    'USER_DATATYPES'
)

# SQLite-related constants
# Константы, связанные с SQLite
NULL = "NULL"

# Date constants
# Константы дат
DATE_PATTERN = (
    '(0?[1-9]|[12][0-9]|3[01]) '

    '(янв(?:аря)?|фев(?:раля)?|мар(?:та)?|апр(?:еля)?|'
    'ма(?:я)|июн(?:я)?|июл(?:я)?|авг(?:уста)?|сен(?:тября)?|'
    'окт(?:ября)?|ноя(?:бря)?|дек(?:абря)?) '

    '([0-9]+)'
)
MONTHS = ('янв', 'фев', 'мар', 'апр', 'ма', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек')

# User data constants
# Констатны, связанные с данными пользователей
# USER_DATATYPES = ('name', 'replacer', 'scheduler', 'dispatcher', 'admin')
USER_DATATYPES = ('name', 'replacer', 'dispatcher', 'admin')
