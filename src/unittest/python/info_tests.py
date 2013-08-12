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

    def _render_info_matrix_to_string(self, mock_print):
        info_matrix = StringIO()
        for call in mock_print.call_args_list:
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
    def test_should_render_matrix_for_one_host(self, mock_state, mock_mtime, mock_print):
        components = yadtshell.components.ComponentDict()
        host = yadtshell.components.Host('foobar42')
        host.state = 'update_needed'
        foo_artefact = yadtshell.components.Artefact(
            'foobar42', 'foo', '0:0.0.0')
        yit_artefact = yadtshell.components.Artefact(
            'foobar42', 'yit', '0:0.0.1')
        host.next_artefacts = {'foo/0:0.0.0': 'yit/0:0.0.1'}
        host.hostname = 'foobar42'
        components['foobar42'] = host
        components['artefact://foobar42/foo/0:0.0.0'] = foo_artefact
        components['artefact://foobar42/yit/0:0.0.1'] = yit_artefact
        mock_state.return_value = components

        yadtshell.info()
        info_matrix = self._render_info_matrix_to_string(mock_print)

        self.assertEqual(info_matrix,
                         '''
${BOLD}yadt info | test${NORMAL}

target status
  foobar42                                       yit  0:0.0.1
                       (next) ${REVERSE}foo${NORMAL}  0:0.0.${REVERSE}0${NORMAL}

problems
${RED}${BOLD}   unknown${NORMAL}  artefact://foobar42/yit/0:0.0.1
${RED}${BOLD}   unknown${NORMAL}  artefact://foobar42/foo/0:0.0.0

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
