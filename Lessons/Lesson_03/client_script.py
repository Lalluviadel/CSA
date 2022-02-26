from common.classfile import Client

client = Client()
client.client_connect()
client.send_a_message()
print(client.responce_read())
