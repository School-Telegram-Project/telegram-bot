'''
Script for deploying the program

Скрипт для развёртки программы
'''

import sqlite3 as sql
from pathlib import Path
from sys import argv
from configparser import ConfigParser

try:
    import telegram
except ModuleNotFoundError:
    print(
        'Для работы программы необходимо установить библиотеку для\n'
        'взаимодействия с API Telegram\'а: pip install python-telegram-bot'
    )
    exit(1)
telegram = None

if '--no-git' in argv:
    argv.remove('--no-git')
else:
    try:
        import git
    except ModuleNotFoundError:
        print(
            'Скрипт использует GitPython для загрузки из репозитория.\n'
            'Загрузите программу из репозитория вручную\n'
            'и запустите скрипт с --no-git или установите git\n'
            'и загрузите библиотеку GitPython с помощью команды\n'
            'pip install GitPython'
        )
        exit(1)


def main() -> None:
    destination = (
        Path(argv[1])
        if len(argv) > 1 else
        Path(argv[0]).parent
    ).resolve()
    if git:
        try:
            git.Git(destination).clone(
                'http://github.com/School-Telegram-Project/telegram-bot.git'
            )
        except git.exc.GitCommandError:
            print(
                'Папка существует и не пуста; '
                'удалите папку и запустите скрипт снова'
                )
    destination = destination/'telegram-bot'
    print(str(destination))
    if (not (settings := destination/'settings.ini').exists()
        or (input('Файл настроек уже существует. Перезаписать его? (д/н)\n')
             .strip().lower()) in ('да', 'д', 'yes', 'y')
        ):
        configparser = ConfigParser()
        configparser.add_section('telegram-replacements-bot')
        configparser['telegram-replacements-bot'].update({
            'token': input(
                'Введите токен Telegram-бота (https://core.telegram.org/bots#how-do-i-create-a-bot):\n'
                ).strip(),
            'logs_folder': 'Console',
            'locales': './locales',
            'language': 'ru',
            'save_interval': '60'
        })
        with settings.open(mode='w', encoding='UTF-8') as fp:
            configparser.write(fp)

    if (not (db := destination/'database').exists()
        or (input('База данных уже существует. Перезаписать её? (д/н)\n')
             .strip().lower()) in ('да', 'д', 'yes', 'y')
        ):
        db.unlink(missing_ok=True)
        db.touch()
        with sql.connect(db) as connection:
            cursor = connection.cursor()
            cursor.executescript(
                "BEGIN;\n"
                "CREATE TABLE staff (\n"
                "    phone_num INTEGER,\n"
                "    telegram_id INTEGER,\n"
                "    name TEXT,\n"
                "    replacer INTEGER DEFAULT (1),\n"
                "    scheduler INTEGER DEFAULT (0),\n"
                "    dispatcher INTEGER DEFAULT (0),\n"
                "    admin INTEGER DEFAULT (0)\n"
                ");\n"
                "\n"
                "CREATE UNIQUE INDEX staff_phone_num_IDX ON staff (phone_num);"
                "\n"
                "\n"
                "CREATE TABLE replacements (\n"
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

if __name__ == '__main__':
    main()
