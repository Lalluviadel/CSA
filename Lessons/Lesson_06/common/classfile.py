import json
import logging
import os
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM

from .decorators import Log
from .variables import ENCODING, MAX_PACKAGE_LENGTH, DEFAULT_IP_ADDRESS, \
    ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, DEFAULT_USERNAME

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

    def validate_port(self, listen_port=DEFAULT_PORT):
        """Port number validation"""
        try:
            if '-p' in sys.argv:
                listen_port = int(sys.argv[sys.argv.index('-p') + 1])
                if listen_port < 1024 or listen_port > 65535:
                    raise ValueError
            self.logger.debug(f'Успешная валидация порта {listen_port}')
            return listen_port
        except IndexError:
            self.logger.critical(f'Ошибка валидации порта. После параметра -\'p\' '
                                 f'необходимо указать номер порта. Завершение работы.')
            sys.exit(1)
        except ValueError:
            self.logger.critical(f'Ошибка валидации порта. Число для порта не может '
                                 f'быть меньше 1024 или больше 65535. Завершение работы.')
            sys.exit(1)

    def validate_address(self, listen_address=''):
        """Port address validation"""
        try:
            if '-a' in sys.argv:
                listen_address = sys.argv[sys.argv.index('-a') + 1]
            self.logger.debug(f'Успешная валидация адреса {listen_address}')
            return listen_address
        except IndexError:
            self.logger.critical(f'Ошибка валидации адреса. После параметра \'a\' '
                                 f'необходимо указать адрес, который будет слушать сервер. '
                                 f'Завершение работы.')
            sys.exit(1)

    def bind_and_listen(self):
        """Binding a socket to port and address and listening for a connection"""

        listen_port = self.validate_port()
        listen_address = self.validate_address()
        try:
            self.socket.bind((listen_address, listen_port))
            self.logger.debug(f'Привязан сокет к адресу {(listen_address, listen_port)}')
        except OSError as e:
            self.logger.critical(f'Произошла критическая ошибка: {e.strerror}. Сервер завершил работу.')
            sys.exit(1)
        self.socket.listen(MAX_CONNECTIONS)
        self.logger.debug('Сервер прослушивает соединение. Ожидание клиента.')

    def accept_and_exchange(self):
        """Accepts a connection request and initiates a message exchange"""
        while True:
            client, client_address = self.socket.accept()
            try:
                msg_from_client = self.get_message(current_socket=client)
                self.logger.info('Принято сообщение от клиента.')
                self.send_reply(msg_from_client, client)
                self.logger.info('Отправлен ответ сервера клиенту. Сессия клиента завершена.')
            except (ValueError, json.JSONDecodeError):
                client.close()
                self.logger.error('Принято некорректное сообщение от клиента. '
                                  'Сессия клиента завершена.')
            except Exception:
                logging.exception('Критическая ошибка в цикле обмена сообщениями')

    def send_reply(self, message, client):
        """Accepts a client message and forms a response"""
        if ACTION in message \
                and message[ACTION] == PRESENCE \
                and TIME in message \
                and USER in message \
                and message[USER][ACCOUNT_NAME] == DEFAULT_USERNAME:

            response = {RESPONSE: 200}
        else:
            response = {
                RESPONSE: 400,
                ERROR: 'Bad Request'
            }
        self.send_msg(response, current_socket=client)
        client.close()


@Log()
class Client(App):
    """Child class for creating a client"""

    def __init__(self, account_name=DEFAULT_USERNAME):
        App.__init__(self)
        self.account_name = account_name
        self.logger = logging.getLogger('app.client_script')

    def validate_addr_port(self, server_address=DEFAULT_IP_ADDRESS, server_port=DEFAULT_PORT):
        """Port address and number validation"""
        try:
            server_address, server_port = sys.argv[1], int(sys.argv[2])
            if server_port < 1024 or server_port > 65535:
                raise ValueError
            self.logger.debug(f'Успешная валидация набора адрес и порт: {server_address, server_port}')
            return server_address, server_port
        except IndexError:
            self.logger.warning(f'Ошибка во введенных данных порта и/или IP-адреса или их отсутствие.\n'
                                f'Будут применены дефолтные значения: адрес - {server_address},'
                                f'порт - {server_port}')
            return server_address, server_port
        except ValueError:
            self.logger.critical(f'Ошибка валидации порта. Число для порта не может '
                                 f'быть меньше 1024 или больше 65535. Завершение работы.')
            sys.exit(1)

    def client_connect(self):
        """Establishes a connection to the server"""

        server_address, server_port = self.validate_addr_port()
        try:
            self.socket.connect((server_address, server_port))
            self.logger.debug(f'Успешное подключение к удаленному сокету '
                              f'по адресу {server_address}, порт {server_port}')
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
        try:
            if RESPONSE in msg:
                answer = '200 : OK' if msg[RESPONSE] == 200 else f'400 : {msg[ERROR]}'
                self.logger.info(f'Получен ответ сервера.')
                return answer
            raise ValueError
        except ValueError:
            self.logger.critical(f'Ошибка в ответе, полученном от сервера, '
                                 f'клиентское приложение будет закрыто.')
            sys.exit(1)
