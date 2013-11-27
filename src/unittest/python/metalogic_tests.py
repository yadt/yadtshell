import unittest
from mock import patch

from yadtshell.metalogic import apply_instructions
from yadtshell.actions import ActionPlan, Action


class MetalogicTests(unittest.TestCase):

    def setUp(self):
        self.log_patcher = patch('yadtshell.metalogic.logging.getLogger')
        self.log_patcher.start()

    def tearDown(self):
        self.log_patcher.stop()

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

    def test_apply_instructions_should_default_to_zero_tolerated_errors(self):
        actions = [Action('sudo service bar stop', 'service://foo/bar'),
                   Action('sudo service baz stop', 'service://foo/baz')]
        original_plan = ActionPlan('update', actions)

        self.assertEqual(original_plan.nr_workers, None)

        actual_plan = apply_instructions(original_plan, None)

        self.assertEqual(actual_plan.nr_errors_tolerated, 0)

    def test_apply_instructions_should_split_plan_in_subplans(self):
        actions = [
            Action('sudo service bar stop', 'service://foo/bar'),
            Action('sudo service baz stop', 'service://foo/baz'),
            Action('sudo service baf start', 'service://foo/baf'),
            Action('sudo service bam start', 'service://foo/bam')
        ]
        original_plan = ActionPlan('test', actions)

        actual_plan = apply_instructions(original_plan, 'test=1_1_0:*_*_1')

        first_subplan = actual_plan.actions[0]
        second_subplan = actual_plan.actions[1]

        self.assertEqual(first_subplan.nr_workers, 1)
        self.assertEqual(first_subplan.nr_errors_tolerated, '0')
        self.assertEqual(len(first_subplan.actions), 1)
        self.assertEqual(first_subplan.actions, [actions[0]])

        self.assertEqual(second_subplan.nr_workers, 3)
        self.assertEqual(second_subplan.nr_errors_tolerated, '1')
        self.assertEqual(len(second_subplan.actions), 3)
        self.assertEqual(second_subplan.actions, actions[1:])
