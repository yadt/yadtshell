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

    def test(self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it01.domain') \
                .then_return(0)

        status_return_code = self.execute_command('yadtshell status -v')
        start_return_code = self.execute_command(
            'yadtshell start service://* -v')

        with self.verify() as verifier:
            self.assertEqual(0, status_return_code)
            verifier.called('ssh').at_least_with_arguments(
                'it01.domain').and_input('/usr/bin/yadt-status')

            self.assertEqual(0, start_return_code)
            verifier.called('ssh').at_least_with_arguments(
                u'-O', u'check', u'it01.domain')
            verifier.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start backend-service')
            verifier.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status backend-service')
            verifier.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start frontend-service')
            verifier.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status frontend-service')

            verifier.called('ssh').at_least_with_arguments(
                'it01.domain').and_input('/usr/bin/yadt-status')


if __name__ == '__main__':
    unittest.main()
