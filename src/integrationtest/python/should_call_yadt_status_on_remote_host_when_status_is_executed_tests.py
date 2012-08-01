import unittest
import integrationtest_support

import yadt_status_mock

class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.prepare_integration_test('status')
        self.write_target_file('it01.test.domain')

        with self.fixture() as fixture:
            fixture.expect('ssh', ['it01.test.domain'], '/usr/bin/yadt-status') \
                   .then_write(yadt_status_mock.output('it01.test.domain'))
        
        actual_return_code = self.execute_command('yadtshell status -v')
        
        self.assertEquals(0, actual_return_code)
        
        with self.verify() as verifier:
            verifier.verify('ssh', ['it01.test.domain'], '/usr/bin/yadt-status')


if __name__ == '__main__':
    unittest.main()
