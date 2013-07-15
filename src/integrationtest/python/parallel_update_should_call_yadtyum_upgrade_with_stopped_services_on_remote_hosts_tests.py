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

__author__ = 'Maximilien Riehl'

import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.write_target_file('it01.domain', 'it02.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('sudo /usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain', template=yadt_status_answer.STATUS_TEMPLATE_WITH_ARTIFACT_SERVICE_DEPENDENCIES))
            when.calling('ssh').at_least_with_arguments('it01.domain', '-O', 'check').then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-stop frontend-service')\
            .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service') \
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-stop backend-service') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status backend-service') \
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-host-update').then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-host-status')\
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-start backend-service') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-start frontend-service') \
                .then_return(0)

            when.calling('ssh').at_least_with_arguments('it02.domain').and_input('sudo /usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it02.domain', template=yadt_status_answer.STATUS_TEMPLATE_WITH_ARTIFACT_SERVICE_DEPENDENCIES))
            when.calling('ssh').at_least_with_arguments('it02.domain', '-O', 'check').then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-stop frontend-service') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status frontend-service') \
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-stop backend-service') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status backend-service') \
                .then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-host-update').then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-host-status') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-start backend-service') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-start frontend-service') \
                .then_return(0)


        actual_return_code = self.execute_command('yadtshell update -v -p 99')

        self.assertEquals(0, actual_return_code)

        with self.verify() as complete_verify:
            with complete_verify.filter_by_argument('it01.domain') as verify:
                verify.called('ssh').at_least_with_arguments('it01.domain').and_input('sudo /usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments('it01.domain', '-O', 'check')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-stop frontend-service').and_input('stop')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-stop backend-service').and_input('stop')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status backend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-host-update').and_input('update')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-host-status').and_input('probe')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-start backend-service').and_input('start')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status backend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-start frontend-service').and_input('start')
                verify.called('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service').and_input('status')

            with complete_verify.filter_by_argument('it02.domain') as verify:
                verify.called('ssh').at_least_with_arguments('it02.domain').and_input('sudo /usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments('it02.domain', '-O', 'check')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-stop frontend-service').and_input('stop')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status frontend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-stop backend-service').and_input('stop')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status backend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-host-update').and_input('update')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-host-status').and_input('probe')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-start backend-service').and_input('start')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status backend-service').and_input('status')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-start frontend-service').and_input('start')
                verify.called('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status frontend-service').and_input('status')

            complete_verify.finished()

if __name__ == '__main__':
    unittest.main()
