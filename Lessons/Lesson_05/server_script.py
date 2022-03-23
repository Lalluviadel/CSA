from common.classfile import Server
import logging


def server_start():
    logger = logging.getLogger('app.server_script')
    server = Server('', 7777)
    logger.info('Сервер создан и готов к работе.')
    server.bind_and_listen()
    server.accept_and_exchange()


if __name__ == '__main__':
    server_start()
