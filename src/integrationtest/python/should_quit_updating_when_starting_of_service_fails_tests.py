import unittest
import integrationtest_support

import yadt_status_mock

class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.prepare_integration_test('should_quit_updating_when_starting_of_service_fails')
        self.write_target_file('it01.domain')

        with self.fixture() as fixture:
            fixture.expect('ssh', ['it01.domain'], '/usr/bin/yadt-status') \
                   .then_write(yadt_status_mock.output('it01.domain'))
            fixture.expect('ssh', ['it01.domain', '-O', 'check'], None) \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start') \
                   .then_return(1)
            fixture.expect('ssh', ['it01.domain', 'exit'], None) \
                   .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v')

        self.assertEquals(1, actual_return_code)

        with self.verify() as verifier:
            verifier.verify('ssh', ['it01.domain'], '/usr/bin/yadt-status')
            verifier.verify('ssh', ['it01.domain', '-O', 'check'], None)
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start')
            verifier.verify('ssh', ['it01.domain', '-O', 'exit'], None)

if __name__ == '__main__':
    unittest.main()
