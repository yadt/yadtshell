import unittest
import logging

from mock import Mock, patch

from unittest_support import FileNameTestCase
from yadtshell.loggingtools import (
    create_next_log_file_name_with_command_arguments_as_tag,
    create_next_log_file_name,
    _get_command_counter_and_increment,
    _strip_special_characters,
    _strip_dashes,
    _switch_characters_to_lower_case,
    _trim_underscores,
    _replace_uri_specific_characters_with_underscores,
    _replace_blanks_with_underscores,
    ErrorFilter,
    InfoFilter,
    configure_logger_output_stream_by_level)
import yadtshell.loggingtools


class LoggerConfigurationTests(unittest.TestCase):

    @patch('yadtshell.loggingtools.ErrorFilter')
    @patch('yadtshell.loggingtools.InfoFilter')
    def test_should_add_error_filter_to_stderr_and_info_filter_to_stdout(self,
                                                                         info_filter,
                                                                         error_filter):
        stderr_handler = Mock()
        stdout_handler = Mock()

        configure_logger_output_stream_by_level(stderr_handler, stdout_handler)

        stderr_handler.addFilter.assert_called_with(error_filter.return_value)
        stdout_handler.addFilter.assert_called_with(info_filter.return_value)


class CreateNextLogFileNameTests(FileNameTestCase):

    def setUp(self):
        self.patcher = patch(
            'yadtshell.loggingtools._get_command_counter_and_increment')
        patched = self.patcher.start()
        patched.return_value = 123
        self.actual_file_name = create_next_log_file_name(
            log_dir='/var/log/test',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            tag='status'
        )

    def tearDown(self):
        self.patcher.stop()

    def test_should_use_script_name_with_log_dir_as_first_element(self):
        self._assert(self.actual_file_name)._element_at(
            0)._is_equal_to('/var/log/test/yadtshell')

    def test_should_use_target_name_as_second_element(self):
        self._assert(self.actual_file_name)._element_at(
            1)._is_equal_to('target-name')

    def test_should_use_current_timestamp_as_third_element(self):
        self._assert(self.actual_file_name)._element_at(
            2)._is_equal_to('2013-01-31--11-27-56')

    def test_should_use_user_name_as_fourth_element(self):
        self._assert(self.actual_file_name)._element_at(
            3)._is_equal_to('user-name')

    def test_should_use_command_counter_as_fifth_element(self):
        self._assert(self.actual_file_name)._element_at(4)._is_equal_to('123')

    def test_should_use_host_name_as_sixth_element(self):
        self._assert(self.actual_file_name)._element_at(
            5)._is_equal_to('host-name')

    def test_should_use_command_argument_as_seventh_element(self):
        self._assert(self.actual_file_name)._element_at(
            6)._is_equal_to('status')


class CreateNextLogFileNameWithCommandArgumentsAsTagTests(FileNameTestCase):

    def setUp(self):
        self.patcher = patch(
            'yadtshell.loggingtools._get_command_counter_and_increment')
        patched = self.patcher.start()
        patched.return_value = 123

    def tearDown(self):
        self.patcher.stop()

    def test_should_use_command_argument_as_seventh_element(self):
        actual_file_name = create_next_log_file_name_with_command_arguments_as_tag(
            log_dir='log-directory',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            command_arguments=['yadtshell', 'status']
        )
        self._assert(actual_file_name)._element_at(6)._is_equal_to('status')

    @patch('yadtshell.loggingtools.create_next_log_file_name')
    def test_should_call_create_next_log_file_name_using_given_arguments(self, next_logfile):
        next_logfile.return_value = 'log-file-name'

        actual_log_file_name = create_next_log_file_name_with_command_arguments_as_tag(
            log_dir='log-directory',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            command_arguments=['yadtshell', 'status']
        )

        self.assertEqual('log-file-name', actual_log_file_name)
        next_logfile.assert_called_with(
            'log-directory', 'target-name', '2013-01-31--11-27-56',
            'user-name', 'host-name', tag='status')

    @patch('yadtshell.loggingtools.create_next_log_file_name')
    def test_should_join_arguments_using_underscore(self, next_logfile):
        next_logfile.return_value = 'log-file-name'

        actual_log_file_name = create_next_log_file_name_with_command_arguments_as_tag(
            log_dir='log-directory',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            command_arguments=[
                    '/usr/bin/yadtshell', 'abc', 'def', 'ghi', 'jkl']
        )

        self.assertEqual('log-file-name', actual_log_file_name)
        next_logfile.assert_called_with('log-directory', 'target-name',
                                        '2013-01-31--11-27-56', 'user-name',
                                        'host-name', tag='abc_def_ghi_jkl')

    @patch('yadtshell.loggingtools.create_next_log_file_name')
    def test_should_join_command_and_arguments_using_underscore_if_command_is_not_yadtshell(self, next_logfile):
        next_logfile.return_value = 'log-file-name'

        actual_log_file_name = create_next_log_file_name_with_command_arguments_as_tag(
            log_dir='log-directory',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            command_arguments=['foobar', 'abc', 'def', 'ghi', 'jkl']
        )

        self.assertEqual('log-file-name', actual_log_file_name)
        next_logfile.assert_called_with(
            'log-directory', 'target-name', '2013-01-31--11-27-56',
            'user-name', 'host-name', tag='foobar_abc_def_ghi_jkl')

    @patch('yadtshell.loggingtools.create_next_log_file_name')
    @patch('yadtshell.loggingtools._replace_uri_specific_characters_with_underscores')
    @patch('yadtshell.loggingtools._strip_dashes')
    @patch('yadtshell.loggingtools._strip_special_characters')
    @patch('yadtshell.loggingtools._trim_underscores')
    @patch('yadtshell.loggingtools._replace_blanks_with_underscores')
    def test_should_prepare_string_as_expected(self, blanks, underscores,
                                               special, dashes, uri, next_logfile):

        uri.return_value = 'replaced uri specific characters'
        dashes.return_value = 'stripped dashes'
        special.return_value = 'stripped special characters'
        underscores.return_value = 'trimmed underscores'
        blanks.return_value = 'replaced blanks with underscores'
        next_logfile.return_value = 'log-file-name'

        actual_log_file_name = create_next_log_file_name_with_command_arguments_as_tag(
            log_dir='log-directory',
            target_name='target-name',
            command_start_timestamp='2013-01-31--11-27-56',
            user_name='user-name',
            source_host='host-name',
            command_arguments=['yadtshell', 'arg1', 'arg2']
        )

        self.assertEqual('log-file-name', actual_log_file_name)
        uri.assert_called_with('arg1_arg2')
        dashes.assert_called_with('replaced uri specific characters')
        special.assert_called_with('stripped dashes')
        underscores.assert_called_with('stripped special characters')
        blanks.assert_called_with('trimmed underscores')

        next_logfile.assert_called_with(
            'log-directory', 'target-name', '2013-01-31--11-27-56',
            'user-name', 'host-name', tag='replaced blanks with underscores')


