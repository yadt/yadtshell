import unittest
from mockito import when, verify, unstub, any as any_value
import yadtshell
from yadtshell.commandline import ensure_command_has_required_arguments, EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT


class EnsureCommandHasRequiredArgumentsTests(unittest.TestCase):

    def tearDown(self):
        unstub()

    def test_should_exit_with_error_code_1_when_executing_start_command_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)
        fake_show_help_function = lambda: None

        ensure_command_has_required_arguments('start', [], fake_show_help_function)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)
