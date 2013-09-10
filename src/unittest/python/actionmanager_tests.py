from unittest import TestCase
from mock import MagicMock, Mock, patch

import yadtshell

from yadtshell.actionmanager import (ActionManager,
                                     _user_should_acknowledge_plan)


class ActionManagerTestBase(TestCase):

    @patch('yadtshell.actionmanager.logging')
    def setUp(self, mock_logging):
        yadtshell.settings.ybc = Mock()
        yadtshell.settings.log_file = Mock()
        yadtshell.settings.SSH = 'ssh'
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.am = ActionManager()


class ActionManagerHelperFunctionsTest(ActionManagerTestBase):

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_not_prompt_when_forcedyes_is_true(self,
                                                      mock_stdout):
        mock_stdout.isatty.return_value = True
        self.assertFalse(_user_should_acknowledge_plan(
            dryrun=False,
            flavor='update',
            forcedyes=True))

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_not_prompt_when_terminal_is_not_a_tty(self,
                                                          mock_sys):
        mock_sys.isatty.return_value = False

        self.assertFalse(
            _user_should_acknowledge_plan(dryrun=False, flavor='update', forcedyes=False))

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_prompt_when_terminal_is_a_tty(self,
                                                  mock_sys):
        mock_sys.isatty.return_value = True

        self.assertTrue(
            _user_should_acknowledge_plan(dryrun=False, flavor='update', forcedyes=False))

    @patch('yadtshell.actionmanager.sys.stdout')
    def test_should_not_prompt_when_terminal_is_a_tty_but_dryrun_is_true(self,
                                                                         mock_sys):
        mock_sys.isatty.return_value = True

        self.assertFalse(
            _user_should_acknowledge_plan(dryrun=True, flavor='update', forcedyes=False))


class ActionManagerHandleTests(ActionManagerTestBase):

    @patch('yadtshell.ActionManager.Task')
    @patch('yadtshell.defer.DeferredPool')
    def test_should_instantiate_deferred_pool_according_to_action(self,
                                                                  mock_deferred_pool,
                                                                  mock_task):
        new_task = Mock()
        mock_task.return_value = new_task
        action = yadtshell.actions.Action('stop', 'host://foobar42')
        self.am.handle(action)

        mock_deferred_pool.assert_called_with(
            '/ stop@host://foobar42', [new_task])
        mock_task.assert_called_with(
            fun=self.am.handle_action, action=action, path=[' stop@host://foobar42'])

    @patch('yadtshell.ActionManager.Task')
    @patch('yadtshell.defer.DeferredPool')
    def test_should_instantiate_deferred_pool_according_to_plan(self,
                                                                mock_deferred_pool,
                                                                mock_task):
        plan = MagicMock(spec=list)
        plan.actions = [Mock()]
        plan.nr_workers = 99
        plan.nr_errors_tolerated = 2
        plan.name = 'update'
        plan.meta_info = Mock()
        self.am.handle(plan)

        mock_deferred_pool.assert_called_with(
            '/update',
            [mock_task.return_value],
            nr_errors_tolerated=2,
            nr_workers=1,
            next_task_fun=self.am.next_with_preconditions)


class ActionManagerActionTests(ActionManagerTestBase):

    def user_declines_transaction(self):
        yadtshell.actionmanager.confirm_transaction_by_user = lambda: False

    def user_accepts_transaction(self):
        yadtshell.actionmanager.confirm_transaction_by_user = lambda: True

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
        dangerous.cmd = 'update'
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
