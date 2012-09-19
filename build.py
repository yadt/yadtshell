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
use_plugin('python.integrationtest')
use_plugin('python.install_dependencies')

use_plugin('python.distutils')
use_plugin('python.pydev')

use_plugin('copy_resources')
use_plugin('filter_resources')


authors     = [Author('Arne Hilmann', 'arne.hilmann@gmail.com')]
description = '''YADT - an Augmented Deployment Tool - The Shell Part
- regards the dependencies between services, over different hosts
- updates artefacts in a safe manner
- issues multiple commands in parallel on severall hosts

for more documentation, visit http://code.google.com/p/yadt/wiki/YadtCommands
'''

name    = 'yadtshell'
license = 'GNU GPL v3'
summary = 'YADT - an Augmented Deployment Tool - The Shell Part'
url     = 'https://github.com/yadt/yadtshell'
version = '1.3.12'
 
default_task = ['publish']

@init
def set_properties (project):
    project.depends_on('hostexpand', url='https://github.com/downloads/yadt/hostexpand/hostexpand-1.0.1.tar.gz')
    project.depends_on('Twisted')
    project.depends_on('PyYAML')

    project.build_depends_on('shtub', url='https://github.com/downloads/yadt/shtub/shtub-0.2.9.tar.gz')

    project.set_property('integration_test_print_err', True)

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
    
@init(environments='teamcity')
def set_properties_for_teamcity_builds (project):
    import os
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['install_build_dependencies', 'publish']

