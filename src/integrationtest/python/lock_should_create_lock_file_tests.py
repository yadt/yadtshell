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

__author__ = 'Michael Gruber, Maximilien Riehl'

import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it01.domain', '-O', 'check') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', '-s', 'None').and_input('lock') \
                .then_return(0)
            when.calling('ssh').at_least_with_arguments('it01.domain', '-O', 'exit') \
                .then_return(0)

        status_return_code = self.execute_command('yadtshell status -v')
        lock_return_code   = self.execute_command('yadtshell lock host://it01 -m "locking \'the host\'" -v')

        with self.verify() as verify:
            self.assertEquals(0, status_return_code)
            verify.called('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status')

            self.assertEquals(0, lock_return_code)
            verify.called('ssh').at_least_with_arguments('it01.domain', '-O', 'check')
            verify.called('ssh').at_least_with_arguments('it01.domain').and_input('lock') \
                .and_at_least_one_argument_matches("""umask 0002 && mkdir -pv /var/lock/yadt && echo -e 'force: false
message: locking the host
owner: .*@.*:/.*
pid: \d*
user: .*
when: [A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} [A-Z]{3}
working_copy: /.*
yadt_host: .*
' > /var/lock/yadt/host.lock""")
            verify.called('ssh').at_least_with_arguments('it01.domain', '-O', 'exit')


if __name__ == '__main__':
    unittest.main()
