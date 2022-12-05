'''
File operation module
Модуль операций с файлами
'''

import sqlite3
import re
from datetime import datetime

from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table, _Row
from docx.text.paragraph import Paragraph

import logs

from constants.files import *


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

def teacher_parse(text: str) -> tuple:
    '''
    Parse teacher field to normalized string and group
    Приводит поле "учитель" к нормализированной строке и группе
    '''
    groups = 0
    matches = re.findall(r'[(]+[\D]*?([0-9]*)[\D]*?[)]+', text)
    if matches:
        m = matches[0]
        text = text[:text.index('(')].strip()
        if len(m):
            groups = int(m)
    words = re.findall(r'([А-ЯЁ][а-яё]+)[\s]*([А-ЯЁа-яё]*)[\s.]*([А-ЯЁа-яё]*)', text)
    if words and words[0]:
        words = words[0]
        string = words[0]
        if len(words) > 1 and words[1] != '':
            string += ' ' + words[1][0]
        if len(words) > 2 and words[2] != '':
            string += ' ' + words[2][0]
        return (string, groups)
    return None

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
            text = block.text.strip()
            if text == '':
                continue
            d = re.findall(DATE_PATTERN, text, re.I)
            if d and len(d[0]) == 3:
                d = d[0]
                date = datetime(
                    int(d[2]),
                    MONTHS.index(str(d[1][:3] if len(d) > 2 else d[1])),
                    int(d[0])
                    )
                if date < datetime.now():
                    date = None
                else:
                    date = f'{date.year}.{date.month}.{date.day}'
            else:
                teacher = teacher_parse(text)
                if teacher:
                    replaced_teachers.append(teacher[0])
        elif isinstance(block, Table):
            if len(block.rows) < 2 or date is None:
                continue
            for row in block.rows[1:]:
                exit_flag = False   # Отсутствует заменяющий учитель
                row_data = {'Заменённый учитель': replaced_teachers[-1]}
                for k, text in zip(keys, (cell.text for cell in row.cells)):
                    text = text.strip()
                    if k == keys[-1]:
                        if text == '':
                            exit_flag = True
                            break
                        parsed_str = teacher_parse(text)
                        if parsed_str:
                            row_data[k], row_data['Группа'] = parsed_str
                        else:
                            exit_flag = True
                            break
                    else:
                        row_data[k] = text.strip()
                if exit_flag:
                    continue
                if not isinstance(replacements.get(date), list):
                    replacements[date] = [row_data]
                else:
                    replacements[date].append(row_data)
                replacing_teachers.add(row_data[keys[-1]])

    return replacing_teachers, replacements

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
                "CREATE TABLE IF NOT EXISTS replacements (\n"
                "  id INTEGER PRIMARY KEY,\n"
                "  class TEXT NOT NULL,\n"
                "  teacher TEXT NOT NULL,\n"
                "  lesson INTEGER NOT NULL,\n"
                "  lesson_date TEXT NOT NULL,\n"
                "  class_group INTEGER,\n"
                "  room TEXT,\n"
                "  replaced_teacher TEXT NOT NULL);"
                "DELETE FROM replacements;\n"
                "DELETE FROM sqlite_sequence WHERE name='replacements';"
            )
            cursor.executescript(query)

            changes_count = 0
            # if mode == 0:

            for _, date in enumerate(data):
                query = (
                        "INSERT INTO replacements "
                        "(class,teacher,lesson,lesson_date,class_group,room,replaced_teacher)\n"
                        "VALUES"
                )
                for _, values in enumerate(data[date]):
                    query += (
                         "\n  ("
                        f"'{values['Класс']}',"
                        f"'{values['Заменяющий учитель']}',"
                        f"{values['№ урока']},"
                        f"'{date}',"
                        f"{values['Группа']},"
                        f"'{values['Кабинет'] if values['Кабинет'] != '' else NULL}',"
                        f"'{values['Заменённый учитель']}'"
                        f"),"
                    )
                query = query[:-1] + ";"
                cursor.execute(query)
                changes_count += cursor.rowcount
            cursor.fetchall()
            cursor.close()
            return changes_count
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
                 "SELECT class, teacher, lesson, lesson_date, class_group, room, replaced_teacher\n"
                 "FROM replacements\n"
                f"WHERE teacher = '{teacher}'\n"
                 "ORDER BY lesson_date;"
            )
            cursor.execute(select_query)
            rows = cursor.fetchall()
        return rows
    except sqlite3.Error as error:
        logs.message(f'Can not read database: {error}', 2)
        return None
