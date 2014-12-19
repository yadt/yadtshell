# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2014  Immobilien Scout GmbH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import yadtshell
from yadtshell import reboot
from yadtshell.actions import Action, TargetState
from unittest_support import create_component_pool_for_one_host

from mock import patch, Mock

from unittest import TestCase
from logging import CRITICAL


class SilencedLoggerTestCase(TestCase):

    def setUp(self):
        self.reboot_logger = yadtshell._reboot.logger
        self.reboot_logger_level = self.reboot_logger.level
        self.reboot_logger.setLevel(CRITICAL)

    def tearDown(self):
        self.reboot_logger.setLevel(self.reboot_logger_level)


class RebootValidationTests(SilencedLoggerTestCase):

    def test_should_raise_error_when_rebooting_service(self):
        try:
            reboot(uris=["service://not-a-host"])
        except BaseException as e:
            self.assertEqual(str(e), "Cannot reboot service://not-a-host")
        else:
            self.fail("No exception raised while trying to reboot a service")

    def test_should_raise_error_when_rebooting_artefact(self):
        try:
            reboot(uris=["artefact://not-a-host"])
        except BaseException as e:
            self.assertEqual(str(e), "Cannot reboot artefact://not-a-host")
        else:
            self.fail("No exception raised while trying to reboot an artefact")


class RebootActionsTest(TestCase):

    def setUp(self):
        self.host = Mock(defined_services=[
            Mock(uri="service://service1"),
            Mock(uri="service://service2")])

        self.reboot_action = yadtshell._reboot.create_reboot_action_for(self.host)

    def test_should_require_stopped_services_on_host_when_rebooting_it(self):
        preconditions = self.reboot_action.preconditions
        self.assertEqual(len(preconditions), 2)
        precondition_uri_attr_target = [(p.uri, p.attr, p.target_value) for p in preconditions]
        self.assertEqual(sorted(precondition_uri_attr_target), [
            ('service://service1', 'state', 'down'),
            ('service://service2', 'state', 'down')])

    def test_should_create_update_action_with_required_reboot_when_rebooting(self):
        self.assertEqual(self.reboot_action.cmd, 'update')
        self.assertEqual(self.reboot_action.kwargs['reboot_required'], True)

    def test_should_disable_artefact_upgrade_when_rebooting_host(self):
        self.assertEqual(self.reboot_action.kwargs['upgrade_packages'], False)


class StopPlanTests(TestCase):

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    def test_should_stop_no_services_when_host_has_no_services(self, state):
        state.return_value = create_component_pool_for_one_host()

        stop_plan = yadtshell._reboot.create_plan_to_stop_all_services_on(["host://foobar42"])

        self.assertEqual(stop_plan.actions, ())

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    def test_should_stop_all_services(self, state):
        state.return_value = create_component_pool_for_one_host(add_services=True)

        stop_plan = yadtshell._reboot.create_plan_to_stop_all_services_on(["host://foobar42"])

        self.assertEqual(stop_plan.dump(),
                         'stop [2 items, workers *undefined*, 0 errors tolerated]:\n'
                         '    stop the service://foobar42/barservice, set state to "down"\n'
                         '    stop the service://foobar42/bazservice, set state to "down"\n')

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    def test_should_stop_all_services_without_preconditions(self, state):
        state.return_value = create_component_pool_for_one_host(add_services=True)

        stop_plan = yadtshell._reboot.create_plan_to_stop_all_services_on(["host://foobar42"])

        for stop_action in stop_plan.list_actions:
            self.assertEqual(stop_action.cmd, "stop")
            self.assertEqual(stop_action.preconditions, set([]))


