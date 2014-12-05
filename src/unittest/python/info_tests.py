import unittest
from mock import Mock, patch

import yadtshell
from yadtshell.info import (
    highlight_differences, calculate_info_view_settings)

from unittest_support import (create_component_pool_for_one_host,
                              render_info_matrix_to_string)


class CalculateInfoViewSettings(unittest.TestCase):

    def setUp(self):
        self.popen_patcher = patch('yadtshell._info.Popen')
        self.popen = self.popen_patcher.start()

    def tearDown(self):
        self.popen_patcher.stop()

    @patch('yadtshell.settings')
    def test_calculate_width_when_stty_fails(self, settings_mock):
        self.popen.return_value.communicate.return_value = (None, 1)
        settings_mock.TARGET_SETTINGS = {'original_hosts': [
            'foo01 foo02 foo03 foo04 foo05 foo06 foo07 foo08']}
        expected = ['matrix', 'color', '3cols']
        result = calculate_info_view_settings()
        self.assertEqual(result, expected)

    @patch('yadtshell.settings')
    def test_calculate_width_maxcols(self, settings_mock):
        self.popen.return_value.communicate.return_value = ('999 999', 0)
        settings_mock.TARGET_SETTINGS = {'original_hosts': [
            'foo01', 'foo02 foo03', 'foo04 foo05 foo06', 'foo07 foo08']}
        expected = ['matrix', 'color', 'maxcols']
        result = calculate_info_view_settings()
        self.assertEqual(result, expected)

    @patch('yadtshell.settings')
    def test_calculate_width_3cols(self, settings_mock):
        self.popen.return_value.communicate.return_value = ('999 52', 0)
        settings_mock.TARGET_SETTINGS = {'original_hosts': [
            'foo01', 'foo02 foo03', 'foo04 foo05 foo06', 'foo07 foo08']}
        expected = ['matrix', 'color', '3cols']
        result = calculate_info_view_settings()
        self.assertEqual(result, expected)

    @patch('yadtshell.settings')
    def test_calculate_width_1col(self, settings_mock):
        self.popen.return_value.communicate.return_value = ('999 1', 0)
        settings_mock.TARGET_SETTINGS = {'original_hosts': [
            'foo01', 'foo02 foo03', 'foo04 foo05 foo06', 'foo07 foo08']}
        expected = ['matrix', 'color', '1col']
        result = calculate_info_view_settings()
        self.assertEqual(result, expected)

    @patch('yadtshell.settings')
    @patch('yadtshell._info.hostexpand.HostExpander.HostExpander.expand')
    def test_calculate_width_when_regular_expr_is_in_orig_hosts(self, he_mock, settings_mock):
        he_mock.return_value = xrange(0, 40)
        self.popen.return_value.communicate.return_value = ('999 80', 0)
        settings_mock.TARGET_SETTINGS = {'original_hosts': [
            'foo01', 'foo02 foo03', 'foo[4..44]', 'foo45 foo46']}
        expected = ['matrix', 'color', '1col']
        result = calculate_info_view_settings()
        self.assertEqual(result, expected)


class InfoMatrixRenderingTests(unittest.TestCase):

    def _patch_assert_in(self):
        def assert_in(element, container):
            if element not in container:
                separator_start = "< " * 36
                separator_end = "> " * 36

                raise AssertionError("""
                     Expected to find
{2}
{0}
{3}

                     in

{2}
{1}
{3}
                     """.format(element, container, separator_start, separator_end))
        self.assert_in = assert_in

    def setUp(self):
        self.he_patcher = patch(
            'yadtshell._info.hostexpand.HostExpander.HostExpander')
        self.he = self.he_patcher.start()
        self.he.return_value.expand = lambda hosts: [hosts]

        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'original_hosts': ['foobar42']}
        yadtshell._info.calculate_info_view_settings = lambda *args: {}
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
    def test_should_render_readonly_services(self,
                                             component_pool):
        component_pool.return_value = create_component_pool_for_one_host(add_readonly_services=True)

        info_matrix = self._call_info_and_render_output_to_string()

        rendered_ro_services = '''
  foobar42

  |  readonly-service ro_up (needed by me you)
  O  readonly-service ro_down (needed by something a_dog)
'''

        self.assert_in(rendered_ro_services,
                       info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_missing_artefact_problems(self,
                                                     component_pool):
        component_pool.return_value = create_component_pool_for_one_host(
            missing_artefact=True)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in(
            "config problem: missing artefact://foobar42/missing",
            info_matrix)

    @patch('yadtshell.util.restore_current_state')
    def test_should_render_colored_readonly_services(self,
                                                     component_pool):
        yadtshell._info.calculate_info_view_settings = lambda *args: {'color': 'yes'}
        component_pool.return_value = create_component_pool_for_one_host(add_readonly_services=True)

        info_matrix = self._call_info_and_render_output_to_string()

        rendered_ro_services = '''
  foobar42

  ${BG_GREEN}${WHITE}${BOLD}|${NORMAL}  readonly-service ro_up (needed by me you)
  ${BG_RED}${WHITE}${BOLD}O${NORMAL}  readonly-service ro_down (needed by something a_dog)
'''

        self.assert_in(rendered_ro_services,
                       info_matrix)

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

    @patch('yadtshell.util.get_age_of_current_state_in_seconds')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_cache_in_green_when_it_is_fresh(self,
                                                           component_pool,
                                                           cache_age):
        cache_age.return_value = 42
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in("queried ${BG_GREEN}${WHITE}${BOLD}  42  ${NORMAL} seconds ago",
                       info_matrix)

    @patch('yadtshell.util.get_age_of_current_state_in_seconds')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_cache_in_red_when_it_is_old(self,
                                                       component_pool,
                                                       cache_age):
        cache_age.return_value = 900
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        info_matrix = self._call_info_and_render_output_to_string()

        self.assert_in("queried ${BG_RED}${WHITE}${BOLD}  900  ${NORMAL} seconds ago",
                       info_matrix)

    @patch('time.time')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_matrix_for_one_host(self,
                                               component_pool,
                                               mock_time):
        mock_time.return_value = 1
        component_pool.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        info_matrix = self._call_info_and_render_output_to_string()

        expected = '''
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
'''

        self.assert_in(expected, info_matrix)
        self.assertEqual(expected, info_matrix)


class ValidateHighlightingTests(unittest.TestCase):

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