class GetCommandCounterAndIncrementTests(unittest.TestCase):

    def setUp(self):
        yadtshell.loggingtools.command_counter = 0

    def test_should_return_zero_as_initial_value(self):
        self.assertEqual(0, _get_command_counter_and_increment())

    def test_should_return_one_as_second_value(self):
        _get_command_counter_and_increment()
        self.assertEqual(1, _get_command_counter_and_increment())

    def test_should_return_two_as_third_value(self):
        _get_command_counter_and_increment()
        _get_command_counter_and_increment()
        self.assertEqual(2, _get_command_counter_and_increment())


class StripSpecialCharactersTest(unittest.TestCase):

    def test_should_strip_special_character_colon(self):
        self.assertEqual('', _strip_special_characters(':'))

    def test_should_strip_special_character_parens(self):
        self.assertEqual('', _strip_special_characters('('))
        self.assertEqual('', _strip_special_characters(')'))

    def test_should_strip_special_character_double_quotes(self):
        self.assertEqual('', _strip_special_characters('"'))

    def test_should_strip_special_character_asterisk(self):
        self.assertEqual('', _strip_special_characters('*'))

    def test_should_strip_special_character_left_square_bracket(self):
        self.assertEqual('', _strip_special_characters('['))

    def test_should_strip_special_character_right_square_bracket(self):
        self.assertEqual('', _strip_special_characters(']'))

    def test_should_strip_special_character_single_quote(self):
        self.assertEqual('', _strip_special_characters("'"))

    def test_should_not_strip_normal_characters(self):
        self.assertEqual(
            'foobar', _strip_special_characters(':*[]foo:*[]bar:*[]'))

    def test_should_not_strip_simple_string(self):
        self.assertEqual('foobar', _strip_special_characters('foobar'))


class TrimUnderscoresTests(unittest.TestCase):

    def test_should_remove_leading_underscore(self):
        self.assertEqual('foobar', _trim_underscores('_foobar'))

    def test_should_remove_trailing_underscore(self):
        self.assertEqual('foobar', _trim_underscores('foobar_'))

    def test_should_trim_underscores(self):
        self.assertEqual('foobar', _trim_underscores('_foobar_'))

    def test_should_pass_simple_string_without_trimming_anything(self):
        self.assertEqual('foobar', _trim_underscores('foobar'))


class StripDashesTests(unittest.TestCase):

    def test_should_pass_simple_string_without_stripping_any_dashes(self):
        self.assertEqual('foobar', _strip_dashes('foobar'))

    def test_should_strip_dash(self):
        self.assertEqual('foobar', _strip_dashes('foo-bar'))

    def test_should_strip_multiple_dashes(self):
        self.assertEqual('foobar', _strip_dashes('-fo-o-b-a--r---'))


