'''
File operation module
Модуль операций с файлами
'''

import sqlite3
import re

from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table, _Row
from docx.text.paragraph import Paragraph

import logs
from user import User

_NULL = "NULL"
_NULL_QUOTE = f"'{_NULL}'"
_DATE_PATTERN = (
    '(0?[1-9]|[12][0-9]|3[01]) '

    '(янв(?:аря)?|фев(?:раля)?|мар(?:та)?|апр(?:еля)?|'
    'ма(?:я)|июн(?:я)?|июл(?:я)?|авг(?:уста)?|сен(?:тября)?|'
    'окт(?:ября)?|ноя(?:бря)?|дек(?:абря)?) '

    '([0-9]+)'
)
_MONTHS = ('янв', 'фев', 'мар', 'апр', 'ма', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек')
_SINGLE_GROUP = 'весь класс'
_GROUPS_PATTERN = f'({_SINGLE_GROUP})|([0-9])(?: группы)'

def find_user(telegram_id: int, phone_num = '') -> User:
    '''
    Finds user in database by phone number or Telegram ID
    Находит пользователя в базе данных по номеру телефона или ID Telegram'а
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()

            # Find user by ID
            # Найти пользователя по ID
            query = (
                    'SELECT DISTINCT\n'
                    '\tname,\n'
                    '\treplacer,\n'
                    '\tscheduler,\n'
                 #  '\tdispatcher,\n'
                    '\tadmin\n'
                    'FROM staff\n'
                f'WHERE telegram_id = {telegram_id};'
            )
            cursor.execute(query)
            data = cursor.fetchall()
            if data:
                return User(data[0])


            # Find user by phone
            # Найти пользователя по номеру телефона
            if phone_num == '':
                return None

            phone_num = int(phone_num)
            query = (
                 'SELECT DISTINCT\n'
                 '\tname,\n'
                 '\treplacer,\n'
                 '\tscheduler,\n'
                #  '\tdispatcher,\n'
                 '\tadmin,\n'
                 '\ttelegram_id\n'
                 'FROM staff\n'
                f'WHERE phone_num = {phone_num};'
            )
            cursor.execute(query)
            data = cursor.fetchall()
            if not data:
                return None
            if data[0][-1] in (None, _NULL):
                query = (
                     'UPDATE staff\n'
                    f'SET telegram_id = {telegram_id}\n'
                    f'WHERE phone_num = {phone_num};'
                )
                cursor.execute(query)
                cursor.fetchall()
            return User(data[0][:-1])
    except sqlite3.Error as sql_error:
        logs.message(f'Error occured while searching for user {telegram_id}: {sql_error}')

# def add_user(data: tuple) -> int:
#     '''
#     Adds new user to table in database
#     Returns success (1 = added, 0 = already in DB, -1 = error)
#     Добавляет нового пользователя в таблицу в базе данных
#     Возвращает результат (1 = добавлен, 0 = уже в базе, -1 = ошибка)
#     '''
#     if len(data) < 8:
#         return -1
#     try:
#         with sqlite3.connect('data') as connection:
#             cursor = connection.cursor()
#             query = (
#                  'INSERT OR IGNORE INTO staff '
#                  '(phone_num, telegram_id, name, full_name, replacer, scheduler, dispatcher, admin)\n'
#                  'VALUES\n'
#                 # f'\t({",".join([str(value) for value in data])});'
#                 f'\t({",".join([str(value) for value in data]) + ",0"});'
#             )
#             cursor.execute(query)
#             row = cursor.fetchall()
#             return bool(row)
#     except sqlite3.Error as sql_error:
#         logs.message(f'Error occured while adding user to database: {sql_error}')
#         return -1

# def save_replacements(file: str, mode = 0) -> int:


def iter_block_items(parent) -> object:
    """
    Generate a reference to each paragraph and table child within *parent*,
    in document order. Each returned value is an instance of either Table or
    Paragraph. *parent* would most commonly be a reference to a main
    Document object, but also works for a _Cell object, which itself can
    contain paragraphs and tables.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif isinstance(parent, _Row):
        parent_elm = parent._tr
    else:
        raise ValueError("Docx reading error")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def teacher_parse(text: str) -> str:
    '''
    Parse teacher field to normalized string
    '''
    # TODO
    words = re.split(r'[\s()]', text)
    groups = re.findall(_GROUPS_PATTERN, words[-1], re.I)
    if groups:
        if groups[0] == _SINGLE_GROUP:
            words.pop(len(words) - 1)
        else:
            words[-1] = str(groups[0])
    return ' '.join(words)

def replacements_from_file(file_path: str) -> tuple:
    '''
    Extracts data from replacements document
    Извлекает данные из файла замен
    '''
    document = Document(file_path)
    replaced_teachers = []
    replacing_teachers = set()
    replacements = {}
    date = tuple()
    keys = ('№ урока', 'Время', 'Класс', 'Кабинет', 'Заменяющий учитель')
    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = block.text
            d = re.findall(_DATE_PATTERN, text, re.I)
            if d and len(d[0]) == 3:
                d = d[0]
                date = int(d[0]), _MONTHS.index(str(d[1][:3] if len(d) > 2 else d[1])), int(d[2])
            else:
                replaced_teachers.append(teacher_parse(text))
        elif isinstance(block, Table):
            if len(block.rows) < 2:
                continue
            for row in block.rows[1:]:
                row_data = {'Заменённый учитель': replaced_teachers[-1]}
                for k, text in zip(keys, (cell.text for cell in row.cells)):
                    if k == keys[-1]:
                        row_data[k] = teacher_parse(text)
                    else:
                        row_data[k] = text.strip()
                if not isinstance(replacements.get(date), list):
                    replacements[date] = [row_data]
                else:
                    replacements[date].append(row_data)
                replacing_teachers.add(row_data[keys[-1]])

    return replacing_teachers, replacements

# def save_replacements(file: str) -> int:
#     '''
#     Returns amount of affected rows
#     Возвращает количество изменённых строк
#     '''
#     db_data = []
#     keys = [ 'Класс', 'Заменяющий учитель', '№ урока', 'Кабинет' ]
#     for i, table in enumerate(file_data):
#         for _, row in enumerate(table):
#             if not isinstance(row, dict):
#                 continue
#             table_data = []
#             for j, key in enumerate(keys):
#                 v = row[key]
#                 if not (j <= 1 or (j > 1 and (v.isdigit() or v == ''))):
#                     table_data = None
#                     break
#                 if v == '' or v.isspace():
#                     table_data.append(_NULL)
#                     continue
#                 table_data.append(v)
#             if table_data is not None:
#                 table_data.append(replaced_teachers[i])
#                 db_data.append(table_data)
#     return _save_replacement(db_data, mode)

# def _save_replacement(data: list, mode = 0) -> int:
def save_replacement(data: list) -> int:
    '''
    Save replacements data to database
    Returns amount of UNaffected rows
    Сохранение замен в базе данных
    Возвращает количество НЕизменённых строк
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            query = (
                "CREATE TABLE IF NOT EXISTS replacements (\n"
                "\tid INTEGER PRIMARY KEY,\n"
                "\tClass TEXT NOT NULL,\n"
                "\tTeacher TEXT NOT NULL,\n"
                "\tLesson INTEGER NOT NULL,\n"
                "\tRoom TEXT,\n"
                "\treplaced_teacher TEXT NOT NULL);"
            )
            cursor.execute(query)

            end = len(data) - 1
            # if mode == 0:
            query = (
                "DELETE FROM replacements;\n"
                "DELETE FROM sqlite_sequence WHERE name='replacements';"
            )
            cursor.executescript(query)
            cursor.fetchall()

            query = (
                    "INSERT INTO replacements "
                    "(class,teacher,lesson,room,replaced_teacher)\n"
                    "VALUES"
            )
            for i, values in enumerate(data):
                query += (
                    f"\n\t'{values['Класс']}','{values['Заменённый учитель']}',"
                    f"{values['№ урока']},"
                    f"{values['Класс'] if values['Класс'] != _NULL else _NULL_QUOTE},"
                    f"'{values['Заменяющий учитель']}'{',' if i < end else ';'}"
                )
            cursor.execute(query)
            cursor.fetchall()
            changes = cursor.rowcount
            cursor.close()
            return len(data) - changes
    except sqlite3.Error as error:
        logs.message(f'Can not save data to database: {error}', 2)
        return -1

def read_replacements(teacher: str) -> list:
    '''
    Reads data from replacements
    Чтение данных из базы замен
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            select_query = (
                 "SELECT\n"
                 "\tClass,\n"
                 "\tLesson,\n"
                 "\tRoom\n"
                 "FROM replacements\n"
                f"WHERE Teacher = '{teacher}'"
                 "ORDER BY Lesson;"
            )
            cursor.execute(select_query)
            rows = cursor.fetchall()
            # logs.message(rows)
        return rows
    except sqlite3.Error as error:
        logs.message(f'Can not read database: {error}', 2)
        return None
