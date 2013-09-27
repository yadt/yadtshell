from yadtshell.defer import DeferredPool

import unittest
from mock import patch, call, Mock


class DeferredPoolTests(unittest.TestCase):

    @patch('yadtshell.defer.reactor')
    def test_should_callback_immediately_when_queue_is_empty(self, fake_reactor):
        pool = DeferredPool('pool-name', queue=[])

        fake_reactor.callLater.assert_called_with(0, pool.callback)

    @patch('yadtshell.defer.DeferredPool.Worker')
    def test_should_instantiate_one_worker_when_one_was_supplied(self, fake_worker):
        pool = DeferredPool('pool-name', queue=['something-to-do'], nr_workers=1)

        fake_worker.assert_called_with('pool-name_worker0', pool._next_task, pool._handle_error)
        self.assertEqual(pool.workers, [fake_worker.return_value])

    @patch('yadtshell.defer.DeferredPool.Worker')
    def test_should_instantiate_n_workers_when_n_were_supplied(self, fake_worker):
        pool = DeferredPool('pool-name', queue=['something-to-do'], nr_workers=8)
        worker_id = 0

        actual_worker_calls = [wc for wc in fake_worker.call_args_list]

        for wc in actual_worker_calls:
            self.assertEqual(wc, call('pool-name_worker%d' % worker_id, pool._next_task, pool._handle_error))
            worker_id += 1

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    def test_should_start_all_workers(self, started_workers):
        DeferredPool('pool-name', queue=['something-to-do'], nr_workers=4)

        started_worker_calls = [wc for wc in started_workers.call_args_list]

        self.assertEqual(started_worker_calls, [call(), call(), call(), call()])

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.reactor')
    def test_should_callback_when_queue_is_empty_and_no_errors_occurred(self, fake_reactor, _):
        pool = DeferredPool('pool-name', queue=[])

        pool._finish()

        fake_reactor.callLater.assert_called_with(0, pool.callback)

    @patch('yadtshell.defer.logging')
    @patch('yadtshell.actions.ActionException')
    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.reactor')
    def test_should_errback_when_actions_could_not_be_executed(self, fake_reactor, _, action_exception, __):
        task = lambda: None
        task.action = lambda: None
        task.action.dump = lambda: 'do something'
        pool = DeferredPool('pool-name', queue=[task])

        pool._finish()

        fake_reactor.callLater.assert_called_with(0, pool.errback, action_exception.return_value)
        action_exception.assert_called_with('Could not execute 1 action(s)', 1)

    @patch('yadtshell.defer.logging')
    @patch('yadtshell.actions.ActionException')
    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.reactor')
    def test_should_errback_when_error_count_is_too_high(self, fake_reactor, _, action_exception, __):
        pool = DeferredPool('pool-name', queue=['some-task'], nr_errors_tolerated=4)
        pool.error_count = 5

        pool._finish()

        fake_reactor.callLater.assert_called_with(0, pool.errback, action_exception.return_value)
        action_exception.assert_called_with('stops: error count too high, 5 > 4', 1)

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.reactor')
    def test_should_callback_when_queue_is_empty_and_less_errors_than_allowed_occurred(self, fake_reactor, _):
        pool = DeferredPool('pool-name', queue=[], nr_errors_tolerated=6)
        pool.error_count = 5

        pool._finish()

        fake_reactor.callLater.assert_called_with(0, pool.callback)

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.reactor')
    def test_should_callback_when_queue_is_empty_and_errors_occurred_equals_errors_allowed(self, fake_reactor, _):
        pool = DeferredPool('pool-name', queue=[], nr_errors_tolerated=5)
        pool.error_count = 5

        pool._finish()

        fake_reactor.callLater.assert_called_with(0, pool.callback)

    def test_next_task_should_return_nothing_when_pool_has_already_callbacked(self):
        pool = DeferredPool('pool-name', queue=[])
        pool.callback(Mock())

        next_task = pool._next_task()

        self.assertEqual(next_task, None)

    def test_next_task_should_return_nothing_when_queue_is_empty_but_workers_are_still_running(self):
        pool = DeferredPool('pool-name', queue=[])
        pool.all_workers_idle = lambda: False

        next_task = pool._next_task()

        self.assertEqual(next_task, None)

    @patch('yadtshell.defer.DeferredPool._stop_workers')
    def test_next_task_should_return_nothing_and_stop_workers_when_queue_is_empty_and_workers_are_idle(self, stop_workers):
        pool = DeferredPool('pool-name', queue=[])
        pool.all_workers_idle = lambda: True

        next_task = pool._next_task()

        self.assertEqual(next_task, None)
        stop_workers.assert_called_with()

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    @patch('yadtshell.defer.DeferredPool._stop_workers')
    def test_next_task_should_stop_workers_when_queue_is_not_empty_but_no_tasks_are_available_and_workers_are_idle(self, stop_workers, _):
        pool = DeferredPool('pool-name', queue=['some-stuff'])
        pool.all_workers_idle = lambda: True
        pool.next_task_fun = lambda _: None

        next_task = pool._next_task()

        self.assertEqual(next_task, None)
        stop_workers.assert_called_with()

    @patch('yadtshell.defer.DeferredPool.Worker.run')
    def test_next_task_should_return_task_when_tasks_are_available(self, _):
        pool = DeferredPool('pool-name', queue=['some-stuff'])
        pool.all_workers_idle = lambda: False

        next_task = pool._next_task()

        self.assertEqual(next_task, 'some-stuff')
