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

__author__ = 'Arne Hilmann, Marcel Wolf'

import re
import unittest
import integrationtest_support

import yadt_status_answer


class Test (integrationtest_support.IntegrationTestSupport):
    def test (self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain', template=yadt_status_answer.STATUS_JSON_TEMPLATE))

        actual_return_code = self.execute_command('yadtshell status')
        self.assertEquals(0, actual_return_code)

        self.assertEquals(0, self.execute_command('yadtshell info | grep " u " | grep "host uptodate"'))
        return_code, stdout, _ = self.execute_command_and_capture_output('yadtshell info')
        update_found_for_foo = False
        for line in stdout.splitlines():
            if re.search('\(next\) foo', line):
                update_found_for_foo = True
                break
        self.assertTrue(update_found_for_foo, 'yit not obsoleted by foo, info was:{0}'.format(stdout))

        self.assertEquals(0, self.execute_command('yadtshell dump --show-pending-updates | grep foo'))

        with self.verify() as complete_verify:
            with complete_verify.filter_by_argument('it01.domain') as verify:
                verify.called('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status')

            complete_verify.finished()

if __name__ == '__main__':
    unittest.main()
