import unittest
import integrationtest_support

host_with_updates_json = '''{
    "hostname": "host_with_updates",
    "fqdn": "host_with_updates",
    "current_artefacts": [
    "yit/0:0.0.1",
    "yat/0:0.0.7"
    ],
    "next_artefacts": {
    "foo/0:0.0.0": "yit/0:0.0.1",
    "yat/0:0.0.8": "yat/0:0.0.7"
    },
    "services": [
    "service1":{
        "state": 0
    }
    ]
}'''

host_with_reboot_required_json = '''{
    "hostname": "host_with_reboot_required",
    "fqdn": "host_with_reboot_required",
    "reboot_required_to_activate_latest_kernel": True,
    "current_artefacts": [
    "yit/0:0.0.1",
    "yat/0:0.0.7"
    ],
    "next_artefacts": {},
    "services": [
        "service2":{
            "state": 0
        }
    ]
}'''


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file(
            'host_with_updates', 'host_with_reboot_required')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('host_with_updates').and_input('/usr/bin/yadt-status') \
                .then_write(host_with_updates_json)
            when.calling('ssh').at_least_with_arguments('host_with_reboot_required').and_input('/usr/bin/yadt-status') \
                .then_write(host_with_reboot_required_json)

            when.calling('ssh').at_least_with_arguments('host_with_reboot_required', 'yadt-command yadt-service-status service2')\
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('host_with_reboot_required') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('host_with_updates') \
                .then_return(0)

        update_return_code = self.execute_command(
            'yadtshell update --no-final-status --reboot')

        self.assertEqual(0, update_return_code)

        with self.verify() as verify:
            #  yadt status before update
            verify.called('ssh').at_least_with_arguments(
                '-o').and_input('/usr/bin/yadt-status')
            verify.called('ssh').at_least_with_arguments(
                '-o').and_input('/usr/bin/yadt-status')

            #  ssh multiplexing
            verify.called('ssh').at_least_with_arguments(
                '-O', 'check')
            verify.called('ssh').at_least_with_arguments(
                '-O', 'check')

            #  prestart
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-start service1')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-status service1')

            #  stop services in correct order
            verify.called('ssh').at_least_with_arguments(
                'host_with_reboot_required', 'yadt-command yadt-service-stop service2')
            verify.called('ssh').at_least_with_arguments(
                'host_with_reboot_required', 'yadt-command yadt-service-status service2')

            #  upgrade host
            verify.called('ssh').at_least_with_arguments(
                'host_with_reboot_required', 'yadt-command yadt-host-update -r ')
            verify.called('ssh').at_least_with_arguments(
                #  start services in correct order
                'host_with_reboot_required', 'yadt-command yadt-service-start service2')
            verify.called('ssh').at_least_with_arguments(
                'host_with_reboot_required', 'yadt-command yadt-service-status service2')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-host-update yat-0:0.0.8 foo-0:0.0.0')


if __name__ == '__main__':
    unittest.main()
