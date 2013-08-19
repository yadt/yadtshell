from unittest import TestCase
from mock import Mock, patch

import yadtshell

from yadtshell.actionmanager import ActionManager


class ActionManagerActionTests(TestCase):

    def user_declines_transaction(self):
        yadtshell.actionmanager.confirm_transaction_by_user = lambda: False

    def user_accepts_transaction(self):
        yadtshell.actionmanager.confirm_transaction_by_user = lambda: True

    @patch('yadtshell.actionmanager.logging')
    def setUp(self, mock_logging):
        yadtshell.settings.ybc = Mock()
        yadtshell.settings.log_file = Mock()
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.am = ActionManager()

    @patch('yadtshell.actionmanager.print', create=True)
    @patch('yadtshell.actionmanager.sys.stdout')
    @patch('yadtshell.twisted.stop_and_return')
    @patch('yadtshell.actionmanager.yaml.load')
    @patch('yadtshell.actionmanager.open', create=True)
    @patch('yadtshell.util.restore_current_state')
    def test_should_abort_when_user_cancels(self,
                                            components,
                                            mock_open,
                                            mock_load_action_plan,
                                            mock_stop_and_return,
                                            mock_stdout,
                                            _):
        mock_stdout.isatty.return_value = True
        noop = Mock()
        noop.cmd = 'harmless'
        dangerous = Mock()
        dangerous.cmd = 'reboot'
        mock_load_action_plan.return_value.list_actions = [noop, dangerous]
        self.user_declines_transaction()

        self.am.action('update')

        mock_stop_and_return.assert_called_with(
            yadtshell.commandline.EXIT_CODE_CANCELED_BY_USER)

    @patch('yadtshell.actionmanager.print', create=True)
    @patch('yadtshell.actionmanager.sys.stdout')
    @patch('yadtshell.twisted.stop_and_return')
    @patch('yadtshell.actionmanager.yaml.load')
    @patch('yadtshell.actionmanager.open', create=True)
    @patch('yadtshell.util.restore_current_state')
    def test_should_not_abort_when_user_confirms(self,
                                                 components,
                                                 mock_open,
                                                 mock_load_action_plan,
                                                 mock_stop_and_return,
                                                 mock_stdout,
                                                 _):
        mock_stdout.isatty.return_value = True
        noop = Mock()
        noop.cmd = 'harmless'
        dangerous = Mock()
        dangerous.cmd = 'reboot'
        mock_load_action_plan.return_value.list_actions = [noop, dangerous]
        self.user_accepts_transaction()

        self.am.action('update')

        self.assertFalse(mock_stop_and_return.called)

    @patch('yadtshell.actionmanager.print', create=True)
    @patch('yadtshell.actionmanager.confirm_transaction_by_user')
    @patch('yadtshell.actionmanager.sys.stdout')
    @patch('yadtshell.twisted.stop_and_return')
    @patch('yadtshell.actionmanager.yaml.load')
    @patch('yadtshell.actionmanager.open', create=True)
    @patch('yadtshell.util.restore_current_state')
    def test_should_not_prompt_when_no_tty(self,
                                           components,
                                           mock_open,
                                           mock_load_action_plan,
                                           mock_stop_and_return,
                                           mock_stdout,
                                           mock_transaction,
                                           _):
        mock_stdout.isatty.return_value = False
        noop = Mock()
        noop.cmd = 'harmless'
        dangerous = Mock()
        dangerous.cmd = 'reboot'
        mock_load_action_plan.return_value.list_actions = [noop, dangerous]
        self.user_accepts_transaction()

        self.am.action('update')

        self.assertFalse(mock_transaction.called)
