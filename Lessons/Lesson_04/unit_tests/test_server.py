import sys
import unittest
from unittest.mock import patch

from ..common.classfile import Server


class TestServer(unittest.TestCase):
    """Tests for Server class"""
    server = Server('', 7777)

    def test_validate_port_ok(self):
        """Test for determining the port value passed in arguments"""
        server = self.server
        test_args = ["server_script.py", '-p', '8079', '-a', '127.0.0.1']
        with patch.object(sys, 'argv', test_args):
            self.assertEqual(server.validate_port(), 8079)

    def test_validate_port_except_ValueErr(self):
        """Test for determining ValueError when the port value passed in arguments
        is not a number < 1024 and > 65535"""
        server = self.server
        test_args = ["server_script.py", '-p', '', '-a', '127.0.0.1']
        with self.assertRaises(SystemExit):
            with patch.object(sys, 'argv', test_args):
                self.assertRaises(ValueError, server.validate_port())
                unittest.main(exit=False)

    def test_validate_port_except_IndexErr(self):
        """Test for determining IndexError when the port value not passed in arguments"""
        server = self.server
        test_args = ["server_script.py", '-p']
        with self.assertRaises(SystemExit):
            with patch.object(sys, 'argv', test_args):
                self.assertRaises(IndexError, server.validate_port())
                unittest.main(exit=False)

    def test_validate_address(self):
        """Test for determining the address value passed in arguments"""
        server = self.server
        test_args = ["server_script.py", '-p', '8079', '-a', '127.0.0.1']
        with patch.object(sys, 'argv', test_args):
            self.assertEqual(server.validate_address(), '127.0.0.1')

    def test_validate_address_except_IndexErr(self):
        """Test for determining IndexError when the port value not passed in arguments"""
        server = self.server
        test_args = ["server_script.py", '-p', '8079', '-a']
        with self.assertRaises(SystemExit):
            with patch.object(sys, 'argv', test_args):
                self.assertRaises(IndexError, server.validate_address())
                unittest.main(exit=False)


if __name__ == '__main__':
    unittest.main()
