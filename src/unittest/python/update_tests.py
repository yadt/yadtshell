import yadtshell
from yadtshell.update import compare_versions, get_all_adjacent_needed_hosts
from unittest_support import create_component_pool_for_one_host

import unittest
from mock import patch, Mock


class AdjacentNeededHostsTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'original_hosts': ['thehost']}

        self.components = yadtshell.components.ComponentDict()
        self.host = yadtshell.components.Host('thehost')
        self.service = yadtshell.components.Service(self.host, 'theservice', {})
        self.components['host://thehost'] = self.host
        self.components['service://thehost/theservice'] = self.service
        other_host = yadtshell.components.Host('otherhost')
        self.components['host://otherhost'] = other_host
        self.components['service://otherhost/otherservice'] = yadtshell.components.Service(other_host, 'otherservice', {})

    def test_should_include_immediate_host_from_service(self):
        self.service.needs = ['host://thehost']

        adjacent_hosts = get_all_adjacent_needed_hosts(self.service.uri, self.components)

        self.assertEqual(adjacent_hosts, set(['host://thehost']))

    def test_should_include_adjacent_hosts_when_service_has_service_dependencies(self):
        self.service.needs = ['service://otherhost/otherservice']

        adjacent_hosts = get_all_adjacent_needed_hosts(self.service.uri, self.components)

        self.assertEqual(adjacent_hosts, set(['host://otherhost']))

    def test_should_include_hosts_from_host_and_service_dependencies(self):
        self.service.needs = ['host://thehost', 'service://otherhost/otherservice']

        adjacent_hosts = get_all_adjacent_needed_hosts(self.service.uri, self.components)

        self.assertEqual(adjacent_hosts, set(['host://otherhost', 'host://thehost']))


class UpdateTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'original_hosts': ['foobar42']}
        yadtshell.settings.VIEW_SETTINGS = {}
        yadtshell.update.logger = Mock()

    @patch('yadtshell.util.dump_action_plan')
    @patch('yadtshell.metalogic.apply_instructions')
    @patch('yadtshell.actions.ActionPlan')
    @patch('yadtshell.util.restore_current_state')
    def test_should_not_update_anything_when_hosts_are_uptodate(self, components, action_plan, apply_instructions, dump_action_plan):
        components.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPTODATE)

        compare_versions()

        dump_action_plan.assert_called_with('update', action_plan.return_value)
        action_plan.assert_called_with('start', set([]))

    @patch('yadtshell.actions.Action')
    @patch('yadtshell.util.dump_action_plan')
    @patch('yadtshell.metalogic.apply_instructions')
    @patch('yadtshell.actions.ActionPlan')
    @patch('yadtshell.util.restore_current_state')
    def test_should_update_host_when_host_is_not_uptodate(self, components, action_plan, apply_instructions, dump_action_plan, action):
        components.return_value = create_component_pool_for_one_host(
            host_state=yadtshell.settings.UPDATE_NEEDED,
            next_artefacts_present=True)

        compare_versions()

        action.assert_called_with('update', 'host://foobar42', 'state', 'uptodate')
