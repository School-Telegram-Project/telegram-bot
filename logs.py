'''
Logging module
Модуль логирования
'''

from datetime import datetime
import logging
from pathlib import Path
import sys

def setup(logs_path='') -> None:
    '''
    Logging setup
    Настройка логирования
    '''
    if logs_path == '' and sys.stdout.isatty():
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
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
                        level=logging.INFO)

def message(text: str, level=0) -> None:
    '''
    Send message to logs
    Отправить сообщение в логи
    level: 0 - INFO, 1 - WARNING, 2 - ERROR, 3 - CRITICAL
    '''
    log_level = [logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][level]
    logging.log(log_level, text)
