'''
File operation module
Модуль операций с файлами
'''

import sqlite3

from docx import Document

import logs


def find_user(telegram_id):
    '''
    Finds user in database by Telegram ID
    Находит пользователя в базе данных по ID Telegram'а
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            select_query = f"""
            SELECT DISTINCT
              name,
              full_name,
              replacer,
              dispatcher,
              scheduler
            FROM staff
            WHERE telegram_id = '{telegram_id}';
            """.strip().replace('            ', '')
            cursor.execute(select_query)
            row = cursor.fetchall()
        if len(row) < 1:
            logs.message(f'User {telegram_id} was not found')
            return None
        return row[0]
    except sqlite3.Error as error:
        logs.message(f'Error occured while searching for user {telegram_id}: {error}')

def save_replacements_from_docx(file):
    '''
    Extracts data tables from docx document
    Извлекает таблицы из документа docx
    '''
    document = Document(file)
    replaced_teachers = []
    for _, par in enumerate(document.paragraphs):
        text = par.text
        if text != '' and not text.isspace():
            replaced_teachers.append(text)
    replaced_teachers.pop(0)

    data = []
    for j in range(min(len(replaced_teachers), len(document.tables))):
        table = document.tables[j]
        d = []
        k = []
        r = []
        for col, table in enumerate(table.rows):
            text = (cell.text for cell in table.cells)
            if col == 0:
                k = tuple(text)
                continue
            r = dict(zip(k, text))
            d.append(r)
        data.append(d)

    db_data = []
    keys = [ 'Класс', 'Заменяющий учитель', '№ урока', 'Кабинет' ]
    for i, table in enumerate(data):
        for _, row in enumerate(table):
            if not isinstance(row, dict):
                continue
            d = []
            for j, k in enumerate(keys):
                v = row[k]
                if not (j <= 1 or (j > 1 and (v.isdigit() or v == ''))):
                    d = None
                    break
                if v == '' or v.isspace():
                    d.append('NULL')
                    continue
                d.append(v)
            if d is not None:
                d.append(replaced_teachers[i])
                db_data.append(d)
    return save_replacement(db_data)

def save_replacement(data):
    '''
    Save replacements data to database
    Сохранение замен в базе данных
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

def read_replacements(teacher):
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