class ReplaceUriSpecificCharactersWithUnderscoresTests(unittest.TestCase):

    def test_should_return_given_string(self):
        self.assertEqual(
            'foobar', _replace_uri_specific_characters_with_underscores('foobar'))

    def test_should_return_string_with_replaced_colon_slash_slash(self):
        self.assertEqual(
            'foo_bar', _replace_uri_specific_characters_with_underscores('foo://bar'))

    def test_should_return_string_with_replaced_slash(self):
        self.assertEqual(
            'bar_boo', _replace_uri_specific_characters_with_underscores('bar/boo'))

    def test_should_return_string_with_replaced_uri_characters(self):
        self.assertEqual(
            'foo_bar_boo', _replace_uri_specific_characters_with_underscores('foo://bar/boo'))


class ReplaceBlanksWithUnderscoresTest(unittest.TestCase):

    def test_should_return_given_string(self):
        self.assertEqual(
            'spameggs', _replace_blanks_with_underscores('spameggs'))

    def test_should_replace_one_blank_with_one_underscore(self):
        self.assertEqual('_', _replace_blanks_with_underscores(' '))

    def test_should_replace_blank_after_character_with_underscore(self):
        self.assertEqual('a_', _replace_blanks_with_underscores('a '))

    def test_should_replace_blank_between_words_with_underscore(self):
        self.assertEqual(
            'spam_eggs', _replace_blanks_with_underscores('spam eggs'))


class SwitchCharactersToLowerCase(unittest.TestCase):

    def test_should_return_given_string_of_lower_characters(self):
        self.assertEqual('abc', _switch_characters_to_lower_case('abc'))

    def test_should_return_lower_case_character_of_character(self):
        self.assertEqual('a', _switch_characters_to_lower_case('A'))

    def test_should_return_lower_case_string_of_given_string(self):
        self.assertEqual('abc', _switch_characters_to_lower_case('ABC'))

    def test_should_return_lower_case_string_of_string_with_capital_letters(self):
        self.assertEqual('foobar', _switch_characters_to_lower_case('FooBar'))


class ErrorFilterTests(unittest.TestCase):
    LOG_RECORD = 1
    DO_NOT_LOG_RECORD = 0

    def setUp(self):
        self.error_filter = ErrorFilter()

    def test_should_log_errors(self):
        error_record = Mock()
        error_record.levelno = logging.ERROR
        self.assertEqual(
            self.error_filter.filter(error_record), self.LOG_RECORD)

    def test_should_log_warnings(self):
        warning_record = Mock()
        warning_record.levelno = logging.WARN
        self.assertEqual(
            self.error_filter.filter(warning_record), self.LOG_RECORD)

        warning_record.levelno = logging.WARNING
        self.assertEqual(
            self.error_filter.filter(warning_record), self.LOG_RECORD)

    def test_should_log_criticals(self):
        critical_record = Mock()
        critical_record.levelno = logging.CRITICAL
        self.assertEqual(
            self.error_filter.filter(critical_record), self.LOG_RECORD)

    def test_should_log_fatals(self):
        fatal_record = Mock()
        fatal_record.levelno = logging.FATAL
        self.assertEqual(
            self.error_filter.filter(fatal_record), self.LOG_RECORD)

    def test_should_not_log_infos(self):
        info_record = Mock()
        info_record.levelno = logging.INFO
        self.assertEqual(self.error_filter.filter(
            info_record), self.DO_NOT_LOG_RECORD)

    def test_should_not_log_debugs(self):
        debug_record = Mock()
        debug_record.levelno = logging.DEBUG
        self.assertEqual(self.error_filter.filter(
            debug_record), self.DO_NOT_LOG_RECORD)


class InfoFilterTests(unittest.TestCase):
    LOG_RECORD = 1
    DO_NOT_LOG_RECORD = 0

    def setUp(self):
        self.info_filter = InfoFilter()

    def test_should_not_log_errors(self):
        error_record = Mock()
        error_record.levelno = logging.ERROR
        self.assertEqual(self.info_filter.filter(
            error_record), self.DO_NOT_LOG_RECORD)

    def test_should_not_log_warnings(self):
        warning_record = Mock()
        warning_record.levelno = logging.WARN
        self.assertEqual(self.info_filter.filter(
            warning_record), self.DO_NOT_LOG_RECORD)

        warning_record.levelno = logging.WARNING
        self.assertEqual(self.info_filter.filter(
            warning_record), self.DO_NOT_LOG_RECORD)

    def test_should_not_log_criticals(self):
        critical_record = Mock()
        critical_record.levelno = logging.CRITICAL
        self.assertEqual(self.info_filter.filter(
            critical_record), self.DO_NOT_LOG_RECORD)

    def test_should_not_log_fatals(self):
        fatal_record = Mock()
        fatal_record.levelno = logging.FATAL
        self.assertEqual(self.info_filter.filter(
            fatal_record), self.DO_NOT_LOG_RECORD)

    def test_should_log_infos(self):
        info_record = Mock()
        info_record.levelno = logging.INFO
        self.assertEqual(self.info_filter.filter(info_record), self.LOG_RECORD)

    def test_should_log_debugs(self):
        debug_record = Mock()
        debug_record.levelno = logging.DEBUG
        self.assertEqual(
            self.info_filter.filter(debug_record), self.LOG_RECORD)
