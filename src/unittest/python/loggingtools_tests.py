import unittest

from yadtshell.loggingtools import create_next_log_file_name_with_command_arguments_as_tag, get_command_counter_and_increment
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


class CreateNextLogFileNameWithCommandArgumentsAsTagTests(unittest.TestCase):

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

    def _assert_element_at_is(self, actual_file_name, element_position, element_value):
        actual_element_value = actual_file_name.split('.')[element_position]
        message = 'Expected : {0} but got {1} instead'.format(element_value, actual_element_value)
        self.assertTrue(actual_element_value == element_value, message)

    def _assert(self, actual_file_name):
        self.actual_file_name = actual_file_name
        return self

    def _element_at(self, element_position):
        self.element_position = element_position
        return self

    def _is_equal_to(self, element_value):
        self._assert_element_at_is(self.actual_file_name, self.element_position, element_value)
