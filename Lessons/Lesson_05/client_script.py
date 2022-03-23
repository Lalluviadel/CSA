import logging

from common.classfile import Client


def client_start():
    logger = logging.getLogger('app.client_script')
    client = Client()
    logger.info('Клиент создан и готов к работе.')
    client.client_connect()
    client.send_a_message()
    # print(client.response_read())
    logger.info(f'Ответ сервера: {client.response_read()}')


if __name__ == '__main__':
    client_start()
