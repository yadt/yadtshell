import unittest
from mockito import when, verify, unstub, any as any_value, never
from mock import Mock, patch

import yadtshell
from yadtshell.commandline import (ensure_command_has_required_arguments,
                                   validate_command_line_options,
                                   normalize_message,
                                   normalize_options,
                                   confirm_transaction_by_user,
                                   infer_options_from_arguments,
                                   determine_command_from_arguments,
                                   EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT,
                                   EXIT_CODE_MISSING_MESSAGE_OPTION)


class ArgumentAndOptionParsingTests(unittest.TestCase):

    def test_should_return_none_when_no_command_is_true(self):
        self.assertEqual(
            None, determine_command_from_arguments({'update': False,
                                                    'status': False}))

    def test_should_return_command_when_value_is_true(self):
        self.assertEqual(
            'status', determine_command_from_arguments({'update': False,
                                                        'status': True, 'destroy': False}))

    def test_should_not_return_commands_not_matching_a_z(self):
        self.assertEqual(
            None, determine_command_from_arguments({'upDate': False,
                                                    'destr0YeR': True, 'status': False}))

    def test_should_not_include_arguments_when_they_do_not_start_with_dash(self):
        self.assertEqual(
            {}, infer_options_from_arguments({'foobar-arg': 'baz'}))

    def test_should_strip_dashdash_from_options_when_they_start_with_dash(self):
        self.assertEqual(
            {'foobar': 'baz'}, infer_options_from_arguments({'--foobar': 'baz'}))

    def test_should_replace_dashes_when_there_are_underscores_in_options(self):
        self.assertEqual(
            {'foobar_arg': 'baz'}, infer_options_from_arguments({'--foobar-arg': 'baz'}))

    def test_should_infer_multiple_options(self):
        self.assertEqual(
            {'test': True,
             'p': 151,
             'a_cool_option': 'abc',
             'foobar_arg': 'baz'},
            infer_options_from_arguments({'--foobar-arg': 'baz',
                                          '--test': True,
                                          'status': False,
                                          '--a-cool-option': 'abc',
                                          'sOmEaRgUm3nT': 42,
                                          '-p': 151}))


class UserConfirmationTests(unittest.TestCase):

    def setUp(self):
        self.user_input = Mock()
        yadtshell.commandline.raw_input = self.user_input

    def test_should_return_true_when_user_confirms_immediately(self):
        self.user_input.return_value = 'y'

        self.assertTrue(confirm_transaction_by_user('y/n', None))

    def test_should_return_true_when_user_confirms_with_uppercase(self):
        self.user_input.return_value = 'Y'

        self.assertTrue(confirm_transaction_by_user('y/n', None))

    def test_should_return_true_when_user_confirms_with_yes(self):
        self.user_input.return_value = 'Yes'

        self.assertTrue(confirm_transaction_by_user('y/n', None))

    def test_should_return_false_when_user_declines_immediately(self):
        self.user_input.return_value = 'n'

        self.assertFalse(confirm_transaction_by_user('y/n', None))

    def test_should_return_false_when_user_declines_immediately_with_uppercase(self):
        self.user_input.return_value = 'N'

        self.assertFalse(confirm_transaction_by_user('y/n', None))

    def test_should_return_false_when_user_declines_immediately_with_no(self):
        self.user_input.return_value = 'nO'

        self.assertFalse(confirm_transaction_by_user('y/n', None))

    def test_should_return_default_when_user_provides_no_value(self):
        self.user_input.return_value = ''

        self.assertTrue(confirm_transaction_by_user('Y/n', True))

    def test_should_request_input_with_selector(self):
        self.user_input.return_value = ''

        confirm_transaction_by_user('y/n', None)

        self.user_input.assert_called_with('Do you want to continue [y/n]? ')


