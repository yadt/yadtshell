from unittest import TestCase
from mock import Mock, patch

import yadtshell

from yadtshell.actionmanager import (ActionManager,
                                     _user_should_acknowledge_plan)


class ActionManagerHelperFunctionsTest(TestCase):

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_not_prompt_when_terminal_is_not_a_tty(self,
                                                          mock_sys):
        mock_sys.isatty.return_value = False

        self.assertFalse(_user_should_acknowledge_plan(dryrun=False, flavor='update'))

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_prompt_when_terminal_is_a_tty(self,
                                                  mock_sys):
        mock_sys.isatty.return_value = True

        self.assertTrue(_user_should_acknowledge_plan(dryrun=False, flavor='update'))

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_not_prompt_when_terminal_is_a_tty_but_dryrun_is_true(self,
                                                                         mock_sys):
        mock_sys.isatty.return_value = True

        self.assertFalse(_user_should_acknowledge_plan(dryrun=True, flavor='update'))


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
