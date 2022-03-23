"""Для проекта «Мессенджер» реализовать логирование с использованием модуля logging:

1. В директории проекта создать каталог log, в котором для клиентской и серверной
сторон в отдельных модулях формата client_log_config.py и server_log_config.py
создать логгеры;
2. В каждом модуле выполнить настройку соответствующего логгера по следующему
алгоритму:
- Создание именованного логгера;
- Сообщения лога должны иметь следующий формат:
"<дата-время> <уровеньважности> <имямодуля> <сообщение>";
- Журналирование должно производиться в лог-файл;
- На стороне сервера необходимо настроить ежедневную ротацию лог-файлов.

3. Реализовать применение созданных логгеров для решения двух задач:
- Журналирование обработки исключений try/except. Вместо функции print()
использовать журналирование и обеспечить вывод служебных сообщений в лог-файл;
- Журналирование функций, исполняемых на серверной и клиентской сторонах при
работе мессенджера."""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

sys.path.append('../../')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, '../log/server.log')
logger = logging.getLogger('app.server_script')
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s ")
file_handler = TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='midnight')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
