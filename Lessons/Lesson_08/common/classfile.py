import json
import logging
import os
import sys
import threading
import time
from pprint import pprint
from socket import socket, AF_INET, SOCK_STREAM
import argparse
from select import select
from .errors import ReqFieldMissingError, ServerError, IncorrectDataRecivedError

from .decorators import Log
from .variables import ENCODING, MAX_PACKAGE_LENGTH, DEFAULT_IP_ADDRESS, \
    ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, DEFAULT_USERNAME, MESSAGE_TEXT, MESSAGE, SENDER, DESTINATION, \
    EXIT, FAQ

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
        self.client_names = dict()

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

            # без этой проверки на то, что последний сокет закрыт,
            # при закрытии всех клиентских консолей сервер будет
            # висеть в бесконечной ошибке
            if self.ready_to_input:
                if len(self.ready_to_input) == 1 and self.ready_to_input[0].fileno() == -1:
                    self.ready_to_input.clear()
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
                print(f'Ошибка {e} Клиент {non_empty_client} отключился от сервера.')
                self.logger.warning(f'Клиент {non_empty_client} отключился от сервера.')
                if non_empty_client in self.client_list:
                    self.client_list.remove(non_empty_client)

            if self.messages_list:
                for msg in self.messages_list:
                    try:
                        self.mailing_messages(msg)
                    except Exception:
                        if msg[DESTINATION] in self.client_names:
                            self.logger.info(f'Отсутствует связь с клиентом {msg[DESTINATION]}')
                            self.client_list.remove(self.client_names[msg[DESTINATION]])
                            del self.client_names[msg[DESTINATION]]
                self.messages_list.clear()

    def mailing_messages(self, message):
        """Sends messages to clients who receive messages or sends a rejection to the client
         if the recipient does not exist"""

        if message[DESTINATION] in self.client_names and \
                self.client_names[message[DESTINATION]] in self.ready_to_output:
            self.send_msg(message, current_socket=self.client_names[message[DESTINATION]])
            self.logger.info(f'Пользователь {message[SENDER]} отправил сообщение для {message[DESTINATION]}.')
            return
        elif message[DESTINATION] in self.client_names \
                and self.client_names[message[DESTINATION]] not in self.ready_to_output:
            raise ConnectionError
        else:
            message_to_sender = {
                ACTION: MESSAGE,
                SENDER: 'Server',
                DESTINATION: message[SENDER],
                TIME: time.time(),
                MESSAGE_TEXT: 'Такого пользователя не существует, выберите другого получателя.'
            }
            self.send_msg(message_to_sender, current_socket=self.client_names[message[SENDER]])
            self.logger.error(f'Пользователя {message[DESTINATION]} не существует')

    def send_reply(self, message, client):
        """Accepts a client message and forms a response"""

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message:
            response = {RESPONSE: 200}

            if message[USER][ACCOUNT_NAME] not in self.client_names.keys():
                self.client_names[message[USER][ACCOUNT_NAME]] = client
            else:
                response = {
                    RESPONSE: 400,
                    ERROR: 'Имя пользователя уже занято.'
                }
                self.send_msg(response, current_socket=client)
                self.client_list.remove(client)
                client.close()

        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages_list.append(message)
            return
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.client_list.remove(self.client_names[message[ACCOUNT_NAME]])
            self.client_names[message[ACCOUNT_NAME]].close()
            del self.client_names[message[ACCOUNT_NAME]]
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

    def __init__(self):
        App.__init__(self)
        self.logger = logging.getLogger('app.client_script')
        self.parser = argparse.ArgumentParser()
        self.client_mode = ''
        self.server_address = ''
        self.server_port = ''
        self.client_name = ''

    def client_parse_args(self):
        """Retrieves port, address and mode from command line arguments"""

        self.parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        self.parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        self.parser.add_argument('-n', '--name', default=None, nargs='?')

        namespace = self.parser.parse_args(sys.argv[1:])
        self.server_address, self.server_port = self.validate_addr_port(namespace)
        self.client_name = self.validate_name(namespace)

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

    def validate_name(self, namespace):
        """Client name validation"""

        username = namespace.name
        if not username:
            while True:
                username = input('Введите ваше имя или никнейм: ')
                if username.isdigit():
                    print('Никнейм может состоять из букв или букв и цифр, '
                          'никнеймы, состоящие только из цифр, недопустимы.')
                elif len(username) <= 3:
                    print('Слишком короткое имя или никнейм, допустимы варианты длиной от 4 символов')
                else:
                    return username
        return username

    def client_connect(self):
        """Establishes a connection to the server"""

        self.client_parse_args()
        try:
            self.socket.connect((self.server_address, self.server_port))
            self.logger.debug(f'Успешное подключение к удаленному сокету '
                              f'по адресу {self.server_address}, порт {self.server_port}, '
                              f'имя клиента {self.client_name}')
        except OSError as e:
            self.logger.critical(f'Произошла критическая ошибка: {e.strerror}. '
                                 f'Клиент завершил работу.')
            sys.exit(1)
        print(f'Добро пожаловать! Ваш никнейм - {self.client_name}.')

    def send_a_message(self, action=PRESENCE):
        """Sends a message to the server"""

        msg_to_server = {
            ACTION: action,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
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
                    msg = 'Соединение с сервером установлено'
                    print(msg)
                    self.logger.info(msg + f' , клиент - {self.client_name}')
                    return
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

        to_user = input('Введите никнейм получателя сообщения: ')
        user_message = input('Введите ваше сообщение: ')

        message_to_other_client = {
            ACTION: MESSAGE,
            SENDER: self.client_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: user_message
        }
        try:
            self.send_msg(message_to_other_client)
            self.logger.info(f'Отправлено сообщение для пользователя {to_user}')
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            self.logger.error(f'Разрыв соединения с {self.server_address}.')
            sys.exit(1)

    def send_or_listen(self):
        """Determines the client's operating mode and forms its actions"""

        receiver = threading.Thread(target=self.message_from_server)
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=self.requesting_commands)
        user_interface.daemon = True
        user_interface.start()
        self.logger.debug(f'Запуск потоков приема и отправки сообщений для клиента {self.client_name}')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            self.logger.warning(f'Потоковый прием или отправка сообщений клиента {self.client_name} завершены.')
            break

    def message_from_server(self):
        """Processes messages from the server and displays them on the terminal screen"""

        while True:
            try:
                message = self.get_message()
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.client_name:
                    msg = f'Пользователь {message[SENDER]} ' \
                          f'отправил вам сообщение: \n{message[MESSAGE_TEXT]}\nВведите вашу команду: '
                    print(f'\n{msg}')
                    self.logger.info(msg)

                else:
                    self.logger.error(f'Ответ сервера в сообщении {message} содержит ошибку')
            except IncorrectDataRecivedError:
                self.logger.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                self.logger.critical(f'Потеряно соединение с сервером.')
                break

    def requesting_commands(self):
        """Requesting commands from the user"""

        self.faq()
        welcome_text = 'После выполнения каждой команды наш ' \
                       'консольный менеджер будет ожидать ввода вами ' \
                       'следующей команды.\nВведите первую команду: '
        while True:
            user_command = input(welcome_text)
            commands = {'ms': self.create_message, 'help': self.faq, 'q': self.say_goodbye_and_exit}
            welcome_text = 'Введите следующую команду: '
            try:
                required_action = commands.get(user_command)
                required_action()
                if user_command == 'q':
                    time.sleep(1)
                    break
            except TypeError:
                print('Введенной команды не существует, введите help для ознакомления с существующими командами')

    def faq(self):
        """Prints a dictionary of valid commands"""

        print('Для работы используйте команды:')
        pprint(FAQ)

    def say_goodbye_and_exit(self):
        """Sends a client shutdown command to the server"""

        msg = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }
        self.send_msg(msg)
        print('Завершение работы. До свидания!')
        self.logger.info(f'Завершение работы {self.client_name} по его запросу.')
