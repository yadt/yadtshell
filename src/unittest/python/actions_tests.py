import unittest
from mock import Mock

import yadtshell


class ActionPlanTests(unittest.TestCase):

    def test_should_remove_actions_on_unhandled_hosts(self):
        actions = [
            yadtshell.actions.Action('start', 'service://cowsay/service0'),
            yadtshell.actions.Action('start', 'service://foobar/service1'),
            yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        mock_service0 = Mock()
        mock_service0.host_uri = 'host://cowsay'
        mock_service1 = Mock()
        mock_service1.host_uri = 'host://foobar'
        mock_service2 = Mock()
        mock_service2.host_uri = 'host://foobaz'
        components = {'service://cowsay/service0': mock_service0,
                      'service://foobar/service1': mock_service1,
                      'service://foobaz/service2': mock_service2}

        handled_hosts = ['host://foobar']
        plan.remove_actions_on_unhandled_hosts(handled_hosts, components)

        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].uri, 'service://foobar/service1')

    def test_should_not_affect_actions_on_handled_hosts(self):
        actions = [yadtshell.actions.Action(
            'start', 'service://foobar/service1'),
            yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        mock_service1 = Mock()
        mock_service1.host_uri = 'host://foobar'
        mock_service2 = Mock()
        mock_service2.host_uri = 'host://foobaz'
        components = {'service://foobar/service1': mock_service1,
                      'service://foobaz/service2': mock_service2}

        handled_hosts = ['host://foobar', 'host://foobaz']
        plan.remove_actions_on_unhandled_hosts(handled_hosts, components)

        self.assertEqual(len(plan.actions), 2)
        self.assertEqual(plan.actions[0].uri, 'service://foobar/service1')
        self.assertEqual(plan.actions[1].uri, 'service://foobaz/service2')

    def test_should_not_be_empty_when_actions_in_plan(self):
        actions = [yadtshell.actions.Action(
            'start', 'service://foobar/service1'),
            yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        self.assertEqual(plan.is_not_empty, True)

    def test_should_be_empty_when_no_actions_in_plan(self):
        actions = []
        plan = yadtshell.actions.ActionPlan('plan', actions)

        self.assertEqual(plan.is_empty, True)

    def test_should_dump_meta_info_for_sequential_plan(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_workers=1)

        self.assertEqual(plan.meta_info(), '0 items, sequential, 0 errors tolerated')

    def test_should_dump_meta_info_for_parallel_plan(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_workers=3)

        self.assertEqual(plan.meta_info(), '0 items, 3 workers, 0 errors tolerated')

    def test_should_dump_meta_info_for_undefined_worker_count(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_workers=None)

        self.assertEqual(plan.meta_info(), '0 items, workers *undefined*, 0 errors tolerated')

    def test_should_dump_meta_info_for_several_actions(self):
        actions = [yadtshell.actions.Action('start', 'service://foobar/service1'),
            yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        self.assertEqual(plan.meta_info(), '2 items, workers *undefined*, 0 errors tolerated')

    def test_should_dump_meta_info_for_increased_error_tolerance(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_errors_tolerated=4)

        self.assertEqual(plan.meta_info(), '0 items, workers *undefined*, 4 errors tolerated')
