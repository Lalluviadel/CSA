import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.classfile import Client


class TestClient(unittest.TestCase):
    """Tests for Client class"""
    client = Client()

    def test_validate_addr_port_ok(self):
        """Test for determining the port value and the address value passed in arguments"""
        client = self.client
        test_args = ["client_script.py", '127.0.0.1', '8079']
        with patch.object(sys, 'argv', test_args):
            self.assertEqual(client.validate_addr_port(), ('127.0.0.1', 8079))

    def test_validate_addr_port_without_data(self):
        """Test for determining the port value and the address value not passed in arguments"""
        client = self.client
        test_args = ["client_script.py", '127.0.0.1']
        test_args_02 = ["client_script.py", '2233']
        test_args_03 = ["client_script.py"]
        with patch.object(sys, 'argv', test_args):
            self.assertEqual(client.validate_addr_port(), ('127.0.0.1', 7777))
        with patch.object(sys, 'argv', test_args_02):
            self.assertEqual(client.validate_addr_port(), ('127.0.0.1', 7777))
        with patch.object(sys, 'argv', test_args_03):
            self.assertEqual(client.validate_addr_port(), ('127.0.0.1', 7777))

    def test_validate_address_except_ValueErr(self):
        """Test for determining ValueError when the port value passed in arguments
        is not a number < 1024 and > 65535"""
        client = self.client
        test_args = ["client_script.py", '127.0.0.1', '100000']
        with self.assertRaises(SystemExit):
            with patch.object(sys, 'argv', test_args):
                self.assertRaises(ValueError, client.validate_addr_port())
                unittest.main(exit=False)

    def test_client_connect(self):
        """Test to check the OSError error if the attempt to connect to the server is unsuccessful"""
        client = self.client
        with self.assertRaises(SystemExit):
            self.assertRaises(OSError, client.client_connect())
            unittest.main(exit=False)


if __name__ == '__main__':
    unittest.main()
