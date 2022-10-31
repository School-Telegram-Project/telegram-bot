'''
Logging module
Модуль логирования
'''

import logging
import sys

def setup(file=''):
    '''
    Logging setup
    Настройка логирования
    '''
    if file != '':
        logging.basicConfig(filename=file,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d,%(name)s,%(levelname)s,%(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
    elif sys.stdout.isatty():
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

def message(text, level=0):
    '''
    Send message to logs
    Отправить сообщение в логи
    '''
    log_level = [logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL][level]
    logging.log(log_level, text)
