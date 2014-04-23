from unittest import TestCase
from StringIO import StringIO
import yadtshell

# initialize this to a arbitrary value so it is defined.
# do not depend on this value in your test.
yadtshell.settings.TARGET_SETTINGS = {
    'name': 'initial name set in unittest_support.py',
}


def render_info_matrix_to_string(mocked_info_output):
    info_matrix = StringIO()
    for call in mocked_info_output.call_args_list:
        try:
            info_matrix.write(call[0][0])
        except IndexError:
            pass
        info_matrix.write('\n')
    info_matrix_string = info_matrix.getvalue()
    info_matrix.close()
    return info_matrix_string


def create_component_pool_for_one_host(host_state=yadtshell.settings.UPTODATE,
                                       add_readonly_services=False,
                                       add_services=False,
                                       service_state=yadtshell.settings.UP,
                                       host_reboot_after_update=False,
                                       host_reboot_now=False,
                                       artefact_state=yadtshell.settings.UP,
                                       host_locked_by_other=False,
                                       host_locked_by_me=False,
                                       next_artefacts_present=False):
    components = yadtshell.components.ComponentDict()

    # create host components
    host = yadtshell.components.Host('foobar42.acme.com')
    host.state = host_state
    host.reboot_required_after_next_update = host_reboot_after_update
    host.reboot_required_to_activate_latest_kernel = host_reboot_now
    host.hostname = 'foobar42'
    components['foobar42'] = host
    if host_locked_by_other:
        host.lockstate = {'owner': 'foobar',
                          'message': 'yes we can (lock the host)'}
        host.is_locked = True
        host.is_locked_by_other = True
    if host_locked_by_me:
        host.lockstate = {'owner': 'me',
                          'message': 'yes we can (lock the host)'}
        host.is_locked = True
        host.is_locked_by_me = True

    # create artefact components
    foo_artefact = yadtshell.components.Artefact(host, 'foo', '0:0.0.0')
    foo_artefact.state = artefact_state
    yit_artefact = yadtshell.components.Artefact(host, 'yit', '0:0.0.1')
    yit_artefact.state = artefact_state

    if not next_artefacts_present:
        host.next_artefacts = {'foo/0:0.0.0': 'yit/0:0.0.1'}
    components['artefact://foobar42/foo/0:0.0.0'] = foo_artefact
    components['artefact://foobar42/yit/0:0.0.1'] = yit_artefact

    if next_artefacts_present:
        host.next_artefacts = {'foo/0:0.1.0': 'yit/0:0.1.1'}

        foo2_artefact = yadtshell.components.Artefact(host, 'foo', '0:0.1.0')
        foo2_artefact.state = artefact_state
        foo2_artefact.revision = yadtshell.settings.NEXT
        yit2_artefact = yadtshell.components.Artefact(host, 'yit', '0:0.1.1')
        yit2_artefact.state = artefact_state
        yit2_artefact.revision = yadtshell.settings.NEXT
        components['artefact://foobar42/foo/0:0.1.0'] = foo2_artefact
        components['artefact://foobar42/yit/0:0.1.1'] = yit2_artefact

    # create service components
    if add_services:
        host.services = ['barservice', 'bazservice']
        bar_service = yadtshell.components.Service(host, 'barservice', {})
        bar_service.state = service_state
        bar_service.dependency_score = -1
        baz_service = yadtshell.components.Service(host, 'barservice', {})
        bar_service.needs_artefacts = ['artefact://foobar42/foo']
        baz_service.state = service_state
        baz_service.dependency_score = 1
        components['service://foobar42/barservice'] = bar_service
        components['service://foobar42/bazservice'] = baz_service

    if add_readonly_services:
        ro_up = yadtshell.components.ReadonlyService(host, 'ro_up')
        ro_up.state = yadtshell.settings.UP
        ro_up.needed_by = ['me', 'you']
        ro_down = yadtshell.components.ReadonlyService(host, 'ro_down')
        ro_down.state = yadtshell.settings.DOWN
        ro_down.needed_by = ['something', 'a_dog']

        components['service://foobar42/ro_up'] = ro_up
        components['service://foobar42/ro_down'] = ro_down

    return components


class FileNameTestCase(TestCase):

    def _assert_element_at_is(self,
                              actual_file_name,
                              element_position,
                              element_value):
        actual_element_value = actual_file_name.split('.')[element_position]
        message = 'Expected : {0} but got {1} instead'.format(
            element_value, actual_element_value)
        self.assertTrue(actual_element_value == element_value, message)

    def _assert(self, actual_file_name):
        self._actual_file_name = actual_file_name
        return self

    def _element_at(self, element_position):
        self.element_position = element_position
        return self

    def _is_equal_to(self, element_value):
        self._assert_element_at_is(
            self._actual_file_name, self.element_position, element_value)
