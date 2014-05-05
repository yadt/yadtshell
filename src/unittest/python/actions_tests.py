import unittest

import yadtshell


class ActionPlanTests(unittest.TestCase):

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

        self.assertEqual(
            plan.meta_info(), '0 items, sequential, 0 errors tolerated')

    def test_should_dump_meta_info_for_parallel_plan(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_workers=3)

        self.assertEqual(
            plan.meta_info(), '0 items, 3 workers, 0 errors tolerated')

    def test_should_dump_meta_info_for_undefined_worker_count(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_workers=None)

        self.assertEqual(
            plan.meta_info(), '0 items, workers *undefined*, 0 errors tolerated')

    def test_should_dump_meta_info_for_several_actions(self):
        actions = [yadtshell.actions.Action(
            'start', 'service://foobar/service1'),
            yadtshell.actions.Action('start', 'service://foobaz/service2')]
        plan = yadtshell.actions.ActionPlan('plan', actions)

        self.assertEqual(
            plan.meta_info(), '2 items, workers *undefined*, 0 errors tolerated')

    def test_should_dump_meta_info_for_increased_error_tolerance(self):
        plan = yadtshell.actions.ActionPlan('plan', [], nr_errors_tolerated=4)

        self.assertEqual(
            plan.meta_info(), '0 items, workers *undefined*, 4 errors tolerated')
