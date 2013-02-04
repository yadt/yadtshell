import unittest
from mockito import when, verify, unstub, any as any_value, never

import yadtshell
from yadtshell.commandline import ensure_command_has_required_arguments, EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT


class EnsureCommandHasRequiredArgumentsTests(unittest.TestCase):

    def setUp(self):
        self._show_help_callback_has_been_called = False
        when(yadtshell.commandline.LOGGER).error(any_value).thenReturn(None)

    def tearDown(self):
        unstub()

    def fake_show_help_callback(self):
        self._show_help_callback_has_been_called = True

    def test_should_not_exit_when_arguments_are_provided(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', ['service://hostname/service'], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys, never).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_with_appropriate_error_code_when_executing_command_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_execute_show_help_callback_when_no_arguments_are_given(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', [], self.fake_show_help_callback)

        self.assertTrue(self._show_help_callback_has_been_called)

    def test_should_fail_when_executing_command_start_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('start', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_stop_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('stop', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_ignore_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('ignore', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_updateartefact_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('updateartefact', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_lock_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('lock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_unlock_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('unlock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_unignore_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments('lock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)
