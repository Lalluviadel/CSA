import json
import logging
import os
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM
import argparse
from select import select
from .errors import ReqFieldMissingError, ServerError

from .decorators import Log
from .variables import ENCODING, MAX_PACKAGE_LENGTH, DEFAULT_IP_ADDRESS, \
    ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, DEFAULT_USERNAME, MESSAGE_TEXT, MESSAGE, SENDER

sys.path.append(os.path.join(os.getcwd(), '..'))
from project_logging.configs import client_log_config, server_log_config

class App:
    """Parent app class"""

    def __init__(self, current_socket=None):
        self.socket = current_socket if current_socket else socket(AF_INET, SOCK_STREAM)

    def send_msg(self, message, current_socket=None):
        """Sends a message in bytes form using a socket"""

        current_socket = current_socket if current_socket else self.socket
        json_msg = json.dumps(message)
        encoded_msg = json_msg.encode(ENCODING)
        current_socket.send(encoded_msg)

    def get_message(self, current_socket=None):
        """Receives data byte and transforms it into a dictionary"""

        current_socket = current_socket if current_socket else self.socket
        encoded_response = current_socket.recv(MAX_PACKAGE_LENGTH)
        if isinstance(encoded_response, bytes):
            json_response = encoded_response.decode(ENCODING)
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError


