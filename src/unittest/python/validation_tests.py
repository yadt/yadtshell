from unittest import TestCase

import yadtshell
from yadtshell.validation import tarjan_scc, ServiceDefinitionValidator
from yadtshell.components import Service


class ServiceValidationTests(TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foo', 'bar']}
        self.servicedefs = {
            'service://foo_host/foo': Service('foo_host', 'foo', {}),
            'service://bar_host/bar': Service('bar_host', 'bar', {}),
        }

    def test_should_not_do_anything_when_there_are_no_service_cycles(self):
        ServiceDefinitionValidator(self.servicedefs).assert_no_cycles_present()

    def test_should_find_simple_service_cycle(self):
        self.servicedefs['service://foo_host/foo'].needs = [
            'service://bar_host/bar']
        self.servicedefs['service://bar_host/bar'].needs = [
            'service://foo_host/foo']

        self.assertRaises(EnvironmentError,
                          ServiceDefinitionValidator(
                              self.servicedefs).assert_no_cycles_present
                          )


class TarjanSCCTests(TestCase):

    def test_should_find_simple_scc(self):
        graph_with_cycle = {'foo': ['bar'],
                            'bar': ['foo']}

        strongly_connected_components = tarjan_scc(graph_with_cycle)

        self.assertEqual(strongly_connected_components, [('bar', 'foo')])

    def test_should_not_find_any_scc_when_graph_empty(self):
        empty_graph = {}

        strongly_connected_components = tarjan_scc(empty_graph)
        self.assertEqual(strongly_connected_components, [])

    def test_should_only_find_single_item_components_when_there_are_no_cycles(self):
        graph_with_no_cycles = {'foo': ['bar'],
                                'a': ['b'],
                                'baz': ['bar'],
                                'hello': ['foo']}

        strongly_connected_components = tarjan_scc(graph_with_no_cycles)
        self.assertEqual(strongly_connected_components, [
                         ('b',), ('a',), ('bar',), ('foo',), ('baz',), ('hello',)])

    def test_should_find_multi_item_components_when_there_are_cycles(self):
        graph_with_cycle = {'foo': ['bar'],
                            'bar': ['baz'],
                            'baz': ['abc'],
                            'abc': ['foo'],
                            'f': ['g'],
                            'j': ['k']}

        strongly_connected_components = tarjan_scc(graph_with_cycle)
        self.assertEqual(strongly_connected_components, [
                         ('baz', 'bar', 'foo', 'abc'), ('g',), ('f',), ('k',), ('j',)])