class ValidateCommandLineOptionsTest(unittest.TestCase):

    def tearDown(self):
        self.log_patcher.stop()

    def setUp(self):
        self._show_help_callback_has_been_called = False
        self.log_patcher = patch('yadtshell.commandline.LOGGER.error')
        self.log_patcher.start()

    def fake_show_help_callback(self):
        self._show_help_callback_has_been_called = True

    @patch('yadtshell.commandline.sys.exit')
    def test_should_exit_with_appropriate_code_when_command_is_lock_and_no_message_was_given(self, mock_exit):
        options = Mock()
        options.message = None

        validate_command_line_options(
            'lock', options, self.fake_show_help_callback)

        mock_exit.assert_called_with(EXIT_CODE_MISSING_MESSAGE_OPTION)

    @patch('yadtshell.commandline.sys.exit')
    def test_should_execute_show_help_callback_when_no_lock_message_is_given(self, _):
        options = Mock()
        options.message = None

        validate_command_line_options(
            'lock', options, self.fake_show_help_callback)

        self.assertTrue(self._show_help_callback_has_been_called)

    @patch('yadtshell.commandline.sys.exit')
    def test_should_not_exit_when_command_is_lock_and_message_is_given(self, mock_exit):
        options = Mock()
        options.message = 'lock message'

        validate_command_line_options(
            'lock', options, self.fake_show_help_callback)

        mock_exit.assert_not_called()

    @patch('yadtshell.commandline.sys.exit')
    def test_should_exit_with_appropriate_code_when_command_is_ignore_and_no_message_was_given(self, mock_exit):
        options = Mock()
        options.message = None

        validate_command_line_options(
            'ignore', options, self.fake_show_help_callback)

        mock_exit.assert_called_with(EXIT_CODE_MISSING_MESSAGE_OPTION)

    @patch('yadtshell.commandline.sys.exit')
    def test_should_execute_show_help_callback_when_no_ignore_message_is_given(self, _):
        options = Mock()
        options.message = None

        validate_command_line_options(
            'ignore', options, self.fake_show_help_callback)

        self.assertTrue(self._show_help_callback_has_been_called)

    @patch('yadtshell.commandline.sys.exit')
    def test_should_not_exit_when_command_is_ignore_and_message_is_given(self, mock_exit):
        options = Mock()
        options.message = 'ignore message'

        validate_command_line_options(
            'ignore', options, self.fake_show_help_callback)

        mock_exit.assert_not_called()


class NormalizeMessageTests(unittest.TestCase):

    def test_should_remove_single_quotes_when_message_contains_single_quotes(self):
        self.assertEqual(normalize_message("don't"), "dont")

    def test_should_not_remove_anything_when_message_does_not_contain_single_nor_double_quotes(self):
        self.assertEqual(
            normalize_message('lorem ipsum dolorem'), 'lorem ipsum dolorem')

    def test_should_remove_double_quotes_when_message_contains_double_quotes(self):
        self.assertEqual(normalize_message('don"t'), 'dont')


class NormalizeOptionsTests(unittest.TestCase):

    class MockedOptions:

        def __init__(self, **keywords):
            self.__dict__.update(keywords)

    def tearDown(self):
        unstub()

    def test_should_execute_normalize_message_when_message_option_is_given(self):
        when(yadtshell.commandline).normalize_message(
            any_value()).thenReturn('normalized message')
        options_with_message = self.MockedOptions()
        options_with_message.message = 'some message'

        actual_options = normalize_options(options_with_message)

        verify(yadtshell.commandline).normalize_message('some message')
        self.assertEqual(actual_options.message, 'normalized message')

    def test_should_not_execute_normalize_message_when_message_option_is_none(self):
        when(yadtshell.commandline).normalize_message(
            any_value()).thenReturn('normalized message')
        options_with_none_message = self.MockedOptions()
        options_with_none_message.message = None

        actual_options = normalize_options(options_with_none_message)

        verify(yadtshell.commandline, never).normalize_message(None)
        self.assertEqual(actual_options.message, None)

    def test_should_not_execute_normalize_message_when_message_option_is_not_given(self):
        when(yadtshell.commandline).normalize_message(
            any_value()).thenReturn('normalized message')
        options_without_message = object()

        normalize_options(options_without_message)

        verify(yadtshell.commandline, never).normalize_message('some message')

    def test_should_not_perform_mutation_on_options_when_normalize_options_is_called(self):
        when(yadtshell.commandline).normalize_message(
            any_value()).thenReturn('normalized message')
        options_with_message = self.MockedOptions()
        options_with_message.message = 'some message'

        actual_options = normalize_options(options_with_message)

        verify(yadtshell.commandline).normalize_message('some message')
        self.assertTrue(actual_options is not options_with_message,
                        'performed mutation on the options instead of creating a new object')


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

        ensure_command_has_required_arguments(
            'start', ['service://hostname/service'], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys, never).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_with_appropriate_error_code_when_executing_command_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'start', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_execute_show_help_callback_when_no_arguments_are_given(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'start', [], self.fake_show_help_callback)

        self.assertTrue(self._show_help_callback_has_been_called)

    def test_should_fail_when_executing_command_start_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'start', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_stop_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'stop', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_ignore_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'ignore', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_updateartefact_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'updateartefact', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_lock_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'lock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_unlock_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'unlock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)

    def test_should_fail_when_executing_command_unignore_without_arguments(self):
        when(yadtshell.commandline.sys).exit(any_value()).thenReturn(None)

        ensure_command_has_required_arguments(
            'lock', [], self.fake_show_help_callback)

        verify(yadtshell.commandline.sys).exit(
            EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)
