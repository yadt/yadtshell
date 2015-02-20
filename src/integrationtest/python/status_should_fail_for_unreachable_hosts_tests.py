#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2014  Immobilien Scout GmbH
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

    def test(self):
        self.write_target_file('it01.domain', 'it02.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_return(255)
            when.calling('ssh').at_least_with_arguments('it02.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it02.domain'))

        actual_return_code, stdout, stderr = self.execute_command_and_capture_output('yadtshell status')

        self.assertEqual(1, actual_return_code)
        self.assertTrue("cannot reach host it01.domain" in stderr.lower())


if __name__ == '__main__':
    unittest.main()
