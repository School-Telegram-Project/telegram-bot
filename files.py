'''
File operation module
Модуль операций с файлами
'''

import sqlite3
#import openpyxl as xl

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
            select_query =   "SELECT DISTINCT\n"
            select_query +=  "\tname,\n"
            select_query +=  "\tfull_name,\n"
            select_query +=  "\treplacer,\n"
            select_query +=  "\tdispatcher,\n"
            select_query +=  "\tscheduler\n"
            select_query +=  "FROM staff\n"
            select_query += f"WHERE telegram_id = '{telegram_id}';\n"
            cursor.execute(select_query)
            row = cursor.fetchall()
        if len(row) < 1:
            logs.message(f'User {telegram_id} was not found')
            return None
        return row[0]
    except sqlite3.Error as error:
        logs.message(f'Error occured while searching for user {telegram_id}: {error}')

# TODO: Timetables updates (Обновления расписаний)
# def database_update(file):
#     try:
#         with sqlite3.connect('data/timetables') as connection:
#             wb = xl.load_workbook(file)
#             sheet = wb.active
#             cursor = connection.cursor()
#            
#         return 0
#     except sqlite3.Error as error:
#         return -1

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
    for i in range(min(len(replaced_teachers), len(document.tables))):
        table = document.tables[i]
        d = []
        k = []
        r_d = []
        for col, row in enumerate(table.rows):
            text = (cell.text for cell in row.cells)
            if col == 0:
                k = tuple(text)
                continue
            r_d = dict(zip(k, text))
            d.append(r_d)
        data.append(d)

    data = []
    keys = [ 'Класс', 'Заменяющий учитель', '№ урока', 'Кабинет' ]
    for i, row in enumerate(data):
        for r in row:
            d = []
            for k in keys:
                v = r[k]
                if v == '' or v.isspace():
                    d.append('NULL')
                    continue
                d.append(v)
            data.append(d)
    return save_replacement(data)

def save_replacement(data):
    '''
    Save replacements data to database
    Сохранение замен в базе данных
    '''
    try:
        with sqlite3.connect('data') as connection:
            cursor = connection.cursor()
            create_query =  "CREATE TABLE IF NOT EXISTS replacements (\n"
            create_query += "\tid INTEGER PRIMARY KEY,\n"
            create_query += "\tClass TEXT NOT NULL,\n"
            create_query += "\tTeacher TEXT NOT NULL,\n"
            create_query += "\tLesson INTEGER NOT NULL,\n"
            create_query += "\tRoom TEXT\n);"
            cursor.execute(create_query)
            cursor.fetchall()
            insert_query =       "INSERT INTO replacements (Class,Teacher,Lesson,Room)\n\t"

            for d in data:
                insert_query += f"VALUES ('{d[0]}','{d[1]}',{d[2]},'{d[3]}');"
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
            select_query =   "SELECT\n"
            select_query +=  "\tClass,\n"
            select_query +=  "\tLesson,\n"
            select_query +=  "\tRoom\n"
            select_query +=  "FROM replacements\n"
            select_query += f"WHERE Teacher = '{teacher}'\n"
            select_query +=  "ORDER BY Lesson;"
            cursor.execute(select_query)
            rows = cursor.fetchall()
            logs.message(rows)
        return rows
    except sqlite3.Error as error:
        logs.message(f'Can not read database: {error}', 2)
        return None
