import json
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM

from .variables import ENCODING, MAX_PACKAGE_LENGTH, DEFAULT_IP_ADDRESS, \
    ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, USER, ERROR, \
    DEFAULT_PORT, DEFAULT_USERNAME


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


class Server(App):
    """Child class for creating a server"""

    def __init__(self, address, port):
        App.__init__(self)
        self.address = address
        self.port = port

    @staticmethod
    def validate_port(listen_port=DEFAULT_PORT):
        """Port number validation"""

        try:
            if '-p' in sys.argv:
                listen_port = int(sys.argv[sys.argv.index('-p') + 1])
                if listen_port < 1024 or listen_port > 65535:
                    raise ValueError
            return listen_port
        except IndexError:
            print('После параметра -\'p\' необходимо указать номер порта.')
            sys.exit(1)
        except ValueError:
            print('Число для порта не может быть меньше 1024 или больше 65535.')
            sys.exit(1)

    @staticmethod
    def validate_address(listen_address=''):
        """Port address validation"""

        try:
            if '-a' in sys.argv:
                listen_address = sys.argv[sys.argv.index('-a') + 1]
            return listen_address
        except IndexError:
            print(
                'После параметра \'a\' необходимо указать адрес, который будет слушать сервер.')
            sys.exit(1)

    def bind_and_listen(self):
        """Binding a socket to port and address and listening for a connection"""

        listen_port = self.validate_port()
        listen_address = self.validate_address()
        try:
            self.socket.bind((listen_address, listen_port))
        except OSError as e:
            print(e.strerror)
            sys.exit(1)
        self.socket.listen(MAX_CONNECTIONS)
        print('Сервер готов. Ожидание клиента.')

    def accept_and_exchange(self):
        """Accepts a connection request and initiates a message exchange"""

        while True:
            client, client_address = self.socket.accept()
            try:
                msg_from_client = self.get_message(current_socket=client)
                self.send_reply(msg_from_client, client)
            except (ValueError, json.JSONDecodeError):
                print('Принято некорректное сообщение от клиента.')
                client.close()

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


class Client(App):
    """Child class for creating a client"""

    def __init__(self, account_name=DEFAULT_USERNAME):
        App.__init__(self)
        self.account_name = account_name

    @staticmethod
    def validate_addr_port(server_address=DEFAULT_IP_ADDRESS, server_port=DEFAULT_PORT):
        """Port address and number validation"""

        try:
            server_address, server_port = sys.argv[1], int(sys.argv[2])
            if server_port < 1024 or server_port > 65535:
                raise ValueError
            return server_address, server_port
        except IndexError:
            print(f'Ошибка во введенных данных порта и/или IP-адреса или их отсутствие.\n'
                  f'Будут применены дефолтные значения: адрес - {server_address},'
                  f'порт - {server_port}')
            return server_address, server_port
        except ValueError:
            print('Число для порта не может быть меньше 1024 или больше 65535.')
            sys.exit(1)

    def client_connect(self):
        """Establishes a connection to the server"""

        server_address, server_port = self.validate_addr_port()
        try:
            self.socket.connect((server_address, server_port))
        except OSError as e:
            print(e.strerror)
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

    def responce_read(self):
        """Receiving the server response and its output"""

        msg = self.get_message()
        try:
            if RESPONSE in msg:
                answer = '200 : OK' if msg[RESPONSE] == 200 else f'400 : {msg[ERROR]}'
                return answer
            raise ValueError
        except ValueError:
            print('Ошибка в ответе, полученном от сервера, клиентское приложение будет закрыто.')
            sys.exit(1)
