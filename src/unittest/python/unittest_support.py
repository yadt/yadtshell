from unittest import TestCase
import yadtshell


def create_component_pool_for_one_host(host_state,
                                       add_services=False,
                                       service_state=yadtshell.settings.UP,
                                       host_reboot_after_update=False,
                                       host_reboot_now=False):
    components = yadtshell.components.ComponentDict()

    # create host components
    host = yadtshell.components.Host('foobar42')
    host.state = host_state
    host.reboot_required_after_next_update = host_reboot_after_update
    host.reboot_required_to_activate_latest_kernel = host_reboot_now
    host.hostname = 'foobar42'
    components['foobar42'] = host

    # create artefact components
    foo_artefact = yadtshell.components.Artefact(
        'foobar42', 'foo', '0:0.0.0')
    foo_artefact.state = yadtshell.settings.UP
    yit_artefact = yadtshell.components.Artefact(
        'foobar42', 'yit', '0:0.0.1')
    yit_artefact.state = yadtshell.settings.UP
    host.next_artefacts = {'foo/0:0.0.0': 'yit/0:0.0.1'}
    components['artefact://foobar42/foo/0:0.0.0'] = foo_artefact
    components['artefact://foobar42/yit/0:0.0.1'] = yit_artefact

    # create service components
    if add_services:
        host.services = ['barservice', 'bazservice']
        bar_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        bar_service.state = service_state
        baz_service = yadtshell.components.Service(
            'foobar42', 'barservice', {})
        baz_service.state = service_state
        components['service://foobar42/barservice'] = bar_service
        components['service://foobar42/bazservice'] = baz_service

    return components


class FileNameTestCase(TestCase):
    def _assert_element_at_is(self, actual_file_name, element_position, element_value):
        actual_element_value = actual_file_name.split('.')[element_position]
        message = 'Expected : {0} but got {1} instead'.format(element_value, actual_element_value)
        self.assertTrue(actual_element_value == element_value, message)

    def _assert(self, actual_file_name):
        self._actual_file_name = actual_file_name
        return self

    def _element_at(self, element_position):
        self.element_position = element_position
        return self

    def _is_equal_to(self, element_value):
        self._assert_element_at_is(self._actual_file_name, self.element_position, element_value)
