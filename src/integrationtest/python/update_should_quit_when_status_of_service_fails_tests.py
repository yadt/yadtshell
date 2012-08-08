#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2012  Immobilien Scout GmbH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Michael Gruber, Udo Juettner'

import unittest
import integrationtest_support

import yadt_status_mock


class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.prepare_integration_test('should_quit_updating_when_status_of_service_fails')
        self.write_target_file('it01.domain')

        with self.fixture() as fixture:
            fixture.expect('ssh', ['it01.domain'], '/usr/bin/yadt-status') \
                   .then_write(yadt_status_mock.output('it01.domain'))
            fixture.expect('ssh', ['it01.domain', '-O', 'check']) \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start') \
                   .then_return(0)
            fixture.expect('ssh', ['it01.domain', 'sudo /sbin/service backend-service status'], 'status') \
                   .then_return(1)
            fixture.expect('ssh', ['it01.domain', '-O', 'exit']) \
                   .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v')

        self.assertEquals(1, actual_return_code)

        with self.verify() as verifier:
            verifier.verify('ssh', ['it01.domain'], '/usr/bin/yadt-status')
            verifier.verify('ssh', ['it01.domain', '-O', 'check'])
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service backend-service start'], 'start')
            verifier.verify('ssh', ['it01.domain', 'sudo /sbin/service backend-service status'], 'status')
            verifier.verify('ssh', ['it01.domain', '-O', 'exit'])


if __name__ == '__main__':
    unittest.main()
