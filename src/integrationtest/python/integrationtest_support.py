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

__author__ = 'Alexander Metzner, Michael Gruber, Udo Juettner'

import sys
import inspect

from os import environ, pathsep, symlink, sep
from os.path import abspath, exists, join

from shutil import rmtree

from shtub import testbase

TARGET_FILE_PREFIX = """name: integration-test
log-dir: logs
hosts:
"""

class IntegrationTestSupport (testbase.IntegrationTestBase):
    def setUp (self):
        super(IntegrationTestSupport, self).setUp()
        caller_stack_record = inspect.stack()[-1]
        caller_path = caller_stack_record[1]
        caller_filename = caller_path.split('/')[-1]
        cleaned_filename = caller_filename[:-9]
        self._create_target_directory(cleaned_filename)
        self.prepare_testbed(self._create_env(), ['ssh'])
        self._make_yadtshell_testable()


    def write_target_file (self, *hostnames):
        target_filename = join(self.base_dir, 'target')
        with open(target_filename, 'w') as target_file:
            target_file.write(TARGET_FILE_PREFIX)
            for host in hostnames:
                target_file.write('- %s\n' % host)


    def _make_yadtshell_testable (self):
        absolute_path_to_script = abspath(join('src', 'main', 'scripts', 'yadtshell'))
        destination = join(self.stubs_dir, 'yadtshell')

        symlink(absolute_path_to_script, destination)


    def _create_target_directory(self, name):
        target_dir = abspath(__file__).split(sep)[:-4]
        target_dir.append('target')
        target_dir.append('integrationtests')
        target_dir.append(name)

        base_dir = sep.join(target_dir)

        if exists(base_dir):
            rmtree(base_dir)

        self.make_base_dir(base_dir)


    def _create_path(self):
        path = self.stubs_dir
        if 'PATH' in environ:
            path += pathsep + environ['PATH']
        else:
            path += pathsep + '/bin'
            path += pathsep + '/usr/bin'
            path += pathsep + '/usr/local/bin'
        return path


    def _create_python_path(self):
        python_path = pathsep.join(sys.path)

        if environ.has_key('PYTHONPATH'):
            python_path += pathsep + environ['PYTHONPATH']

        python_path += pathsep + abspath(join('..', 'hostexpand', 'src', 'main', 'python'))
        python_path += pathsep + abspath(join('src', 'main', 'python'))
        return python_path


    def _create_env(self):
        return {'HOME'       : self.base_dir,
                'PATH'       : self._create_path(),
                'PYTHONPATH' : self._create_python_path()}
