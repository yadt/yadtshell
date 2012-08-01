import unittest
import integrationtest_support

import yadt_status_mock

class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.prepare_integration_test('update')
        self.write_target_file('it01.domain')

        with self.fixture() as fixture:
            fixture.expect('ssh', ['it01.domain'], '/usr/bin/yadt-status') \
                   .then_write(yadt_status_mock.output('it01.domain'))
            fixture.expect('ssh', ['it01.domain', '-O', 'check'], None) \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service backend-service status'], 'status') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service frontend-service start'], 'start') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service frontend-service status'], 'status') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /usr/bin/yadt-yum upgrade'], 'update') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', '/usr/bin/yadt-status-host'], 'probe') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', '-O', 'exit'], None) \
                   .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v')

        self.assertEquals(0, actual_return_code)

        with self.verify() as verifier:
            verifier.verify('ssh', ['it01.domain'], '/usr/bin/yadt-status')
            verifier.verify('ssh', ['it01.domain', '-O', 'check'], None)
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start')
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service backend-service status'], 'status')
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service frontend-service start'], 'start')
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service frontend-service status'], 'status')
            verifier.verify('ssh', ['it01.domain', 'sudo /usr/bin/yadt-yum upgrade'], 'update')
            verifier.verify('ssh', ['it01.domain', '/usr/bin/yadt-status-host'], 'probe')
            verifier.verify('ssh', ['it01.domain', '-O', 'exit'], None)

if __name__ == '__main__':
    unittest.main()
