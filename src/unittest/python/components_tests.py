import re
import unittest
import yaml

from mock import Mock, patch, ANY

import yadtshell


class ServiceTests(unittest.TestCase):

    def setUp(self):
        mock_service = Mock(yadtshell.components.Service)
        mock_service._retrieve_service_call = lambda action: action
        mock_service.name = 'internet'
        self.mock_service = mock_service

    def test_should_stop_service(self):
        yadtshell.components.Service.stop(self.mock_service)

        self.mock_service.remote_call.assert_called_with(
            'stop', 'internet_stop', False)

    def test_should_probe_service(self):
        yadtshell.components.Service.status(self.mock_service)

        self.mock_service.remote_call.assert_called_with(
            'status', tag='internet_status')

    def test_should_start_service(self):
        yadtshell.components.Service.start(self.mock_service)

        self.mock_service.remote_call.assert_called_with(
            'start', 'internet_start', False)

    def test_should_ignore_service(self):
        yadtshell.components.Service.ignore(
            self.mock_service, 'yes we can ignore the service')

        self.mock_service.remote_call.assert_called_with(
            'yadt-service-ignore internet \'yes we can ignore the service\'', 'ignore_internet', False)

    def test_should_unignore_service(self):
        yadtshell.components.Service.unignore(self.mock_service)

        self.mock_service.remote_call.assert_called_with(
            'yadt-service-unignore internet', 'unignore_internet')

    def test_retrieve_service_call_should_build_command_with_action_and_name(self):
        service_call = yadtshell.components.Service._retrieve_service_call(
            self.mock_service, 'test')

        self.assertEqual(service_call, 'yadt-service-test internet')


class ReadonlyServiceTests(unittest.TestCase):

    def test_should_default_to_unknown_state(self):
        host = yadtshell.components.Host('example.com')
        readonly_service = yadtshell.components.ReadonlyService(host, 'NAME')
        self.assertEquals(yadtshell.settings.UNKNOWN, readonly_service.state)

    @patch('yadtshell.components.reactor')
    def test_status_calls_spawn_process_with_service_status(self, reactor_mock):
        host = yadtshell.components.Host('example.com')
        readonly_service = yadtshell.components.ReadonlyService(host, 'NAME')
        readonly_service.status()
        expected_command = ['ssh', 'example.com',
                            ANY, ANY, 'yadt-command yadt-service-status NAME']
        reactor_mock.spawnProcess.assert_called_once_with(
            ANY, 'ssh', expected_command, None)

    @patch('yadtshell.components.reactor')
    @patch('yadtshell.components.YadtProcessProtocol')
    def test_status_returns_yadt_process_protocol_deferred(self,
                                                           yadt_process_protocol_mock, _):
        host = yadtshell.components.Host('example.com')
        readonly_service = yadtshell.components.ReadonlyService(host, 'service_name')
        yadt_process_protocol_mock.return_value = Mock(cmd='command argument')
        status_deferred = readonly_service.status()
        MOCK_POSITIONAL_ARGS, SECOND_ARG = 0, 1
        command_string = yadt_process_protocol_mock.call_args[MOCK_POSITIONAL_ARGS][SECOND_ARG]
        yadt_process_protocol_mock.assert_called_once_with(readonly_service, ANY, out_log_level=ANY)
        self.assertTrue(
            re.match('^ssh example.com WHO=".*"'
                     ' YADT_LOG_FILE=".*" '
                     '"yadt-command yadt-service-status service_name" $',
                     command_string
                     ) is not None)
        self.assertTrue(status_deferred is yadt_process_protocol_mock.return_value.deferred)


class ArtefactTests(unittest.TestCase):

    def test_should_update_artefacts(self):
        mock_artefact = Mock(yadtshell.components.Artefact)
        mock_artefact.name = 'ham'
        mock_artefact.host = 'foobar42.domain'

        yadtshell.components.Artefact.updateartefact(mock_artefact)

        mock_artefact.remote_call.assert_called_with(
            'yadt-artefact-update ham', 'artefact_foobar42.domain_ham_updateartefact')