class StartAfterRebootPlanTests(TestCase):

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    def test_should_start_all_services_once_host_is_set_to_rebooted(self, state):
        components = create_component_pool_for_one_host(add_services=True)
        state.return_value = components

        start_plan = yadtshell._reboot.create_plan_to_start_services_after_rebooting(["service://foobar42/barservice", "service://foobar42/bazservice"],
                                                                                     ["host://foobar42"], components)

        self.assertEqual(start_plan.dump(),
                         'start [2 items, workers *undefined*, 0 errors tolerated]:\n'
                         '    start the service://foobar42/barservice, set state to "up"\n'
                         '        when state of host://foobar42 is "rebooted"\n'
                         '    start the service://foobar42/bazservice, set state to "up"\n'
                         '        when state of host://foobar42 is "rebooted"\n')

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    def test_should_start_services_unconditionally_when_other_host_is_rebooted(self, state):
        components = create_component_pool_for_one_host(add_services=True)
        state.return_value = components

        start_plan = yadtshell._reboot.create_plan_to_start_services_after_rebooting(["service://foobar42/barservice", "service://foobar42/bazservice"],
                                                                                     ["host://foobar43"], components)

        self.assertEqual(start_plan.dump(),
                         'start [2 items, workers *undefined*, 0 errors tolerated]:\n'
                         '    start the service://foobar42/barservice, set state to "up"\n'
                         '    start the service://foobar42/bazservice, set state to "up"\n')


class RebootActionPlanTests(SilencedLoggerTestCase):

    def test_should_raise_exception_when_uri_is_a_service(self):
        self.assertRaises(ValueError, reboot, uris=["service://foobar42/barservice"])

    def test_should_raise_exception_when_uri_is_an_artefact(self):
        self.assertRaises(ValueError, reboot, uris=["artefact://foobar42/foo/0:0.0.0"])

    @patch("yadtshell.metalogic.yadtshell.util.restore_current_state")
    @patch("yadtshell._reboot.restore_current_state")
    @patch("yadtshell._reboot.dump_action_plan")
    def test_should_stop_services_then_reboot_then_start_services(self,
                                                                  dump_plan,
                                                                  state_reboot,
                                                                  state_metalogic):
        components = create_component_pool_for_one_host(add_services=True)
        state_reboot.return_value = components
        state_metalogic.return_value = state_reboot.return_value

        reboot(uris=["host://foobar42"])

        dump_plan_calls = dump_plan.call_args_list
        self.assertEqual(len(dump_plan_calls), 1, "More than one plan for reboot was serialized! (potential overwrite)")
        dump_plan_call = dump_plan_calls[0]
        dump_plan_call_name, dump_plan_args = dump_plan_call[0]
        actual_reboot_plan = dump_plan_args

        # Careful, there's no missing comma here (string concatenation)
        expected_actions = [
            Action("update", "host://foobar42", "state", "rebooted",
                   kwargs={"reboot_required": True, "upgrade_packages": False},
                   preconditions=[
                       TargetState("service://foobar42/bazservice", "state", "down"),
                       TargetState("service://foobar42/barservice", "state", "down")]),
            Action("start", "service://foobar42/barservice", "state", "up",
                   preconditions=[
                       TargetState("host://foobar42", "state", "rebooted")]),
            Action("start", "service://foobar42/bazservice", "state", "up",
                   preconditions=[
                       TargetState("host://foobar42", "state", "rebooted")]),
            Action("stop", "service://foobar42/barservice", "state", "down"),
            Action("stop", "service://foobar42/bazservice", "state", "down")
        ]

        assert_actual_plan_matches_expected_actions(self, expected_actions, actual_reboot_plan)


def assert_actual_plan_matches_expected_actions(self, expected_actions, actual_plan):
    self.assertEqual(len(expected_actions), greedy_len(actual_plan.list_actions))
    for position, expected_action in enumerate(expected_actions):
        self.assertTrue(expected_action in actual_plan.list_actions,
                        "Expected %s, but not found in:\n%s" % (expected_action,
                                                                actual_plan.dump()))


def greedy_len(generator):
    return len([item for item in generator])
