import json
import sys
import os
import unittest
sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import ENCODING, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, DEFAULT_USERNAME, \
    RESPONSE, ERROR
from common.classfile import App


class TestSocket:
    """Test class socket simulations for checking sending and receiving functions"""

    def __init__(self, data: dict):
        self.data = data
        self.enc_msg = None
        self.recv_msg = None

    def send(self, msg):
        """Transforms dictionary into bytes and sends data to the socket"""
        self.enc_msg = json.dumps(self.data).encode(ENCODING)
        self.recv_msg = msg

    def recv(self, max_len):
        """Retrieves the data that the socket received"""
        return json.dumps(self.data).encode(ENCODING)


class TestApp(unittest.TestCase):
    """Test class simulates the parent class of the client and server parts"""
    msg_to_server = {ACTION: PRESENCE,
                     TIME: 1.2345,
                     USER: {ACCOUNT_NAME: DEFAULT_USERNAME}}
    good_server_reply = {RESPONSE: 200}
    bad_server_reply = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_send_msg(self):
        """Test for an App class function sending messages"""
        socket = TestSocket(self.msg_to_server)
        app = App(socket)
        app.send_msg(self.msg_to_server)
        self.assertEqual(socket.enc_msg, socket.recv_msg)
        self.assertRaises(TypeError, app.send_msg, socket)

    def test_get_message(self):
        """Test for an App class function receiving messages"""
        test_good = TestSocket(self.good_server_reply)
        test_bad = TestSocket(self.bad_server_reply)
        app = App(TestSocket(self.msg_to_server))
        self.assertEqual(app.get_message(test_good), self.good_server_reply)
        self.assertEqual(app.get_message(test_bad), self.bad_server_reply)


if __name__ == '__main__':
    unittest.main()

