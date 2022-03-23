"""1. Продолжая задачу логирования, реализовать декоратор @log, фиксирующий обращение к декорируемой функции. Он сохраняет ее имя и аргументы.
2. В декораторе @log реализовать фиксацию функции, из которой была вызвана декорированная. Если имеется такой код:
@log
def func_z():
 pass

def main():
 func_z()
...в логе должна быть отражена информация:
"<дата-время> Функция func_z() вызвана из функции main"""


"""Скрипт для быстрой проверки взаимодействия сервера и клиента"""
import subprocess
import sys

server = subprocess.Popen([sys.executable, "server_script.py", '-p', '8079', '-a', '127.0.0.1'])
client = subprocess.Popen([sys.executable, "client_script.py", '127.0.0.1', '8079'])
server.communicate()
client.communicate()