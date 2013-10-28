import unittest

import yadtshell
from yadtshell.util import (inbound_deps,
                            outbound_deps,
                            compute_dependency_scores)


class ServiceOrderingTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.components = yadtshell.components.ComponentDict()
        self.bar_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        self.baz_service = yadtshell.components.Service(
            'foobar42', 'bazservice', {})
        self.ack_service = yadtshell.components.Service(
            'foobar42', 'ackservice', {})

        self.components['service://foobar42/barservice'] = self.bar_service
        self.components['service://foobar42/bazservice'] = self.baz_service
        self.components['service://foobar42/ackservice'] = self.ack_service

    def test_inbound_deps_should_return_empty_list_when_service_is_not_needed(self):

        self.assertEqual(inbound_deps(self.bar_service, self.components), [])

    def test_inbound_deps_should_return_needing_service(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']

        self.assertEqual(
            inbound_deps(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_outbound_deps_should_return_empty_list_when_service_needs_nothing(self):
        self.assertEqual(outbound_deps(self.bar_service, self.components), [])

    def test_outbound_deps_should_return_needed_service(self):
        self.bar_service.needs = ['service://foobar42/bazservice']

        self.assertEqual(
            outbound_deps(self.bar_service, self.components), ['service://foobar42/bazservice'])

    def test_should_compute_inbound_deps_recursively(self):
        self.ack_service.needed_by = ['service://foobar42/bazservice']
        self.baz_service.needed_by = ['service://foobar42/barservice']

        self.assertEqual(inbound_deps(self.ack_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/barservice'])

    def test_should_compute_outbound_deps_recursively(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        self.baz_service.needs = ['service://foobar42/ackservice']

        self.assertEqual(outbound_deps(self.bar_service, self.components), [
                         'service://foobar42/bazservice', 'service://foobar42/ackservice'])

    def test_should_return_0_when_there_are_no_edges(self):
        compute_dependency_scores(self.components)
        self.assertEqual(self.baz_service.dependency_score, 0)
        self.assertEqual(self.bar_service.dependency_score, 0)
        self.assertEqual(self.ack_service.dependency_score, 0)

    def test_should_increase_dependency_score_when_ingoing_edge_found(self):
        self.bar_service.needed_by = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, 1)

    def test_should_decrease_dependency_score_when_outdoing_edge_found(self):
        self.bar_service.needs = ['service://foobar42/bazservice']
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)

    def test_should_enable_and_decrease_dependency_score_based_on_edges(self):
        self.bar_service.needs = ['service://foobar42/bazservice']      # -1
        self.baz_service.needs = ['service://foobar42/ackservice']      # -1
        self.bar_service.needed_by = ['service://foobar42/ackservice']  # +1
        compute_dependency_scores(self.components)

        self.assertEqual(self.bar_service.dependency_score, -1)