class UnreachableHostTests(unittest.TestCase):

    def test_should_be_unreachable(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertFalse(unreachable_host.is_reachable())

    def test_should_be_unknown(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertTrue(unreachable_host.is_unknown)

    def test_should_not_have_updates(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.next_artefacts, [])

    def test_should_not_be_locked_by_me(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.is_locked_by_me, False)

    def test_should_not_be_locked_by_other(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.is_locked_by_me, False)

    def test_uri(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42.rz.is')
        self.assertEquals(unreachable_host.uri, 'host://foobar42')


class HostTests(unittest.TestCase):

    def test_should_be_reachable(self):
        reachable_host = yadtshell.components.Host('foobar42')
        self.assertTrue(reachable_host.is_reachable())

    def test_should_update_next_artefacts_only(self):
        mock_host = Mock(yadtshell.components.Host)
        mock_host.next_artefacts = ['foo/1-2.3', 'bar/1-1.3/2']
        mock_host.hostname = 'foobar42.domain'
        mock_host.remote_call.return_value = 'remote call'
        mock_host.reboot_required = False

        yadtshell.components.Host.update(mock_host)

        mock_host.remote_call.assert_called_with(
            'yadt-host-update foo-1-2.3 bar-1-1.3/2', 'foobar42.domain_update')

    def test_should_update_with_reboot_switch_when_reboot_required(self):
        mock_host = Mock(yadtshell.components.Host)
        mock_host.next_artefacts = ['foo/1-2.3', 'bar/1-1.3/2']
        mock_host.hostname = 'foobar42.domain'
        mock_host.remote_call.return_value = 'remote call'
        mock_host.reboot_required = True
        mock_host.ssh_poll_max_seconds = 42
        mock_host.kwargs = {'reboot_required': True}

        yadtshell.components.Host.update(mock_host, reboot_required=True)

        mock_host.remote_call.assert_called_with(
            'yadt-host-update -r foo-1-2.3 bar-1-1.3/2', 'foobar42.domain_update')

    def test_should_force_lock_host(self):
        mock_host = Mock(yadtshell.components.Host)
        mock_host.hostname = 'foobar42.domain'

        yadtshell.components.Host.lock(
            mock_host, message='lock me!', force=True)

        mock_host.remote_call.assert_called_with(
            "yadt-host-lock 'lock me!'", 'lock_host', True)

    def test_should_lock_host(self):
        mock_host = Mock(yadtshell.components.Host)
        mock_host.hostname = 'foobar42.domain'

        yadtshell.components.Host.lock(
            mock_host, message='lock me!', force=False)

        mock_host.remote_call.assert_called_with(
            "yadt-host-lock 'lock me!'", 'lock_host', False)

    @patch('yadtshell.components.get_user_info')
    def test_remote_call_should_create_wrapping_command_with_adequate_environment(self, mock_lockinfo):
        mock_lockinfo.return_value = {'owner': 'badass'}
        mock_host = Mock(yadtshell.components.Host)
        mock_host.create_remote_log_filename.return_value = 'logfilename'
        mock_host.fqdn = 'foobar42.domain'
        mock_host.name = 'foobar42'

        command = yadtshell.components.Host.remote_call(mock_host, 'test')

        self.assertEqual(
            command, 'ssh foobar42.domain WHO="badass" YADT_LOG_FILE="logfilename" "yadt-command test" ')

    @patch('yadtshell.components.get_user_info')
    def test_remote_call_should_use_host_when_component_has_no_fqdn(self, mock_lockinfo):
        mock_lockinfo.return_value = {'owner': 'badass'}
        mock_host = Mock(yadtshell.components.Host)
        mock_host.create_remote_log_filename.return_value = 'logfilename'
        mock_host.host = 'foobar42'
        mock_host.name = 'foobar42'

        command = yadtshell.components.Host.remote_call(mock_host, 'test')

        self.assertEqual(
            command, 'ssh foobar42 WHO="badass" YADT_LOG_FILE="logfilename" "yadt-command test" ')

    def test_set_attrs_with_obsolete_services_format(self):
        data = {"fqdn": "foo-boing",
                "services": [
                    {"service_foo": Mock()},
                    {"service_bar": Mock()}
                ]}
        host = yadtshell.components.Host("myhost")
        host.set_attrs_from_data(data)
        self.assertEqual(len(host.services), 2)
        self.assertTrue("service_foo" in host.services)
        self.assertTrue("service_bar" in host.services)

    def test_set_attrs_with_obsolete_yaml_services_format(self):
        data_text = """fqdn: foo.baz
services:
- backend-service:
    state: $backend_service_state
    service_artefact: yit-backend-service
    needs_services: ['service://foo/bar']
"""
        data = yaml.load(data_text, Loader=yaml.Loader)
        host = yadtshell.components.Host("myhost")
        host.set_attrs_from_data(data)
        self.assertEqual(len(host.services), 1)
        self.assertTrue("backend-service" in host.services)
        self.assertTrue(host.services["backend-service"]["service_artefact"], "yit-backend-service")
