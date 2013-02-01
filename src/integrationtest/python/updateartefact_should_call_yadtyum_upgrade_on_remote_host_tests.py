#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2013  Immobilien Scout GmbH
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

__author__ = 'Michael Gruber'

import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.write_target_file('it01.test.domain')

        with self.fixture() as when:
            when.calling('ssh').with_arguments('it01.test.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.test.domain'))
            when.calling('ssh').with_arguments('-O', 'check', 'it01.test.domain') \
                .then_return(0)
            when.calling('ssh').with_arguments('-s', 'yit-config-it01', 'sudo /usr/bin/yadt-yum upgrade -y yit-config-it01', 'it01.test.domain').and_input('updateartefact') \
                .then_return(0)
            when.calling('ssh').with_arguments('-O', 'exit', 'it01.test.domain') \
                .then_return(0)

        status_return_code = self.execute_command('yadtshell status -v')
        update_return_code = self.execute_command('yadtshell updateartefact artefact://it01/yit-config-it01 -v')

        with self.verify() as verify:
            self.assertEquals(0, status_return_code)
            verify.called('ssh').at_least_with_arguments('it01.test.domain').and_input('/usr/bin/yadt-status')

            self.assertEquals(0, update_return_code)
            verify.called('ssh').at_least_with_arguments('-O', 'check', 'it01.test.domain')
            verify.called('ssh').at_least_with_arguments('-s', 'yit-config-it01', 'sudo /usr/bin/yadt-yum upgrade -y yit-config-it01', 'it01.test.domain').and_input('updateartefact')
            verify.called('ssh').at_least_with_arguments('-O', 'exit', 'it01.test.domain')


if __name__ == '__main__':
    unittest.main()
