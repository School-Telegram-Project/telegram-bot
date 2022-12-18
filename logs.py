'''
Logging module
Модуль логирования
'''

from datetime import datetime
import logging
from pathlib import Path
import sys

__all__ = (
    'setup',
    'logger'
)

def setup(logs_path='', debug = False) -> logging.Logger:
    '''
    Logging setup
    If logs_path is empty string, logs are written to console
    By default INFO is minimal level, if debug is True then DEBUG is also saved
    
    Настройка логирования
    Если logs_path - пустая строка, лог пишется в консоль
    По умолчанию минимальный уровень логирования - INFO, если debug равен True, DEBUG также сохраняется
    '''
    if logs_path == '' and sys.stdout.isatty():
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG if debug else logging.INFO)
        return

    today = datetime.now()
    file_name = f'{today.year}.{today.month}.{today.day}.txt'
    if logs_path == '':
        logs_path = Path(__file__).cwd() / 'logs'
    else:
        logs_path = Path(logs_path)
    if logs_path.is_file():
        logs_path.unlink()
    logs_path.mkdir(exist_ok=True)
    logs_path = logs_path / file_name
    logs_path.touch()

    logging.basicConfig(filename=logs_path,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d,%(levelname)s,%(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG if debug else logging.INFO)

def logger(module_name) -> logging.Logger:
    return logging.getLogger(module_name)
