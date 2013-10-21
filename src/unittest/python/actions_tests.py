import unittest
from mock import Mock

import yadtshell


class ActionsTests(unittest.TestCase):
    def test_should_remove(self):
        actions = [yadtshell.actions.Action('start', 'service://foobar/service1'), yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        mock_service1 = Mock()
        mock_service1.host_uri = 'host://foobar'
        mock_service2 = Mock()
        mock_service2.host_uri = 'host://foobaz'
        components = {'service://foobar/service1': mock_service1,
                      'service://foobaz/service2': mock_service2}

        handled_hosts = ['host://foobar']
        plan.remove_actions_on_unhandled_hosts(handled_hosts, components)

        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].uri, 'service://foobar/service1')
