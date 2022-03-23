"""Скрипт для быстрой проверки взаимодействия сервера и клиента"""
import subprocess
import sys

server = subprocess.Popen([sys.executable, "server_script.py", '-p', '8079', '-a', '127.0.0.1'])
client = subprocess.Popen([sys.executable, "client_script.py", '127.0.0.1', '8079'])
server.communicate()
client.communicate()