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

    @patch('yadtshell.settings.os.getcwd')
    @patch('yadtshell.settings.open', create=True)
    def test_should_load_meta_target_file(self, mock_open, getcwd):
        content = """
hosts:
    - foobar01
includes:
    - sub-target
"""
        subcontent = """
hosts:
    - foobar42
"""

        def my_open(filename):
            if filename == 'root-target':
                return MagicMock(spec=file, wraps=StringIO(content))
            return MagicMock(spec=file, wraps=StringIO(subcontent))

        mock_open.side_effect = my_open
        getcwd.return_value = '/foo/bar/foobaz42'

        result = yadtshell.settings.load_target_file('root-target')
        expect = dict(name='foobaz42',
                      hosts=['foobar01', 'foobar42'],
                      includes=['sub-target'])
        self.assertEqual(result, expect)

    @patch('yadtshell.settings.os.getcwd')
    @patch('yadtshell.settings.open', create=True)
    def test_should_load_recursed_meta_target_files(self, mock_open, getcwd):
        content = """
hosts:
    - foobar01
includes:
    - sub-target
"""
        subcontent = """
hosts:
    - foobar42
includes:
    - sub-sub-target
"""
        subsubcontent = """
hosts:
    - foobar4242
"""

        def my_open(filename):
            if filename == 'root-target':
                return MagicMock(spec=file, wraps=StringIO(content))
            if filename == 'sub-target':
                return MagicMock(spec=file, wraps=StringIO(subcontent))

            return MagicMock(spec=file, wraps=StringIO(subsubcontent))

        mock_open.side_effect = my_open
        getcwd.return_value = '/foo/bar/foobaz42'

        result = yadtshell.settings.load_target_file('root-target')
        expect = dict(name='foobaz42',
                      hosts=['foobar01', 'foobar42', 'foobar4242'],
                      includes=['sub-target'])
        self.assertEqual(result, expect)

    @patch('yadtshell.settings.os.getcwd')
    @patch('yadtshell.settings.open', create=True)
    def test_should_load_recursed_meta_target_files_once(self, mock_open, getcwd):
        content = """
hosts:
    - foobar01
includes:
    - sub-target
"""
        subcontent = """
hosts:
    - foobar42
includes:
    - root-target
"""

        def my_open(filename):
            if filename == 'root-target':
                return MagicMock(spec=file, wraps=StringIO(content))
            return MagicMock(spec=file, wraps=StringIO(subcontent))

        mock_open.side_effect = my_open
        getcwd.return_value = '/foo/bar/foobaz42'

        result = yadtshell.settings.load_target_file('root-target')
        expect = dict(name='foobaz42',
                      hosts=['foobar01', 'foobar42'],
                      includes=['sub-target'])
        self.assertEqual(result, expect)
