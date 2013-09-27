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
    "foo_service":{
        "needs_artefacts": ["yat"],
        "state": 0
    }
    ]
}'''

host_with_dependent_service_json = '''{
    "hostname": "host_with_dependent_service",
    "fqdn": "host_with_dependent_service",
    "current_artefacts": [
    "yit/0:0.0.1",
    "yat/0:0.0.7"
    ],
    "next_artefacts": {},
    "services": [
        "dependent_service":{
            "needs_services": ["service://host_with_updates/foo_service"],
            "state": 0
        }
    ]
}'''


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file(
            'host_with_updates', 'host_with_dependent_service')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('host_with_updates').and_input('/usr/bin/yadt-status') \
                .then_write(host_with_updates_json)
            when.calling('ssh').at_least_with_arguments('host_with_dependent_service').and_input('/usr/bin/yadt-status') \
                .then_write(host_with_dependent_service_json)

            when.calling('ssh').at_least_with_arguments('host_with_dependent_service', 'yadt-command yadt-service-status dependent_service')\
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('host_with_dependent_service') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('host_with_updates', 'yadt-command yadt-service-status foo_service')\
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('host_with_updates') \
                .then_return(0)

        update_return_code = self.execute_command('yadtshell update --no-final-status')

        self.assertEqual(0, update_return_code)

        with self.verify() as verify:
            #  yadt status before update
            verify.called('ssh').at_least_with_arguments('-o').and_input('/usr/bin/yadt-status')
            verify.called('ssh').at_least_with_arguments('-o').and_input('/usr/bin/yadt-status')

            #  ssh multiplexing
            verify.called('ssh').at_least_with_arguments(
                'host_with_dependent_service', '-O', 'check')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', '-O', 'check')

            #  stop services in correct order
            verify.called('ssh').at_least_with_arguments(
                'host_with_dependent_service', 'yadt-command yadt-service-stop dependent_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_dependent_service', 'yadt-command yadt-service-status dependent_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-stop foo_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-status foo_service')

            #  upgrade host
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-host-update yat-0:0.0.8 foo-0:0.0.0')

            #  start services in correct order
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-start foo_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_updates', 'yadt-command yadt-service-status foo_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_dependent_service', 'yadt-command yadt-service-start dependent_service')
            verify.called('ssh').at_least_with_arguments(
                'host_with_dependent_service', 'yadt-command yadt-service-status dependent_service')

if __name__ == '__main__':
    unittest.main()
