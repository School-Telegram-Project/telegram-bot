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

logger = logs.logger('Files')
headers = None

def setup_translation(localedir, language):
    global headers
    headers = Headers(localedir, language)

def find_user(telegram_id = 0, phone_num = '', name = '') -> tuple:
    '''
    Finds user in database
    
    Найди пользователя в базе данных
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()
            # Find user by ID
            # Найти пользователя по ID
            if telegram_id > 0:
                cursor.execute(
                     'SELECT DISTINCT\n'
                     '\tname,\n'
                     '\treplacer,\n'
                     '\tdispatcher,\n'
                     #  '\tscheduler,\n'
                     '\tadmin\n'
                     'FROM staff\n'
                    f'WHERE telegram_id = ?;',
                    [telegram_id]
                )
                data = cursor.fetchall()
                if data:
                    return tuple(zip(USER_DATATYPES, data[0]))

            # Find user by phone
            # Найти пользователя по номеру телефона
            if phone_num != '':
                phone_num = int(phone_num)
                cursor.execute(
                     'SELECT DISTINCT\n'
                     '\tname,\n'
                     '\treplacer,\n'
                     '\tdispatcher,\n'
                     #  '\tscheduler,\n'
                     '\tadmin,\n'
                     '\ttelegram_id\n'
                     'FROM staff\n'
                    f'WHERE phone_num = ?;',
                    [phone_num]
                )
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
                return tuple(zip((*USER_DATATYPES, 'tg_id'), data[0]))

            # Find user by name (returns Telegram ID)
            # Найти пользователя по имени (возвращает Telegram ID)
            if name == '':
                return None
            cursor.execute(
                 'SELECT phone_num, telegram_id\n'
                 'FROM staff\n'
                f'WHERE name = ?;',
                [name]
            )
            return cursor.fetchall()

    except sqlite3.Error as sql_error:
        logger.exception(f'Error occurred while searching for user {telegram_id}')
        return None

def add_user(data: dict) -> int:
    '''
    Add new user
    Returns:
    - 1: success
    - 0: user already in database
    - -1: error

    Добавить нового пользователя
    Возвращает:
    - 1: успех
    - 0: пользователь есть в базе данных
    - -1: ошибка
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO staff '
                '(phone_num, name, replacer, scheduler, dispatcher, admin)\n'
                'VALUES (:phone, :name, :replacer, 0, :dispatcher, :admin)',
                data
            )
            return cursor.rowcount
    except sqlite3.Error as sql_error:
        logger.exception(f'Error occurred while searching for user {telegram_id}')
        return -1

def delete_user(phone_number) -> bool:
    '''
    Delete user, returns True if successful

    Удалить пользователя, возвращает True при успехе
    '''
    try:
        with sqlite3.connect('database') as connection:
            cursor = connection.cursor()
            cursor.execute(
                'DELETE FROM staff\n'
                'WHERE phone_num = ?',
                [phone_number]
            )
        return bool(cursor.rowcount)
    except sqlite3.Error as sql_error:
        logger.exception(f'Error occurred while removing user with phone number {phone_number}')
        return False

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
    
    Привести поле "учитель" к формату 'Aaa A A' и дополнительной информации
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
    
    Извлечь данные из файла замен
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
            m = re.findall(headers.DATE_PATTERN, text, re.I)
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
                if text in headers.REPLACEMENT_DATATYPES:
                    columns.append((i, text))

            for row in block.rows[1:]:
                data = {}
                for i, header in columns:
                    if i >= len(row.cells):
                        break
                    text = row.cells[i].text.strip()
                    if text != '':
                        data[header] = text
                if any(datatype not in data for datatype in headers.REPLACEMENT_NECESSARY_TYPES):
                    continue
                teacher_data = teacher_parse(data[headers.REPLACING_TEACHER])
                if teacher_data is None:
                    continue
                add_value(
                    key=teacher_data[0],
                    value=[Replacement(
                        replaced_teacher = replaced_teacher,
                        lesson = data[headers.LESSON],
                        class_name = data[headers.CLASS_NAME],
                        date = date,
                        room = (data[headers.ROOM] if headers.ROOM in data
                                and data[headers.ROOM] is not None else None),
                        additional = teacher_data[1]
                    )],
                    dictionary=replacements
                )

    return replacements


def replacements_generator(data: dict) -> Generator:
    '''
    Generator of 1-dimensional array from dictionary {date: replacements}
    
    Генератор 1-мерного массива из словаря {дата: замены}
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
            cursor.executescript(
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
        logger.exception('Could not save replacements to database')
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
        logger.exception(f'Could not load replacements for {teacher}')
        return None