@Log()
class Server(App):
    """Child class for creating a server"""

    def __init__(self, address, port):
        App.__init__(self)
        self.address = address
        self.port = port
        self.logger = logging.getLogger('app.server_script')
        self.parser = argparse.ArgumentParser()
        self.messages_list = []
        self.client_list = []
        self.ready_to_input = []
        self.ready_to_output = []
        self.error_data = []

    def server_parse_args(self):
        """Retrieves port and address from command line arguments"""

        self.parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        self.parser.add_argument('-a', default='', nargs='?')
        namespace = self.parser.parse_args(sys.argv[1:])
        listen_port, listen_addr = self.validate_port(namespace), self.validate_address(namespace)
        self.logger.debug(f'Сервер распарсил адрес {listen_addr} и порт {listen_port}')
        return listen_port, listen_addr

    def validate_port(self, namespase_obj):
        """Port number validation"""
        try:
            listen_port = namespase_obj.p
            if listen_port < 1024 or listen_port > 65535:
                raise ValueError
            self.logger.debug(f'Успешная валидация порта {listen_port}')
            return listen_port
        except AttributeError:
            self.logger.critical(f'Ошибка валидации порта. Парсер аргументов командной'
                                 f'строки не обнаружил атрибута \'p\' '
                                 f'Завершение работы.')
            sys.exit(1)
        except ValueError:
            self.logger.critical(f'Ошибка валидации порта. Число для порта не может '
                                 f'быть меньше 1024 или больше 65535. Завершение работы.')
            sys.exit(1)

    def validate_address(self, namespase_obj):
        """Port address validation"""
        try:
            listen_address = namespase_obj.a
            self.logger.debug(f'Успешная валидация адреса {listen_address}')
            return listen_address
        except AttributeError:
            self.logger.critical(f'Ошибка валидации адреса. Парсер аргументов командной'
                                 f'строки не обнаружил атрибута \'a\' '
                                 f'Завершение работы.')
            sys.exit(1)

    def bind_and_listen(self):
        """Binding a socket to port and address and listening for a connection"""
        listen_port, listen_address = self.server_parse_args()
        try:
            self.socket.bind((listen_address, listen_port))
            self.logger.debug(f'Привязан сокет к адресу {(listen_address, listen_port)}')
        except OSError as e:
            self.logger.critical(f'Произошла критическая ошибка: {e.strerror}. Сервер завершил работу.')
            sys.exit(1)

        self.socket.settimeout(0.5)
        self.socket.listen(MAX_CONNECTIONS)
        self.logger.debug('Сервер прослушивает соединение. Ожидание клиентов.')
        print(f'Сервер готов к работе. Настройки адреса: {listen_address} и порта: {listen_port}')

    def accept_and_exchange(self):
        """Accepts a connection request and initiates a message exchange"""
        while True:
            try:
                client, client_address = self.socket.accept()
                self.logger.info(f'Успешное соединение с адресом {client_address}')
                self.client_list.append(client)
                print(f'В список клиентов добавлен клиент {client.getpeername()}')
            except OSError:
                pass

            try:
                if self.client_list:
                    self.ready_to_input, self.ready_to_output, self.error_data = select(self.client_list,
                                                                                        self.client_list, [], 0)
            except OSError:
                pass
            if self.ready_to_input:
                self.receiving_msg_and_reply()

    def receiving_msg_and_reply(self):
        """Receives messages from outgoing clients, sends a response"""
        for non_empty_client in self.ready_to_input:
            try:
                msg_from_client = self.get_message(current_socket=non_empty_client)
                self.logger.info(f'Принято сообщение от клиента {non_empty_client}')
                self.send_reply(msg_from_client, non_empty_client)
                self.logger.info(f'Отправлен ответ сервера клиенту {non_empty_client}')
            except Exception as e:
                print(f'Ошибка {e} Клиент {non_empty_client.getpeername()} отключился от сервера.')
                self.logger.warning(f'Клиент {non_empty_client.getpeername()} отключился от сервера.')
                self.client_list.remove(non_empty_client)

            if self.messages_list and self.ready_to_output:
                self.mailing_messages()

    def mailing_messages(self):
        """Sends messages to clients who receive messages"""
        message = {
            ACTION: MESSAGE,
            SENDER: self.messages_list[0][0],
            TIME: time.time(),
            MESSAGE_TEXT: self.messages_list[0][1]
        }
        del self.messages_list[0]
        for waiting_client in self.ready_to_output:
            try:
                self.send_msg(message, current_socket=waiting_client)
                self.logger.info(f'Сервер отослал ответ {message} клиенту {waiting_client}')
            except Exception:
                self.logger.info(f'Потеряно соединение сервера с клиентом {waiting_client.getpeername()}')
                self.client_list.remove(waiting_client)

    def send_reply(self, message, client):
        """Accepts a client message and forms a response"""
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
            response = {RESPONSE: 200}
        elif ACTION in message and message[ACTION] == MESSAGE and \
                TIME in message and MESSAGE_TEXT in message:
            self.messages_list.append((message[ACCOUNT_NAME], message[MESSAGE_TEXT]))
            return
        else:
            response = {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
        self.send_msg(response, current_socket=client)


@Log()
class Client(App):
    """Child class for creating a client"""

    def __init__(self, account_name=DEFAULT_USERNAME):
        App.__init__(self)
        self.account_name = account_name
        self.logger = logging.getLogger('app.client_script')
        self.parser = argparse.ArgumentParser()
        self.client_mode = ''
        self.server_address = ''
        self.server_port = ''

    def client_parse_args(self):
        """Retrieves port, address and mode from command line arguments"""
        self.parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        self.parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        self.parser.add_argument('-m', '--mode', default='listen', nargs='?')
        namespace = self.parser.parse_args(sys.argv[1:])
        self.server_address, self.server_port = self.validate_addr_port(namespace)
        self.client_mode = self.validate_mode(namespace)

    def validate_addr_port(self, namespace):
        """Port address and number validation"""

        try:
            server_address, server_port = namespace.addr, namespace.port
            if server_port < 1024 or server_port > 65535:
                raise ValueError
            self.logger.debug(f'Успешная валидация набора адрес и порт: {server_address, server_port}')
            return server_address, server_port
        except AttributeError:
            self.logger.critical(f'Ошибка валидации порта. Парсер аргументов командной'
                                 f'строки не обнаружил атрибутов \'addr\' или \'port\' '
                                 f'Завершение работы клиента.')
            sys.exit(1)
        except ValueError:
            self.logger.critical(f'Ошибка валидации порта. Число для порта не может '
                                 f'быть меньше 1024 или больше 65535. Завершение работы клиента.')
            sys.exit(1)

    def validate_mode(self, namespace):
        """Client mode validation"""

        mode = namespace.mode
        if mode not in ('listen', 'send'):
            self.logger.critical(f'Режим {mode} не распознан. Допустимые варианты: \'listen\' , \'send\'. '
                                 f'Завершение работы клиента.')
            sys.exit(1)
        return mode

    def client_connect(self):
        """Establishes a connection to the server"""

        self.client_parse_args()
        try:
            self.socket.connect((self.server_address, self.server_port))
            self.logger.debug(f'Успешное подключение к удаленному сокету '
                              f'по адресу {self.server_address}, порт {self.server_port}')
        except OSError as e:
            self.logger.critical(f'Произошла критическая ошибка: {e.strerror}. '
                                 f'Клиент завершил работу.')
            sys.exit(1)

    def send_a_message(self, action=PRESENCE):
        """Sends a message to the server"""

        msg_to_server = {
            ACTION: action,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.account_name
            }
        }
        self.send_msg(msg_to_server)
        self.logger.info(f'Отправлено сообщение серверу.')

    def response_read(self):
        """Receiving the server response and its output"""

        msg = self.get_message()
        self.logger.info(f'Получено сообщение от сервера {msg}')
        try:
            if RESPONSE in msg:
                if msg[RESPONSE] == 200:
                    return '200 : OK'
                elif msg[RESPONSE] == 400:
                    raise ServerError(f'400 : {msg[ERROR]}')
            raise ReqFieldMissingError(RESPONSE)
        except ValueError:
            self.logger.critical(f'Ошибка в ответе сервера. Клиент завершил работу')
            sys.exit(1)
        except ReqFieldMissingError as missing_error:
            self.logger.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)
        except ConnectionRefusedError:
            self.logger.critical('Ошибка подключения к серверу: сервер отверг запрос на подключение')
            sys.exit(1)

    def create_message(self):
        """Receives a message from the user and forms it for sending"""

        user_message = input('Введите сообщение для отправки или \'exit\' для завершения работы: ')
        if user_message == 'exit':
            self.socket.close()
            self.logger.info('Завершение работы клиента по команде пользователя.')
            sys.exit(0)
        message_to_clients = {
            ACTION: MESSAGE,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
            MESSAGE_TEXT: user_message
        }
        return message_to_clients

    def send_or_listen(self):
        """Determines the client's operating mode and forms its actions"""

        if self.client_mode == 'send':
            print('Режим работы - отправка сообщений.')
        else:
            print('Режим работы - приём сообщений.')
        while True:
            if self.client_mode == 'send':
                try:
                    self.send_msg(self.create_message())
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    self.logger.error(f'Разрыв соединения с {self.server_address}.')
                    sys.exit(1)

            if self.client_mode == 'listen':
                try:
                    self.message_from_server(self.get_message())
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    self.logger.error(f'Разрыв соединения с {self.server_address}.')
                    sys.exit(1)

    def message_from_server(self, message):
        """Processes messages from the server and displays them on the terminal screen"""
        if ACTION in message and message[ACTION] == MESSAGE and \
                SENDER in message and MESSAGE_TEXT in message:
            print(f'Получено сообщение от пользователя '
                  f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            self.logger.info(f'Получено сообщение от пользователя '
                             f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        else:
            self.logger.error(f'Сервер передал некорректное сообщение: {message}')
