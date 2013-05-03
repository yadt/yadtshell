import unittest
from yadtshell.metalogic import apply_instructions
from yadtshell.actions import ActionPlan, Action

class MetalogicTests(unittest.TestCase):

    def test_apply_instructions_should_augment_plan_with_multiple_workers(self):
        actions = [Action('sudo service bar stop', 'service://foo/bar'),
                   Action('sudo service baz stop', 'service://foo/baz')]
        original_plan = ActionPlan('update', actions)

        self.assertEqual(original_plan.nr_workers, None)

        actual_plan = apply_instructions(original_plan, 99)

        self.assertEqual(actual_plan.nr_workers, 99)

    def test_apply_instructions_should_augment_plan_with_no_instructions_to_use_one_worker(self):
        actions = [Action('sudo service bar stop', 'service://foo/bar'),
                   Action('sudo service baz stop', 'service://foo/baz')]
        original_plan = ActionPlan('update', actions)

        self.assertEqual(original_plan.nr_workers, None)

        actual_plan = apply_instructions(original_plan, None)

        self.assertEqual(actual_plan.nr_workers, 1)

    def test_apply_instructions_should_augment_plan_with_workers_and_tolerated_errors(self):
        actions = [Action('sudo service bar stop', 'service://foo/bar'),
                   Action('sudo service baz stop', 'service://foo/baz')]
        original_plan = ActionPlan('update', actions)

        self.assertEqual(original_plan.nr_workers, None)

        actual_plan = apply_instructions(original_plan, 'update=1_1_3')

        self.assertEqual(actual_plan.actions[0].nr_workers, 1)
        self.assertEqual(actual_plan.actions[0].nr_errors_tolerated, '3')


