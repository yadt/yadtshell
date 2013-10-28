import unittest
from mock import Mock, patch

import yadtshell
from yadtshell.info import (highlight_differences,
                            compute_dependency_scores,
                            inbound_deps,
                            outbound_deps)

from unittest_support import (create_component_pool_for_one_host,
                              render_info_matrix_to_string)


class InfoMatrixRenderingTests(unittest.TestCase):

    def _patch_assert_in(self):
        try:
            self.assert_in = self.assertIn
        except AttributeError:
            def assert_in(element, container):
                if not element in container:
                    raise AssertionError(
                        '{0} not found in {1}'.format(element, container))
            self.assert_in = assert_in

    def setUp(self):
        self.he_patcher = patch(
            'yadtshell._info.hostexpand.HostExpander.HostExpander')
        self.he = self.he_patcher.start()
        self.he.return_value.expand = lambda hosts: [hosts]

        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'original_hosts': ['foobar42']}
        yadtshell.settings.VIEW_SETTINGS = {}
        self.mock_term = Mock()
        self.mock_render = lambda unrendered: unrendered
        yadtshell.settings.term = self.mock_term
        yadtshell.settings.term.render = self.mock_render

        self._patch_assert_in()

    def tearDown(self):
        self.he_patcher.stop()

    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('__builtin__.print')
    def _call_info_and_render_output_to_string(self, mock_print, mock_mtime):
        mock_mtime.return_value = 1
        yadtshell.info()
        return render_info_matrix_to_string(mock_print)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_unreachable_hosts(self,
                                             component_pool):
        components = yadtshell.components.ComponentDict()
        components['foobar42'] = yadtshell.components.UnreachableHost(
            'foobar42')

        component_pool.return_value = components
        info_matrix = self._call_info_and_render_output_to_string()

        expected_matrix = '''
${BG_RED}${WHITE}${BOLD}
  foobar42 is unreachable!
${NORMAL}

  f
  o
  o
  b
  a
  r
  4
  2

  ?  host uptodate
  ?  reboot required
  ?  host access
'''
        self.assert_in(expected_matrix, info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_running_services(self,
                                            component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE,
            add_services=True,
            service_state=yadtshell.settings.UP)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' |  service barservice', info_matrix)
        self.assert_in(' |  service bazservice', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_stopped_services(self,
                                            component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE,
            add_services=True,
            service_state=yadtshell.settings.DOWN)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' O  service barservice', info_matrix)
        self.assert_in(' O  service bazservice', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_uptodate_when_host_is_uptodate(self,
                                                          component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' |  host uptodate', info_matrix)
        self.assert_in('1/1 hosts uptodate', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_update_needed_when_host_is_not_uptodate(self,
                                                                   component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' u  host uptodate', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_reboot_after_update(self,
                                               component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED,
            host_reboot_after_update=True)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' r  reboot required', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_reboot_now(self,
                                      component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED,
            host_reboot_now=True)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(' R  reboot required', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_artefact_problems_when_state_is_not_up(self,
                                                                  component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED,
            artefact_state=yadtshell.settings.MISSING)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in('''
problems
${RED}${BOLD}   missing${NORMAL}  artefact://foobar42/yit/0:0.0.1
${RED}${BOLD}   missing${NORMAL}  artefact://foobar42/foo/0:0.0.0

''', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_host_locked_by_other(self,
                                                component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_locked_by_other=True)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in('''
${BG_RED}${WHITE}${BOLD}
  foobar42 is locked by foobar
    reason yes we can (lock the host)
${NORMAL}
''', info_matrix)

        self.assert_in(' L  host access', info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_host_locked_by_me(self,
                                             component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            host_locked_by_me=True)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in('''
${BG_YELLOW}${BOLD}
  foobar42 is locked by me
    reason yes we can (lock the host)
${NORMAL}
''', info_matrix)

        self.assert_in(' l  host access', info_matrix)

    @patch('time.time')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_matrix_for_one_host(self,
                                               component_pool,
                                               mock_time):
        mock_time.return_value = 1
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assertEqual(info_matrix,
                         '''
${BOLD}yadt info | test${NORMAL}

target status
  foobar42                                       yit  0:0.0.1
                       (next) ${REVERSE}foo${NORMAL}  0:0.0.${REVERSE}0${NORMAL}

  f
  o
  o
  b
  a
  r
  4
  2

  u  host uptodate
  |  reboot required
  |  host access

legend: | up(todate),accessible  O down  ? unknown  io? ignored (up,down,unknown)
        lL locked by me/other  u update pending
        rR reboot needed (after update/due to new kernel)

queried ${BG_GREEN}${WHITE}${BOLD}  0  ${NORMAL} seconds ago

status:   0%   0% | 0/0 services up, 0/1 hosts uptodate
''')


class ValidateHighlightingTest(unittest.TestCase):

    def test_should_highlight_nothing_when_no_difference(self):
        text = highlight_differences("foo", "foo")
        self.assertEqual("foo", text)

    def test_should_highlight_last_character_when_they_differ(self):
        text = highlight_differences("foo", "foX")
        self.assertEqual("fo${REVERSE}X${NORMAL}", text)

    def test_should_highlight_everything_when_strings_mismatch_totally(self):
        text = highlight_differences("foo", "bar")
        self.assertEqual("${REVERSE}bar${NORMAL}", text)

    def test_should_highlight_everything_when_strings_mismatch_in_first_position_only(self):
        text = highlight_differences("foo", "boo")
        self.assertEqual("${REVERSE}boo${NORMAL}", text)

    def test_should_highlight_every_but_the_first_character_when_strings_differ_in_position_two(self):
        text = highlight_differences("foo", "fXo")
        self.assertEqual("f${REVERSE}Xo${NORMAL}", text)

    def test_should_highlight_when_string_lengths_differ(self):
        text = highlight_differences("foo", "fo1234567890")
        self.assertEqual("fo${REVERSE}1234567890${NORMAL}", text)

    def test_should_highlight_when_string_lengths_differ_again(self):
        text = highlight_differences("fo1234567890", "foo")
        self.assertEqual("fo${REVERSE}o${NORMAL}", text)


class ServiceOrderingTests(unittest.TestCase):

    def setUp(self):
        self.components = yadtshell.components.ComponentDict()
        self.bar_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        self.baz_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        self.ack_service = yadtshell.components.Service(
            'foobar42', 'ackservice', {})

        self.components['service://foobar42/barservice'] = self.bar_service
        self.components['service://foobar42/bazservice'] = self.baz_service
        self.components['service://foobar42/ackservice'] = self.ack_service

    def test_inbound_deps_should_return_empty_list_when_service_is_not_needed(self):

        self.assertEqual(inbound_deps(self.bar_service, self.components), [])

    def test_inbound_deps_should_return_needing_service(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']

        self.assertEqual(inbound_deps(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_outbound_deps_should_return_empty_list_when_service_needs_nothing(self):
        self.assertEqual(outbound_deps(self.bar_service, self.components), [])

    def test_outbound_deps_should_return_needed_service(self):
        self.bar_service.needs = ['service://foobar42/bazservice']

        self.assertEqual(outbound_deps(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_should_compute_inbound_deps_recursively(self):
        self.ack_service.needed_by = ['service://foobar42/bazservice']
        self.baz_service.needed_by = ['service://foobar42/barservice']

        self.assertEqual(inbound_deps(self.ack_service, self.components), ['service://foobar42/bazservice', 'service://foobar42/barservice'])

    def test_should_compute_outbound_deps_recursively(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        self.baz_service.needs = ['service://foobar42/ackservice']

        self.assertEqual(outbound_deps(self.bar_service, self.components), ['service://foobar42/bazservice', 'service://foobar42/ackservice'])
