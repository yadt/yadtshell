import unittest

from mockito import when, unstub, verify, any as any_value

from unittest_support import FileNameTestCase
from yadtshell.loggingtools import (create_next_log_file_name_with_command_arguments_as_tag,
                                    create_next_log_file_name,
                                    get_command_counter_and_increment,
                                    _strip_special_characters,
                                    _trim_underscores,
                                    _strip_dashes,
                                    _replace_uri_specific_characters_with_underscores)
import yadtshell.loggingtools


class GetCommandCounterAndIncrementTests(unittest.TestCase):

    def setUp(self):
        yadtshell.loggingtools.command_counter = 0

    def test_should_return_zero_as_initial_value(self):
        self.assertEqual(0, get_command_counter_and_increment())

    def test_should_return_one_as_second_value(self):
        get_command_counter_and_increment()
        self.assertEqual(1, get_command_counter_and_increment())

    def test_should_return_two_as_third_value(self):
        get_command_counter_and_increment()
        get_command_counter_and_increment()
        self.assertEqual(2, get_command_counter_and_increment())


class CreateNextLogFileNameTests(FileNameTestCase):
    def setUp(self):
        when(yadtshell.loggingtools).get_command_counter_and_increment().thenReturn(123)
        self.actual_file_name = create_next_log_file_name(
                log_dir='/var/log/test',
                target_name='target-name',
                command_start_timestamp='2013-01-31--11-27-56',
                user_name='user-name',
                source_host='host-name',
                tag='status'
        )

    def tearDown(self):
        unstub()


    def test_should_use_script_name_with_log_dir_as_first_element(self):
        self._assert(self.actual_file_name)._element_at(0)._is_equal_to('/var/log/test/yadtshell')

    def test_should_use_target_name_as_second_element(self):
        self._assert(self.actual_file_name)._element_at(1)._is_equal_to('target-name')

    def test_should_use_current_timestamp_as_third_element(self):
        self._assert(self.actual_file_name)._element_at(2)._is_equal_to('2013-01-31--11-27-56')

    def test_should_use_user_name_as_fourth_element(self):
        self._assert(self.actual_file_name)._element_at(3)._is_equal_to('user-name')

    def test_should_use_command_counter_as_fifth_element(self):
        self._assert(self.actual_file_name)._element_at(4)._is_equal_to('123')

    def test_should_use_host_name_as_sixth_element(self):
        self._assert(self.actual_file_name)._element_at(5)._is_equal_to('host-name')

    def test_should_use_command_argument_as_seventh_element(self):
        self._assert(self.actual_file_name)._element_at(6)._is_equal_to('status')


class CreateNextLogFileNameWithCommandArgumentsAsTagTests(FileNameTestCase):

    def setUp(self):
        when(yadtshell.loggingtools).get_command_counter_and_increment().thenReturn(123)

    def tearDown(self):
        unstub()

    def test_should_use_command_argument_as_seventh_element(self):
        self.actual_file_name = create_next_log_file_name_with_command_arguments_as_tag(
                log_dir='log-directory',
                target_name='target-name',
                command_start_timestamp='2013-01-31--11-27-56',
                user_name='user-name',
                source_host='host-name',
                command_arguments=['yadtshell', 'status']
        )
        self._assert(self.actual_file_name)._element_at(6)._is_equal_to('status')

    def test_should_call_create_next_log_file_name_using_given_arguments(self):
        when(yadtshell.loggingtools).create_next_log_file_name(any_value(), any_value(), any_value(), any_value(), any_value(), tag=any_value()).thenReturn('log-file-name')

        actual_log_file_name = self.actual_file_name = create_next_log_file_name_with_command_arguments_as_tag(
                log_dir='log-directory',
                target_name='target-name',
                command_start_timestamp='2013-01-31--11-27-56',
                user_name='user-name',
                source_host='host-name',
                command_arguments=['yadtshell', 'status']
        )

        self.assertEqual('log-file-name', actual_log_file_name)
        verify(yadtshell.loggingtools).create_next_log_file_name('log-directory', 'target-name', '2013-01-31--11-27-56', 'user-name', 'host-name', tag='status')


class StripSpecialCharactersTest(unittest.TestCase):

    def test_should_strip_special_character_colon(self):
        self.assertEqual('', _strip_special_characters(':'))

    def test_should_strip_special_character_asterisk(self):
        self.assertEqual('', _strip_special_characters('*'))

    def test_should_strip_special_character_left_square_bracket(self):
        self.assertEqual('', _strip_special_characters('['))

    def test_should_strip_special_character_right_square_bracket(self):
        self.assertEqual('', _strip_special_characters(']'))

    def test_should_not_strip_normal_characters(self):
        self.assertEqual('foobar', _strip_special_characters(':*[]foo:*[]bar:*[]'))

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
        self.assertEqual('foobar', _replace_uri_specific_characters_with_underscores('foobar'))

    def test_should_return_string_with_replaced_colon_slash_slash(self):
        self.assertEqual('foo_bar', _replace_uri_specific_characters_with_underscores('foo://bar'))

    def test_should_return_string_with_replaced_slash(self):
        self.assertEqual('bar_boo', _replace_uri_specific_characters_with_underscores('bar/boo'))

    def test_should_return_string_with_replaced_uri_characters(self):
        self.assertEqual('foo_bar_boo', _replace_uri_specific_characters_with_underscores('foo://bar/boo'))

