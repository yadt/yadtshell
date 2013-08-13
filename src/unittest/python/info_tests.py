import unittest
from StringIO import StringIO
from mock import Mock, patch

import yadtshell
from yadtshell.info import (highlight_differences)


class InfoMatrixRenderingTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'original_hosts': ['foobar42']}
        yadtshell.settings.VIEW_SETTINGS = {}
        self.mock_term = Mock()
        self.mock_render = lambda unrendered: unrendered
        yadtshell.settings.term = self.mock_term
        yadtshell.settings.term.render = self.mock_render

    def _create_component_pool_for_one_host(self,
                                            host_state,
                                            add_services=False,
                                            service_state=yadtshell.settings.UP,
                                            host_reboot_after_update=False,
                                            host_reboot_now=False):
        components = yadtshell.components.ComponentDict()
        host = yadtshell.components.Host('foobar42')
        host.state = host_state
        host.reboot_required_after_next_update = host_reboot_after_update
        host.reboot_required_to_activate_latest_kernel = host_reboot_now
        host.hostname = 'foobar42'
        components['foobar42'] = host

        foo_artefact = yadtshell.components.Artefact(
            'foobar42', 'foo', '0:0.0.0')
        foo_artefact.state = yadtshell.settings.UP
        yit_artefact = yadtshell.components.Artefact(
            'foobar42', 'yit', '0:0.0.1')
        yit_artefact.state = yadtshell.settings.UP
        host.next_artefacts = {'foo/0:0.0.0': 'yit/0:0.0.1'}
        components['artefact://foobar42/foo/0:0.0.0'] = foo_artefact
        components['artefact://foobar42/yit/0:0.0.1'] = yit_artefact

        if add_services:
            host.services = ['barservice', 'bazservice']
            bar_service = yadtshell.components.Service(
                'foobar42', 'barservice', {})
            bar_service.state = service_state
            baz_service = yadtshell.components.Service(
                'foobar42', 'barservice', {})
            baz_service.state = service_state
            components['service://foobar42/barservice'] = bar_service
            components['service://foobar42/bazservice'] = baz_service

        return components

    def _render_info_matrix_to_string(self, mocked_info_output):
        info_matrix = StringIO()
        for call in mocked_info_output.call_args_list:
            try:
                info_matrix.write(call[0][0])
            except:
                pass
            info_matrix.write('\n')
        info_matrix_string = info_matrix.getvalue()
        info_matrix.close()
        return info_matrix_string

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_running_services(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE, add_services=True, service_state=yadtshell.settings.UP)
        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' |  service barservice' in info_matrix)
        self.assertTrue(' |  service bazservice' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_stopped_services(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE, add_services=True, service_state=yadtshell.settings.DOWN)
        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' O  service barservice' in info_matrix)
        self.assertTrue(' O  service bazservice' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_uptodate_when_host_is_uptodate(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE)

        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' |  host uptodate' in info_matrix)
        self.assertTrue('1/1 hosts uptodate' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_update_needed_when_host_is_not_uptodate(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' u  host uptodate' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_reboot_after_update(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED, host_reboot_after_update=True)
        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' r  reboot required' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_reboot_now(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED, host_reboot_now=True)
        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
        self.assertTrue(' R  reboot required' in info_matrix)

    @patch('__builtin__.print')
    @patch('yadtshell.util.get_mtime_of_current_state')
    @patch('yadtshell.util.restore_current_state')
    def test_should_render_matrix_for_one_host(self, component_pool, _, mocked_info_output):
        component_pool.return_value = self._create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED)

        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mocked_info_output)
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

queried ${BG_RED}${WHITE}${BOLD}  1  ${NORMAL} seconds ago

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
