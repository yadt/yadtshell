import yadtshell
# from twisted.trial
import unittest
from mock import Mock, patch, call
from twisted.internet import defer


class MyCustomService(yadtshell.components.Service):
    pass


# TODO(rwill): break up tests into different classes so we can have different setUp() for each group.
class StatusTests(unittest.TestCase):
    # TODO(rwill): make sure no actual files are read or written. (Always mock `os` module...??)

    def setUp(self):
        # Apparently we don't need to mock or patch reactor.spawnProcess
        # because it doesn't do anything as long as no actual reactor is running!
        yadtshell.settings.ybc = Mock()
        yadtshell.settings.SSH = 'ssh'
        yadtshell.settings.TARGET_SETTINGS = {'name': 'test',
                                              'hosts': ['foobar42']
                                              }
        self.pi_patcher = patch('yadtshell.twisted.ProgressIndicator')
        self.pi_patcher.start()

    def tearDown(self):
        self.pi_patcher.stop()

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_globbed_old_state_files_when_calling_status_without_hosts(self, os, glob):
        yadtshell.status()

        os.path.join.assert_called_with(yadtshell.settings.OUT_DIR, 'current_state*')
        os.remove.assert_called_with(os.path.join.return_value)

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_old_state_files_explicity_when_calling_status_with_hosts(self, os, glob):
        yadtshell.status(hosts=['foobar42'])

        os.path.join.assert_called_with(yadtshell.settings.OUT_DIR, 'current_state_foobar42.yaml')
        os.remove.assert_called_with(os.path.join.return_value)

    @patch('yadtshell.twisted.ProgressIndicator')
    @patch('yadtshell._status.query_status')
    @patch('yadtshell._status.os')
    def test_should_setup_deferred_list_with_two_hosts(self, _, query_status, pi):
        yadtshell.status(hosts=['foobar42', 'foobar43'])

        self.assertEqual(query_status.call_args_list, [
            call('foobar42', pi.return_value),
            call('foobar43', pi.return_value)])

    @patch('yadtshell._status.os.environ')
    @patch('yadtshell._status.reactor.spawnProcess')
    @patch('yadtshell.twisted.YadtProcessProtocol')
    def test_query_status_should_spawn_status_process(self, protocol, spawn_process, environment):
        yadtshell._status.query_status(component_name='host://foobar42')
        protocol.assert_called_with(
            'host://foobar42', '/usr/bin/yadt-status', None)
        spawn_process.assert_called_with(
            protocol.return_value, 'ssh', ['ssh', 'host://foobar42'], environment)

    @patch('yadtshell._status.logger')
    def test_handle_unreachable_host(self, _):
        failure = Mock()
        failure.value.component = 'foobar42.domain.tld'
        failure.value.exitCode = 255
        components = {}
        result = yadtshell._status.handle_unreachable_host(failure, components)
        self.assertTrue(isinstance(result, yadtshell.components.UnreachableHost))
        self.assertEqual(result.fqdn, 'foobar42.domain.tld')
        # self.assertIn('host://foobar42', components)  # use this when we have Python >= 2.7
        self.assertTrue('host://foobar42' in components)
        self.assertEqual(components['host://foobar42'], result, "components.keys() = %s" % components.keys())

    def test_should_create_host_from_json(self):
        components = {}
        protocol_with_json_data = Mock()
        protocol_with_json_data.component = 'host://foobar42'
        protocol_with_json_data.data = '''{
"fqdn": "foobar42.acme.com",
"next_artefacts": {},
"some_attribute": "some-value"
}'''

        result_host = yadtshell._status.create_host(protocol_with_json_data, components)

        self.assertEqual(result_host.hostname, 'foobar42')
        self.assertEqual(result_host.next_artefacts, {})
        self.assertEqual(result_host.is_uptodate(), True)
        self.assertEqual(result_host.some_attribute, "some-value")
        self.assertEqual(result_host.loc_type, {
                         'loc': 'foo', 'host': 'foobar42', 'type': 'bar', 'loctype': 'foobar', 'nr': '42'})

    def test_should_create_host_with_update_needed_when_next_artefacts_is_not_empty(self):
        components = {}
        protocol_with_json_data = Mock()
        protocol_with_json_data.component = 'host://foobar42'
        protocol_with_json_data.data = '''{
"fqdn": "foobar42.acme.com",
"next_artefacts": {"some-artefact": "another-artefact"},
"some_attribute": "some-value"
}'''

        result_host = yadtshell._status.create_host(protocol_with_json_data, components)

        self.assertEqual(result_host.is_update_needed(), True)

    def test_should_create_host_from_yaml(self):
        components = {}
        protocol_with_yaml_data = Mock()
        protocol_with_yaml_data.component = 'host://foobar42'
        protocol_with_yaml_data.data = '''
fqdn: foobar42.acme.com
next_artefacts: []
some_attribute: some-value
'''
        result_host = yadtshell._status.create_host(protocol_with_yaml_data, components)

        self.assertEqual(result_host.hostname, 'foobar42')
        self.assertEqual(result_host.next_artefacts, [])
        self.assertEqual(result_host.is_uptodate(), True)
        self.assertEqual(result_host.some_attribute, "some-value")
        self.assertEqual(result_host.loc_type, {
                         'loc': 'foo', 'host': 'foobar42', 'type': 'bar', 'loctype': 'foobar', 'nr': '42'})

    @patch('yadtshell._status.logger')
    def test_initialize_services(self, _):
        host = yadtshell.components.Host("foo.acme.com")
        host.state = "uptodate"
        self.assertTrue(yadtshell.util.is_up(host.state), host.state)

        host.services = {"fooService": {},
                         "barService": {}
                         }
        components = {}
        host = yadtshell._status.initialize_services(host, components)
        self.assertEqual(len(host.defined_services), 2)
        self.assertTrue(host.defined_services[0].name in host.services.keys())
        self.assertTrue(host.defined_services[1].name in host.services.keys())
        self.assertEqual(len(components), 2)

    @patch('yadtshell._status.logger')
    def test_initialize_service_with_custom_service_class(self, _):
        host = yadtshell.components.Host("foo.acme.com")
        host.state = "uptodate"
        self.assertTrue(yadtshell.util.is_up(host.state), host.state)

        host.services = {"fooService": {"service": "MyCustomService"},
                         "barService": {}
                         }
        components = {}
        host = yadtshell._status.initialize_services(host, components)
        service_class = components["service://foo/fooService"].__class__
        self.assertEqual(service_class.__name__, "MyCustomService")

    def test_get_service_class_from_loaded_modules(self):
        result_class = yadtshell._status.get_service_class_from_loaded_modules("MyCustomService")
        self.assertEqual(result_class.__name__, "MyCustomService")

    def test_get_service_class_from_fallback_1(self):
        myhost = yadtshell.components.Host("foo.bar.com")
        result_class = yadtshell._status.get_service_class_from_fallbacks(myhost, "yadtshell.components.Component")
        self.assertEqual(result_class.__name__, "Component")

    def test_get_service_class_from_fallback_2(self):
        myhost = yadtshell.components.Host("foo.bar.com")
        result_class = yadtshell._status.get_service_class_from_fallbacks(myhost, "module_for_class_loading.Example")
        self.assertEqual(result_class.__name__, "Example")

    def test_initialize_artefacts(self):
        host = yadtshell.components.Host("foo.bar.com")
        host.current_artefacts = ["arte/0", "fact/2"]
        host.next_artefacts = ["arte/1"]
        components = {}
        yadtshell._status.initialize_artefacts(host, components)
        expected_uris = ['artefact://foo/arte/0', 'artefact://foo/arte/current',
                         'artefact://foo/arte/1', 'artefact://foo/arte/next',
                         'artefact://foo/fact/2', 'artefact://foo/fact/current']
        # self.assertItemsEqual(components.keys(), expected_uris)  # use this in Python >= 2.7
        self.assertEqual(set(components.keys()), set(expected_uris))

    @patch('yadtshell._status.query_status')
    def todo_test_syntax_status(self, query_status):
        # TODO(rwill): this currently crashes because of build_*_dependency_tree.component_files
        # extract file I/O from status() method into submethods, so those can be mocked.
        protocol = Mock()
        protocol.component = "host://myhost"
        protocol.data = '''
fqdn: foobar42.acme.com
current_artefacts:
- foo/1.0
- bar/2.3
next_artefacts:
- foo/1.1
services:
  tomcat:
    needs_services: [database]
    state: down
  database:
    state: up
'''
        query_status.return_value = defer.succeed(protocol)
        yadtshell.status("myhost")
