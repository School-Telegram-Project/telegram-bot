'''
File operation module
Модуль операций с файлами
'''

import sqlite3

from docx import Document

import logs
from user import User

_NULL = "NULL"
_NULL_QUOTE = f"'{_NULL}'"

def int_phone(phone_num: str) -> int:
    '''
    Turns phone number string into number
    Переводит строковый номер телефона в число
    '''
    phone_num = phone_num.strip().replace(' ', '')
    if phone_num.count('+') > 0:
        phone_num = str(int(phone_num[1]) + 1) + phone_num[2:]
    return int(phone_num)

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

            phone_num = int_phone(phone_num)
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
            row = cursor.fetchall()
            if not row:
                return None
            if row[0][-1] in (None, _NULL):
                query = (
                     'UPDATE staff\n'
                    f'SET telegram_id = {telegram_id}\n'
                    f'WHERE phone_num = {phone_num};'
                )
                cursor.execute(query)
                cursor.fetchall()
            data = row[0][:-1]
            return User(data)
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
def replacements_from_file(file_path: str) -> tuple:
    '''
    Extracts data from replacements document
    Извлекает данные из файла замен
    '''
    document = Document(file_path)
    replaced_teachers = []
    for _, par in enumerate(document.paragraphs):
        text = par.text
        if isinstance(text, str) and text != '' and not text.isspace():
            replaced_teachers.append(text)
    replaced_teachers.pop(0)

    data = []
    replacing_teachers = set()
    tables = zip(replaced_teachers, document.tables)
    keys = ('№ урока', 'Время', 'Класс', 'Кабинет', 'Заменяющий учитель')
    for teacher, table in tables:
        if len(table.rows) < 2:
            continue
        for row in table.rows[1:]:
            row_data = {'Заменённый учитель': teacher}
            for key, text in zip(keys, (cell.text for cell in row.cells)):
                if key == keys[-1]:
                    row_data[key] = ' '.join(t.strip() for t in text.split('. '))
                else:
                    row_data[key] = text.strip()
            data.append(row_data)
            repl_teacher = str(row_data[keys[-1]])
            if repl_teacher not in replaced_teachers:
                replacing_teachers.add(repl_teacher)
    return replacing_teachers, data

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
            cursor.fetchall()

            end = len(data) - 1
            # if mode == 0:
            query = (
                "DELETE FROM replacements;\n"
                "DELETE FROM sqlite_sequence WHERE name='replacements';"
            )
            cursor.executemany(query)

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
