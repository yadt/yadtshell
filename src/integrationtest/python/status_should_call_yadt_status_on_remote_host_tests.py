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
