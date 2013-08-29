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

__author__ = 'Michael Gruber, Udo Juettner'

import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it01.domain') \
                .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v')

        self.assertEqual(0, actual_return_code)

        with self.verify() as verify:
            verify.called('ssh').at_least_with_arguments(
                'it01.domain').and_input('/usr/bin/yadt-status')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', '-O', 'check')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.001\.it01\.backend-service_start\.log')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.002\.it01\.backend-service_status\.log')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.003\.it01\.frontend-service_start\.log')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.004\.it01\.frontend-service_status\.log')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.005\.it01\.it01_update\.log')
            verify.called('ssh').at_least_with_arguments('-l').at_least_one_argument_matches(
                '\d{4}-\d{2}-\d{2}/yadtshell.integration-test.\d{4}-\d{2}-\d{2}--\d{2}-\d{2}-\d{2}.*\.006\.it01\.log')

if __name__ == '__main__':
    unittest.main()
