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
        self.write_target_file('it01.domain', 'it02.domain', 'it03.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it01.domain') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('it02.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it02.domain'))
            when.calling('ssh').at_least_with_arguments('it02.domain') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('it03.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it03.domain'))
            when.calling('ssh').at_least_with_arguments('it03.domain') \
                .then_return(0)

        actual_return_code = self.execute_command('yadtshell update -v -p 99')

        self.assertEqual(0, actual_return_code)

        with self.verify() as complete_verify:
            with complete_verify.filter_by_argument('it01.domain') as filtered_verify:
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain').and_input('/usr/bin/yadt-status')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', '-O', 'check')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-start backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-status backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-start frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-status frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-host-update yit-config-it01-0:0.0.1-2')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it01.domain').and_input('/usr/bin/yadt-status')

            with complete_verify.filter_by_argument('it02.domain') as filtered_verify:
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain').and_input('/usr/bin/yadt-status')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', '-O', 'check')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-start backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-status backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-start frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-status frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-host-update yit-config-it02-0:0.0.1-2')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it02.domain').and_input('/usr/bin/yadt-status')

            with complete_verify.filter_by_argument('it03.domain') as filtered_verify:
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain').and_input('/usr/bin/yadt-status')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', '-O', 'check')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', 'yadt-command yadt-service-start backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', 'yadt-command yadt-service-status backend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', 'yadt-command yadt-service-start frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', 'yadt-command yadt-service-status frontend-service')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain', 'yadt-command yadt-host-update yit-config-it03-0:0.0.1-2')
                filtered_verify.called('ssh').at_least_with_arguments(
                    'it03.domain').and_input('/usr/bin/yadt-status')

            complete_verify.finished()


if __name__ == '__main__':
    unittest.main()
