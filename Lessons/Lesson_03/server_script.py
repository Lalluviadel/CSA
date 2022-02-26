from common.classfile import Server

server = Server('', 7777)
server.bind_and_listen()
server.accept_and_exchange()
