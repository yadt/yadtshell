import unittest
from mockito import when, verify, unstub, any as any_value, mock
import yadtshell
from yadtshell.commandline import ensure_command_has_required_arguments


class EnsureCommandHasRequiredArgumentsTests(unittest.TestCase):

    def tearDown(self):
        unstub()

    def test_start_command_without_arguments_should_exit_with_code_0(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)
        fake_show_help_function = lambda: None

        ensure_command_has_required_arguments('start', [], fake_show_help_function)

        verify(yadtshell.commandline.sys).exit(0)
