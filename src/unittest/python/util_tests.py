import unittest

from mock import Mock, patch, MagicMock

import yadtshell
from yadtshell.util import (inbound_deps_on_same_host,
                            outbound_deps_on_same_host,
                            compute_dependency_scores,
                            calculate_max_tries_for_interval_and_delay,
                            render_state,
                            restore_current_state,
                            get_mtime_of_current_state,
                            get_age_of_current_state_in_seconds,
                            filter_missing_services,
                            first_error_line,
                            log_exceptions)
from yadtshell.constants import STANDALONE_SERVICE_RANK
from yadtshell.components import (Host,
                                  Service,
                                  MissingComponent)


class FirstErrorLineTests(unittest.TestCase):

    def test_should_return_nothing_when_logging_is_not_enabled(self):
        self.assertEquals(first_error_line(None), "")

    @patch("yadtshell.util.open", create=True)
    def test_should_return_first_error_line(self, mock_open):
        mock_open.return_value = MagicMock(spec=file)
        mock_readlines_function = mock_open.return_value.__enter__.return_value.readlines
        mock_readlines_function.return_value = ["DEBUG: Some stuff",
                                                "INFO: Other stuff",
                                                "<a timestamp> ERROR: WTF happened",
                                                "DEBUG: debug output after an error"]

        self.assertEquals(
            first_error_line("/foo/bar"),
            "<a timestamp> ERROR: WTF happened"
        )

    @patch("yadtshell.util.open", create=True)
    def test_should_return_first_critical_line(self, mock_open):
        mock_open.return_value = MagicMock(spec=file)
        mock_readlines_function = mock_open.return_value.__enter__.return_value.readlines
        mock_readlines_function.return_value = ["DEBUG: Some stuff",
                                                "CRITICAL: uh oh, this is going to blow up",
                                                "INFO: Other stuff",
                                                "<a timestamp> ERROR: WTF happened",
                                                "DEBUG: debug output after an error"]

        self.assertEquals(
            first_error_line("/foo/bar"),
            "CRITICAL: uh oh, this is going to blow up"
        )

    @patch("yadtshell.util.open", create=True)
    def test_should_return_nothing_when_no_error_in_log(self, mock_open):
        mock_open.return_value = MagicMock(spec=file)
        mock_readlines_function = mock_open.return_value.__enter__.return_value.readlines
        mock_readlines_function.return_value = ["DEBUG: Some stuff",
                                                "INFO: Other stuff"]

        self.assertEquals(
            first_error_line("/foo/bar"),
            None
        )


class MissingServiceTests(unittest.TestCase):

    def test_should_return_missing_services(self):
        components = {
            'service://foo/exists': Service(Mock(), 'exists'),
            'service://foo/missing': MissingComponent('service://foo/missing'),
            'service://bar/missing': MissingComponent('service://bar/missing'),
            'artefact://bar/artefact': MissingComponent('artefact://bar/artefact')
        }

        missing_services = filter_missing_services(components)

        self.assertEquals(missing_services, [
            components['service://foo/missing'],
            components['service://bar/missing'],
        ])

    def test_should_return_empty_list_when_no_services_are_missing(self):
        components = {
            'service://foo/exists': Service(Mock(), 'exists'),
            'artefact://bar/artefact': MissingComponent('artefact://bar/artefact')
        }

        missing_services = filter_missing_services(components)

        self.assertEquals(missing_services, [])


class ServiceOrderingTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.components = yadtshell.components.ComponentDict()
        myhost = Host('foo.bar.com')
        self.otherhost = Host('foo.boing')
        self.bar_service = Service(myhost, 'barservice', {})
        self.baz_service = Service(myhost, 'bazservice', {})
        self.ack_service = Service(myhost, 'ackservice', {})

        self.components['service://foobar42/barservice'] = self.bar_service
        self.components['service://foobar42/bazservice'] = self.baz_service
        self.components['service://foobar42/ackservice'] = self.ack_service

    def test_inbound_deps_should_return_empty_list_when_service_is_not_needed(self):

        self.assertEqual(inbound_deps_on_same_host(
            self.bar_service, self.components), [])

    def test_inbound_deps_should_return_needing_service(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']

        self.assertEqual(
            inbound_deps_on_same_host(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_outbound_deps_should_return_empty_list_when_service_needs_nothing(self):
        self.assertEqual(outbound_deps_on_same_host(
            self.bar_service, self.components), [])

    def test_outbound_deps_should_return_needed_service(self):
        self.bar_service.needs = ['service://foobar42/bazservice']

        self.assertEqual(
            outbound_deps_on_same_host(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_should_compute_inbound_deps_recursively(self):
        self.ack_service.needed_by = ['service://foobar42/bazservice']
        self.baz_service.needed_by = ['service://foobar42/barservice']

        self.assertEqual(inbound_deps_on_same_host(self.ack_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/barservice'])

    def test_should_compute_outbound_deps_recursively(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        self.baz_service.needs = ['service://foobar42/ackservice']

        self.assertEqual(outbound_deps_on_same_host(self.bar_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/ackservice'])

    def test_should_label_standalone_services(self):
        compute_dependency_scores(self.components)
        self.assertEqual(
            self.baz_service.dependency_score, STANDALONE_SERVICE_RANK)

    def test_should_increase_dependency_score_when_ingoing_edge_found(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, 1)

    def test_should_decrease_dependency_score_when_outdoing_edge_found(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)

    def test_should_enable_and_decrease_dependency_score_based_on_edges(self):
        self.bar_service.needs = ['service://foobar42/bazservice']      # -1
        self.baz_service.needs = ['service://foobar42/ackservice']      # -1
        self.bar_service.needed_by = ['service://foobar42/ackservice']  # +1
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)

    def test_should_ignore_cross_host_inward_dependencies(self):
        self.components['service://otherhost/foo'] = Service(self.otherhost, 'foo', {})
        self.bar_service.needed_by = ['service://otherhost/foo']
        compute_dependency_scores(self.components)

    def test_should_ignore_cross_host_outward_dependencies(self):
        self.components['service://otherhost/foo'] = Service(self.otherhost, 'foo', {})
        self.bar_service.needs = ['service://otherhost/foo']
        compute_dependency_scores(self.components)
        self.assertEqual(
            self.bar_service.dependency_score, STANDALONE_SERVICE_RANK)


class IntervalAndDelayConversionTests(unittest.TestCase):

    def test_should_return_divisor_when_division_without_remainder_is_possible(self):
        max_tries = calculate_max_tries_for_interval_and_delay(10, 5)

        self.assertEqual(max_tries, 2)

    def test_should_increase_interval_when_remainder_found(self):
        max_tries = calculate_max_tries_for_interval_and_delay(10, 6)

        self.assertEqual(max_tries, 2)  # now waits 12 seconds instead of 10

    def test_should_at_least_make_one_try_when_delay_is_longer_than_interval(self):
        max_tries = calculate_max_tries_for_interval_and_delay(1, 5)

        self.assertEqual(max_tries, 1)

    def test_should_not_make_tries_when_interval_is_zero(self):
        max_tries = calculate_max_tries_for_interval_and_delay(0, 5)

        self.assertEqual(max_tries, 0)


class ServiceRenderingTests(unittest.TestCase):

    def setUp(self):
        self.mock_term = Mock()
        self.mock_render = Mock(side_effect=lambda unrendered: unrendered)
        yadtshell.settings.term = self.mock_term
        yadtshell.settings.term.render = self.mock_render

    def test_should_render_red_when_state_is_down(self):
        render_state(yadtshell.settings.DOWN, width=0)

        self.mock_render.assert_called_with('${RED}${BOLD}down${NORMAL}')

    def test_should_render_green_when_state_is_up(self):
        render_state(yadtshell.settings.UP, width=0)

        self.mock_render.assert_called_with('${GREEN}${BOLD}up${NORMAL}')

    def test_should_adjust_left_by_default(self):
        render_state(yadtshell.settings.UP, width=4)

        self.mock_render.assert_called_with('${GREEN}${BOLD}up  ${NORMAL}')

    def test_should_adjust_right(self):
        render_state(yadtshell.settings.UP, width=6, just='right')

        self.mock_render.assert_called_with('${GREEN}${BOLD}    up${NORMAL}')


class CurrentStateTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.OUT_DIR = '/out/dir/'

    @patch('yadtshell.util.os.path.getmtime')
    def test_should_return_mtime_of_current_state(self, mtime_function):
        mtime_function.return_value = 42

        self.assertEqual(get_mtime_of_current_state(), 42)

        mtime_function.assert_called_with('/out/dir/current_state.components')

    @patch('yadtshell.util.get_age_of_current_state_in_seconds')
    @patch('yadtshell.util.restore')
    def test_should_restore_current_state(self, restore_function, age_of_state):
        age_of_state.return_value = 0

        restore_current_state()

        restore_function.assert_called_with('/out/dir/current_state.components')

    @patch('yadtshell.util.get_age_of_current_state_in_seconds')
    @patch('yadtshell.util.restore')
    def test_should_raise_when_restored_state_is_too_old_and_must_be_fresh(self, _, age_of_state):
        age_of_state.return_value = 1337  # the limit is 600 for 10 minutes

        self.assertRaises(IOError, restore_current_state, must_be_fresh=True)

    @patch('yadtshell.util.get_age_of_current_state_in_seconds')
    @patch('yadtshell.util.restore')
    def test_should_not_raise_when_restored_state_is_too_old_and_must_not_be_fresh(self, _, age_of_state):
        age_of_state.return_value = 1337  # the limit is 600 for 10 minutes

        restore_current_state(must_be_fresh=False)  # this should not raise

    @patch('yadtshell.util.time.time')
    @patch('yadtshell.util.get_mtime_of_current_state')
    def test_should_return_age_of_state_in_seconds(self, mtime, time):
        mtime.return_value = 2
        time.return_value = 44

        self.assertEqual(get_age_of_current_state_in_seconds(), 42)


class LogExceptionsTests(unittest.TestCase):

    def test_should_passthrough_exceptions_when_decorated_with_unsafe(self):

        @log_exceptions(Mock())
        def boom():
            raise ValueError("Any error message")

        self.assertRaises(ValueError, boom)

    def test_should_log_exceptions_when_decorated_with_unsafe(self):
        mock_logger = Mock()

        @log_exceptions(mock_logger)
        def boom():
            raise ValueError("Any error message")

        try:
            boom()
        except ValueError:
            pass

        mock_logger.error.assert_called_with("Problem white running boom: Any error message")

    def test_should_preserve_docstring(self):
        @log_exceptions(Mock())
        def function_with_docstring():
            """ Any documentation
                Write what you want here
            """
            pass

        self.assertEqual(function_with_docstring.__doc__,
                         ' Any documentation\n'
                         '                Write what you want here\n'
                         '            ')

    def test_should_preserve_name(self):
        @log_exceptions(Mock())
        def any_function_name():
            pass

        self.assertEqual(any_function_name.__name__, "any_function_name")

    def test_should_passthrough_args_and_kwargs(self):
        function = Mock(__name__="function")
        decorated_function = log_exceptions(Mock())(function)

        decorated_function("any-positional-argument", any_keyword_argument="foo")

        function.assert_called_with("any-positional-argument", any_keyword_argument="foo")
