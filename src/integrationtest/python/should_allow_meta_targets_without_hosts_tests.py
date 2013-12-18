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

__author__ = 'Marcel Wolf, Maximilien Riehl'

import os
import unittest

from os.path import join

import integrationtest_support
import yadt_status_answer


root_target_contents = """
hosts:
includes:
 - sub
"""
sub_target_contents = """
hosts:
 - foo.bar02
"""


class Test(integrationtest_support.IntegrationTestSupport):

    def do_preliminary_cleanup(self):
        self.subtarget_folder = join(os.path.dirname(self.base_dir), 'sub')
        import shutil
        if os.path.isdir(self.subtarget_folder):
            shutil.rmtree(self.subtarget_folder)

    def test(self):
        self.do_preliminary_cleanup()
        with open(join(self.base_dir, 'target'), 'w') as target_file:
            target_file.write(root_target_contents)
        os.makedirs(self.subtarget_folder)
        with open(join(self.subtarget_folder, 'target'), 'w') as subtarget_file:
            subtarget_file.write(sub_target_contents)
        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('foo.bar02').and_input(
                '/usr/bin/yadt-status').then_write(yadt_status_answer.stdout('foo.bar02'))

        return_code = self.execute_command('yadtshell status -v')

        self.assertEqual(0, return_code)
        with self.verify() as verify:

            verify.called('ssh').at_least_with_arguments(
                'foo.bar02').and_input('/usr/bin/yadt-status')


if __name__ == '__main__':
    unittest.main()
