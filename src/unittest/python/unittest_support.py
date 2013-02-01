from unittest import TestCase


class FileNameTestCase(TestCase):
    def _assert_element_at_is(self, actual_file_name, element_position, element_value):
        actual_element_value = actual_file_name.split('.')[element_position]
        message = 'Expected : {0} but got {1} instead'.format(element_value, actual_element_value)
        self.assertTrue(actual_element_value == element_value, message)

    def _assert(self, actual_file_name):
        self._actual_file_name = actual_file_name
        return self

    def _element_at(self, element_position):
        self.element_position = element_position
        return self

    def _is_equal_to(self, element_value):
        self._assert_element_at_is(self._actual_file_name, self.element_position, element_value)
