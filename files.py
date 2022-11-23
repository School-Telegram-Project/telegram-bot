'''
File operation module
Модуль операций с файлами
'''

import sqlite3

from docx import Document

import logs
from user import User

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
                 'SELECT DISTINCT id\n'
                 'FROM staff\n'
                f'WHERE telegram_id = {telegram_id};'
            )
            cursor.execute(query)
            row = cursor.fetchall()
            if row:
                query = (
                     'SELECT DISTINCT\n'
                     '\tname,\n'
                     '\tfull_name,\n'
                     '\treplacer,\n'
                     '\tdispatcher,\n'
                    #  '\tscheduler\n'
                     'FROM staff\n'
                    f'WHERE id = {row[0][0]};'
                )
                cursor.execute(query)
                data = [ telegram_id, *cursor.fetchall()[0] ]
                return User(data)

            # Find user by phone
            # Найти пользователя по номеру телефона
            if phone_num == '':
                return None

            phone_num = int_phone(phone_num)
            query = (
                 'SELECT DISTINCT\n'
                 '\ttelegram_id,\n'
                 '\tname,\n'
                 '\tfull_name,\n'
                 '\treplacer,\n'
                 '\tdispatcher\n'
                #  '\tscheduler\n'
                 'FROM staff\n'
                f'WHERE phone_num = {phone_num};'
            )
            cursor.execute(query)
            row = cursor.fetchall()
            if not row:
                return None
            if row[0][0] == 'NULL':
                query = (
                     'UPDATE staff\n'
                    f'SET telegram_id = {telegram_id}'
                    f'WHERE phone_num = {phone_num};'
                )
                cursor.execute(query)
                cursor.fetchall()
                data = [ telegram_id, *row[0][1:] ]
            else:
                data = row[0]
            return User(data)
    except sqlite3.Error as sql_error:
        logs.message(f'Error occured while searching for user {telegram_id}: {sql_error}')

def add_user(data: tuple) -> int:
    '''
    Adds new user to table in database
    Returns success (1 = added, 0 = already in DB, -1 = error)
    Добавляет нового пользователя в таблицу в базе данных
    Возвращает результат (1 = добавлен, 0 = уже в базе, -1 = ошибка)
    '''
    if len(data) < 7:
        return -1
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            query = (
                 'INSERT OR IGNORE INTO staff '
                 '(phone_num, telegram_id, name, full_name, replacer, scheduler, dispatcher)\n'
                 'VALUES\n'
                # f'\t({",".join([str(value) for value in data])});'
                f'\t({",".join([str(value) for value in data]) + ",0"});'
            )
            cursor.execute(query)
            row = cursor.fetchall()
            return bool(row)
    except sqlite3.Error as sql_error:
        logs.message(f'Error occured while adding user to database: {sql_error}')
        return -1

def save_replacements_from_docx(file: str) -> int:
    '''
    Extracts data tables from docx document
    Returns amount of affected rows
    Извлекает таблицы из документа docx
    Возвращает количество изменённых строк
    '''
    document = Document(file)
    replaced_teachers = []
    for _, par in enumerate(document.paragraphs):
        text = par.text
        if text != '' and not text.isspace():
            replaced_teachers.append(text)
    replaced_teachers.pop(0)

    file_data = []
    for j in range(min(len(replaced_teachers), len(document.tables))):
        table = document.tables[j]
        table_data = []
        keys = []
        for col, table in enumerate(table.rows):
            text = (cell.text for cell in table.cells)
            if col == 0:
                keys = tuple(text)
                continue
            table_data.append(dict(zip(keys, text)))
        file_data.append(table_data)

    db_data = []
    keys = [ 'Класс', 'Заменяющий учитель', '№ урока', 'Кабинет' ]
    for i, table in enumerate(file_data):
        for _, row in enumerate(table):
            if not isinstance(row, dict):
                continue
            table_data = []
            for j, keys in enumerate(keys):
                v = row[keys]
                if not (j <= 1 or (j > 1 and (v.isdigit() or v == ''))):
                    table_data = None
                    break
                if v == '' or v.isspace():
                    table_data.append('NULL')
                    continue
                table_data.append(v)
            if table_data is not None:
                table_data.append(replaced_teachers[i])
                db_data.append(table_data)
    return save_replacement(db_data)

def save_replacement(data: list) -> int:
    '''
    Save replacements data to database
    Returns amount of affected rows
    Сохранение замен в базе данных
    Возвращает количество изменённых строк
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            create_query = """
            CREATE TABLE IF NOT EXISTS replacements (
              id INTEGER PRIMARY KEY,
              Class TEXT NOT NULL,
              Teacher TEXT NOT NULL,
              Lesson INTEGER NOT NULL,
              Room TEXT,
              replaced_teacher TEXT NOT NULL);
            """.strip().replace('            ', '')
            cursor.execute(create_query)
            cursor.fetchall()

            delete_query = "DELETE FROM replacements"
            cursor.execute(delete_query)

            insert_query =       "INSERT INTO replacements (Class,Teacher,Lesson,Room,replaced_teacher)"
            insert_query +=      "\n\tVALUES"
            for d in data:
                c, t, l, rt = d[0], d[1], d[2], d[4]
                r = d[3]
                if r == 'NULL':
                    r = f"'{r}'"
                insert_query += f"\n\t('{c}', '{t}', {l}, {r}, '{rt}'),"
            insert_query = insert_query.strip()[:-1] + ";"
            cursor.execute(insert_query)
            rows = cursor.fetchall()
            cursor.close()
        return len(rows)
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
            select_query = f"""
            SELECT
              Class,
              Lesson,
              Room
            FROM replacements\n
            WHERE Teacher = '{teacher}'
            ORDER BY Lesson;
            """.strip().replace('            ', '')
            cursor.execute(select_query)
            rows = cursor.fetchall()
            logs.message(rows)
        return rows
    except sqlite3.Error as error:
        logs.message(f'Can not read database: {error}', 2)
        return None
