import unittest
from mockito import when, verify, unstub, any as any_value

import yadtshell
from yadtshell.commandline import ensure_command_has_required_arguments, EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT


class EnsureCommandHasRequiredArgumentsTests(unittest.TestCase):

    def setUp(self):
        self._show_help_callback_has_been_called = False

    def tearDown(self):
        unstub()

    def fake_show_help_callback(self):
        self._show_help_callback_has_been_called = True


    def test_should_exit_with_error_code_1_when_executing_command_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)


    def test_should_execute_show_help_callback_when_no_arguments_are_given(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', [], self.fake_show_help_callback)

        self.assertTrue(self._show_help_callback_has_been_called)
