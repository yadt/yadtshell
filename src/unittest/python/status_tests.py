import yadtshell
import unittest
from mock import Mock, patch, call


class StatusTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.ybc = Mock()
        yadtshell.settings.SSH = 'ssh'
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_globbed_old_state_files_when_calling_status_without_hosts(self, os, glob):
        yadtshell.status()

        os.path.join.assert_called_with(
            yadtshell.settings.OUT_DIR, 'current_state*')
        os.remove.assert_called_with(os.path.join.return_value)

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_old_state_files_explicity_when_calling_status_with_hosts(self, os, glob):
        yadtshell.status(hosts=['foobar42'])

        os.path.join.assert_called_with(
            yadtshell.settings.OUT_DIR, 'current_state_foobar42.yaml')
        os.remove.assert_called_with(os.path.join.return_value)

    @patch('yadtshell.twisted.ProgressIndicator')
    @patch('yadtshell._status.query_status')
    @patch('yadtshell._status.os')
    def test_should_setup_deferred_list_with_two_hosts(self, _, query_status, pi):
        yadtshell.status(hosts=['foobar42', 'foobar43'])

        self.assertEqual(query_status.call_args_list, [
            call('foobar42', pi.return_value),
            call('foobar43', pi.return_value)])
