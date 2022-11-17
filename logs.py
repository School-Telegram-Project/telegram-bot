'''
Logging module
Модуль логирования
'''

import logging
import sys
from pathlib import PurePath
import os

def setup(path='logs/latest.txt'):
    '''
    Logging setup
    Настройка логирования
    '''
    # Logs path was passed as argument
    if path != '':
        logging.basicConfig(filename=path,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d,%(name)s,%(levelname)s,%(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
    # Running in shell with output interface
    elif sys.stdout.isatty():
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
    # Default behaviour
    else:
        logging.basicConfig(filename=str(PurePath(__file__).with_name('logs/latest.txt')),
                            filemode='a',
                            format='%(asctime)s,%(msecs)d,%(name)s,%(levelname)s,%(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

def message(text, level=0):
    '''
    Send message to logs
    Отправить сообщение в логи
    '''
    log_level = [logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][level]
    logging.log(log_level, text)
