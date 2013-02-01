import unittest

from yadtshell.loggingtools import (create_next_log_file_name_with_command_arguments_as_tag,
                                    create_next_log_file_name,
                                    get_command_counter_and_increment)
from unittest_support import FileNameTestCase
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
        yadtshell.loggingtools.command_counter = 123
        self.actual_file_name = create_next_log_file_name(
                log_dir='/var/log/test',
                target_name='target-name',
                command_start_timestamp='2013-01-31--11-27-56',
                user_name='user-name',
                source_host='host-name',
                tag='status'
        )

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
        yadtshell.loggingtools.command_counter = 123
        self.actual_file_name = create_next_log_file_name_with_command_arguments_as_tag(
                log_dir='/var/log/test',
                target_name='target-name',
                command_start_timestamp='2013-01-31--11-27-56',
                user_name='user-name',
                source_host='host-name',
                command_arguments=['yadtshell', 'status']
        )
