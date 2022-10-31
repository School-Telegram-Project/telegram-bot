'''
File operation module
Модуль операций с файлами
'''

import sqlite3

from docx import Document

import logs

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

    db_errors = 0
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
            db_errors += save_replacement(d)
    return db_errors

def save_replacement(data):
    '''
    Save replacements data to database
    Сохранение замен в базе данных
    '''
    try:
        with sqlite3.connect('/mnt/data/Programming/telegram-bot/data') as connection:
            cursor = connection.cursor()
            insert_query =   "INSERT INTO replacements (Class,Teacher,Lesson,Room)\n\t"
            insert_query += f"VALUES ('{data[0]}','{data[1]}',{data[2]},'{data[3]}');"
            cursor.execute(insert_query)
            cursor.fetchall()
            cursor.close()
        return 0
    except sqlite3.Error as error:
        logs.message(f'Can not save data to database: {error}', 2)
        return 1

def read_replacements(teacher):
    '''
    Reads data from replacements
    Чтение данных из базы замен
    '''
    try:
        with sqlite3.connect('/mnt/data/Programming/telegram-bot/data') as connection:
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