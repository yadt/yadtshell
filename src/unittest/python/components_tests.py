import unittest
from mock import Mock, patch
import yadtshell
import yaml


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
            'yadt-service-ignore internet "yes we can ignore the service"', 'ignore_internet', False)

    def test_should_unignore_service(self):
        yadtshell.components.Service.unignore(self.mock_service)

        self.mock_service.remote_call.assert_called_with(
            'yadt-service-unignore internet', 'unignore_internet')

    def test_retrieve_service_call_should_build_command_with_action_and_name(self):
        service_call = yadtshell.components.Service._retrieve_service_call(
            self.mock_service, 'test')

        self.assertEqual(service_call, 'yadt-service-test internet')


class ArtefactTests(unittest.TestCase):

    def test_should_update_artefacts(self):
        mock_artefact = Mock(yadtshell.components.Artefact)
        mock_artefact.name = 'ham'
        mock_artefact.host = 'foobar42.domain'

        yadtshell.components.Artefact.updateartefact(mock_artefact)

        mock_artefact.remote_call.assert_called_with(
            'yadt-artefact-update ham', 'artefact_foobar42.domain_ham_updateartefact')


class UnreachableHostTests(unittest.TestCase):

    def setUp(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'foo'
        }

    def test_should_be_unreachable(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertFalse(unreachable_host.is_reachable())

    def test_should_be_unknown(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertTrue(unreachable_host.is_unknown)

    def test_should_not_have_updates(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.next_artefacts, {})

    def test_should_not_be_locked_by_me(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.is_locked_by_me, False)

    def test_should_not_be_locked_by_other(self):
        unreachable_host = yadtshell.components.UnreachableHost('foobar42')
        self.assertEquals(unreachable_host.is_locked_by_me, False)


class HostTests(unittest.TestCase):

    def test_should_be_reachable(self):
        yadtshell.settings.TARGET_SETTINGS = {
            'name': 'foo'
        }
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

    @patch('yadtshell.util.get_locking_user_info')
    def test_remote_call_should_create_wrapping_command_with_adequate_environment(self, mock_lockinfo):
        mock_lockinfo.return_value = {'owner': 'badass'}
        yadtshell.settings.SSH = 'super-ssh'
        mock_host = Mock(yadtshell.components.Host)
        mock_host.create_remote_log_filename.return_value = 'logfilename'
        mock_host.fqdn = 'foobar42.domain'
        mock_host.name = 'foobar42'

        command = yadtshell.components.Host.remote_call(mock_host, 'test')

        self.assertEqual(
            command, 'super-ssh foobar42.domain WHO="badass" YADT_LOG_FILE="logfilename" "yadt-command test" ')

    @patch('yadtshell.util.get_locking_user_info')
    def test_remote_call_should_use_host_when_component_has_no_fqdn(self, mock_lockinfo):
        mock_lockinfo.return_value = {'owner': 'badass'}
        yadtshell.settings.SSH = 'super-ssh'
        mock_host = Mock(yadtshell.components.Host)
        mock_host.create_remote_log_filename.return_value = 'logfilename'
        mock_host.host = 'foobar42'
        mock_host.name = 'foobar42'

        command = yadtshell.components.Host.remote_call(mock_host, 'test')

        self.assertEqual(
            command, 'super-ssh foobar42 WHO="badass" YADT_LOG_FILE="logfilename" "yadt-command test" ')

    def test_set_attrs_with_obsolete_services_format(self):
        data = {"hostname": "foo",
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
        data_text = """hostname: foo
services:
- backend-service:
    state: $backend_service_state
    service_artefact: yit-backend-service
    needs_services: ['service://foo/bar']
"""
        data = yaml.load(data_text, Loader=yaml.Loader)
        print data
        host = yadtshell.components.Host("myhost")
        host.set_attrs_from_data(data)
        self.assertEqual(len(host.services), 1)
        self.assertTrue("backend-service" in host.services)
        self.assertTrue(host.services["backend-service"]["service_artefact"], "yit-backend-service")
