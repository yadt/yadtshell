#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2012  Immobilien Scout GmbH
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

from pythonbuilder.core import use_plugin, init, Author

use_plugin('python.core')
use_plugin('python.unittest')
use_plugin('python.integrationtest')
use_plugin('python.coverage')
use_plugin('python.pychecker')
use_plugin('python.pymetrics')
use_plugin('python.pylint')
use_plugin('python.distutils')
use_plugin('python.pydev')

use_plugin('copy_resources')
use_plugin('filter_resources')


authors = [Author('Arne Hilmann', 'arne.hilmann@gmail.com')]
description = """YADT - an Augmented Deployment Tool - The Shell Part
- regards the dependencies between services, over different hosts
- updates artefacts in a safe manner
- issues multiple commands in parallel on severall hosts

for more documentation, visit http://code.google.com/p/yadt/wiki/YadtCommands
"""
license = 'GNU GPL v3'
requires = 'PyYAML python-twisted python-hostexpand'
summary = 'YADT - an Augmented Deployment Tool - The Shell Part'
url = 'http://code.google.com/p/yadt'
version = '1.3.11'

default_task = ['analyze', 'publish']

@init
def set_properties (project):
    project.depends_on('hostexpand')
    project.depends_on('Twisted')
    project.depends_on('PyYAML')
    
    project.set_property('coverage_break_build', False)
    project.set_property('pychecker_break_build', False)
    project.set_property('integration_test_print_err', True)

    project.get_property('distutils_commands').append('bdist_rpm')    
    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').append('setup.cfg')
    project.get_property('filter_resources_glob').append('**/yadtshell/__init__.py')
    project.set_property('dir_dist_scripts', 'scripts')

    project.get_property('distutils_commands').append('bdist_egg')
    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration'
    ])
