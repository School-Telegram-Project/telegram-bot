'''
File operation module
Модуль операций с файлами
'''

import re
import sqlite3
from collections.abc import Generator
from datetime import datetime

from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table, _Cell, _Row
from docx.text.paragraph import Paragraph

import logs
from constants.files import *
from replacements import Replacement
from utils import add_value


def find_user(telegram_id: int, phone_num = '') -> tuple:
    '''
    Finds user in database by phone number or Telegram ID
    Находит пользователя в базе данных по номеру телефона или ID Telegram'а
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()

            # Find user by ID
            # Найти пользователя по ID
            query = (
                 'SELECT DISTINCT\n'
                 '\tname,\n'
                 '\treplacer,\n'
                 '\tdispatcher,\n'
                #  '\tscheduler,\n'
                 '\tadmin\n'
                 'FROM staff\n'
                f'WHERE telegram_id = {telegram_id};'
            )
            cursor.execute(query)
            data = cursor.fetchall()
            if data:
                return tuple(zip(USER_DATATYPES, data[0]))


            # Find user by phone
            # Найти пользователя по номеру телефона
            if phone_num == '':
                return None

            phone_num = int(phone_num)
            query = (
                 'SELECT DISTINCT\n'
                 '\tname,\n'
                 '\treplacer,\n'
                 '\tdispatcher,\n'
                #  '\tscheduler,\n'
                 '\tadmin,\n'
                 '\ttelegram_id\n'
                 'FROM staff\n'
                f'WHERE phone_num = {phone_num};'
            )
            cursor.execute(query)
            data = cursor.fetchall()
            if not data:
                return None
            if data[0][-1] in (None, NULL):
                query = (
                     'UPDATE staff\n'
                    f'SET telegram_id = {telegram_id}\n'
                    f'WHERE phone_num = {phone_num};'
                )
                cursor.execute(query)
                cursor.fetchall()
            return tuple(zip(USER_DATATYPES, data[0][:-1]))
    except sqlite3.Error as sql_error:
        logs.message(f'Error occurred while searching for user {telegram_id}: {sql_error}')

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
#         logs.message(f'Error occurred while adding user to database: {sql_error}')
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

def teacher_parse(text: str) -> tuple:
    '''
    Parse teacher field to format 'Aaa A A' and additional info
    Приводит поле "учитель" к формату 'Aaa A A' и дополнительной информации
    '''
    groups = 0
    teacher = re.match(TEACHER_PATTERN, text)
    if teacher is None:
        return None
    groups = teacher.groups()
    if len(teacher.groups()) < 3:
        return None
    result = (groups[0] + (' ' + groups[1][0] if groups[1] != '' else '') +
              (' ' + groups[2][0] if groups[2] != '' else ''))

    m = re.search(ADDITIONAL_PATTERN, text, re.I)
    return result, (m.group() if m is not None else None)

    # m = re.search(ADDITIONAL_PATTERNS, text, re.I)
    # if m is None or len(m) < 1:
    #     return (result, None)
    # for additional_type in ADDITIONAL_TYPES:
    #     info = m.group(additional_type)
    #     if info is None:
    #         continue
    #     if additional_type == 'whole':
    #         result.append((0, 0))
    #     elif additional_type == 'percent':
    #         result.append((int(info) / 100, 1))
    #     elif additional_type == 'group':
    #         result.append((int(info), 2))
    #     elif additional_type == 'instead':
    #         result.append((info, 3))
    #     else:       # 'with'
    #         result.append((info, 4))
    #     break
    # else:
    #     result.append(None)
    # return result

def replacements_from_file(file_path: str) -> tuple:
    '''
    Extracts data from replacements document
    Извлекает данные из файла замен
    '''
    document = Document(file_path)
    replaced_teacher = ''
    replacements = {}
    date = None
    for block in iter_block_items(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text == '':
                continue
            m = re.findall(DATE_PATTERN, text, re.I)
            if m and len(m[0]) == 3:
                date = datetime(
                    int(m[0][2]),
                    MONTHS.index(str(m[0][1][:min(3, len(m[0][1]) - 1)])),
                    int(m[0][0])
                )
                if (date - datetime.now()).days > 0:
                    date = None
            elif date is not None:
                teacher_data = teacher_parse(text)
                if teacher_data is not None:
                    replaced_teacher = teacher_data[0]
        elif isinstance(block, Table):
            if date is None or replaced_teacher == '' or len(block.rows) < 2:
                continue
            columns = []
            for i, cell in enumerate(block.rows[0].cells):
                text = cell.text.lower().strip()
                if text in REPLACEMENT_DATATYPES:
                    columns.append((i, text))

            for row in block.rows[1:]:
                data = {}
                for i, header in columns:
                    if i >= len(row.cells):
                        break
                    text = row.cells[i].text.strip()
                    if text != '':
                        data[header] = text
                if any(datatype not in data for datatype in REPLACEMENT_NECESSARY_TYPES):
                    continue
                teacher_data = teacher_parse(data[REPLACING_TEACHER])
                if teacher_data is None:
                    continue
                add_value(
                    key=teacher_data[0],
                    value=[Replacement(
                        replaced_teacher = replaced_teacher,
                        lesson = data[LESSON],
                        class_name = data[CLASS_NAME],
                        date = date,
                        room = data[ROOM] if ROOM in data and data[ROOM] is not None else None,
                        additional = teacher_data[1]
                    )],
                    dictionary=replacements
                )

    return replacements

def replacements_generator(data: dict) -> Generator:
    '''
    Returns generator of 1-dimensional array from dictionary {date: replacements}
    Возвращает генератор 1-мерного массива из словаря {дата: замены}
    '''
    for _, teacher in enumerate(data):
        for __, repl in enumerate(data[teacher]):
            yield (
                teacher,
                repl.class_name,
                repl.lesson,
                f'{repl.date.year}.{repl.date.month}.{repl.date.day}',
                repl.room if repl.room != '' else NULL,
                repl.replaced_teacher if repl.replaced_teacher != '' else NULL,
                repl.additional
            )

# def _save_replacement(data: list, mode = 0) -> int:
def save_replacement(data: list) -> int:
    '''
    Save replacements data to database
    Returns amount of affected rows
    Сохранение замен в базе данных
    Возвращает количество изменённых строк
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()
            query = (
                "BEGIN;\n"
                "CREATE TABLE IF NOT EXISTS replacements (\n"
                "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "    teacher TEXT NOT NULL,\n"
                "    class TEXT NOT NULL,\n"
                "    lesson INTEGER NOT NULL,\n"
                "    lesson_date TEXT NOT NULL,\n"
                "    room TEXT,\n"
                "    replaced TEXT,\n"
                "    additional TEXT\n"
                ");\n"
                "DELETE FROM replacements;\n"
                "DELETE FROM sqlite_sequence WHERE name='replacements';\n"
                "COMMIT;"
            )
            cursor.executescript(query)

            # if mode == 0:

            cursor.executemany(
                "INSERT INTO replacements "
                "(teacher, class, lesson, lesson_date, room, replaced, additional)\n"
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                replacements_generator(data)
            )
            cursor.fetchall()
            cursor.close()
            connection.commit()
            return cursor.rowcount
    except sqlite3.Error as error:
        logs.message(f'Can not save data to database: {error}', 2)
        return -1

def read_replacements(teacher: str) -> list:
    '''
    Reads data from replacements
    Чтение данных из базы замен
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()
            select_query = (
                "SELECT teacher, class, lesson, lesson_date, room, replaced, additional\n"
                "FROM replacements\n"
                "WHERE teacher = ?\n"
                "ORDER BY lesson_date;"
            )
            cursor.execute(select_query, [teacher])
            rows = cursor.fetchall()
        return rows
    except sqlite3.Error as error:
        logs.message(f'Can not read database: {error}', 2)
        return None
