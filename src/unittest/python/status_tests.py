import yadtshell
# from twisted.trial
import unittest
from mock import Mock, patch, call


class StatusTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.ybc = Mock()
        yadtshell.settings.SSH = 'ssh'
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'test', 'hosts': ['foobar42']}
        self.pi_patcher = patch('yadtshell.twisted.ProgressIndicator')
        self.pi_patcher.start()

    def tearDown(self):
        self.pi_patcher.stop()

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_globbed_old_state_files_when_calling_status_without_hosts(self, os, glob):
        yadtshell.status()

        os.path.join.assert_called_with(
            yadtshell.settings.OUT_DIR, 'current_state*')
        os.remove.assert_called_with(os.path.join.return_value)

    @patch('yadtshell._status.glob')
    @patch('yadtshell._status.os')
    def test_should_remove_old_state_files_explicity_when_calling_status_with_hosts(self, os, glob):
        yadtshell.status(hosts=['foobar42'])

        os.path.join.assert_called_with(
            yadtshell.settings.OUT_DIR, 'current_state_foobar42.yaml')
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
        self.assertEqual(components['host://foobar42'], result)

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
    def todo_test_loading_service_class(self, _):
        host = yadtshell.components.Host("foo.acme.com")
        host.state = "uptodate"
        self.assertTrue(yadtshell.util.is_up(host.state), host.state)

        host.services = {"fooService": {"service": "MyService"},
                         "barService": {}
                         }
        components = {}
        host = yadtshell._status.initialize_services(host, components)

    def test_get_service_class_from_loaded_modules(self):
        result_class = yadtshell._status.get_service_class_from_loaded_modules("StatusTests")
        self.assertEqual(result_class.__name__, "StatusTests")

    def test_get_service_class_from_fallbacks(self):
        result_class = yadtshell._status.get_service_class_from_loaded_modules("StatusTests")
        self.assertEqual(result_class.__name__, "StatusTests")
