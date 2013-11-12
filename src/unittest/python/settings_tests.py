import yadtshell
import unittest
from mock import patch, MagicMock
from StringIO import StringIO


class SettingsTests(unittest.TestCase):

    @patch('yadtshell.settings.os.getcwd')
    @patch('yadtshell.settings.open', create=True)
    def test_should_load_target_file(self, mock_open, getcwd):
        content = """
hosts:
    - foobar
"""
        mock_open.return_value = MagicMock(spec=file, wraps=StringIO(content))
        getcwd.return_value = '/foo/bar/foobaz42'

        result = yadtshell.settings.load_target_file("useless_name")
        expect = dict(name='foobaz42',
                      hosts=['foobar'])
        self.assertEqual(result, expect)
