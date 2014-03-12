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

from pybuilder.core import use_plugin, init, Author, task
from pybuilder.utils import assert_can_execute

use_plugin('python.core')
use_plugin('python.integrationtest')
use_plugin('python.install_dependencies')
use_plugin('python.unittest')
use_plugin('python.coverage')
use_plugin('python.flake8')

use_plugin('python.distutils')
use_plugin('copy_resources')
use_plugin('filter_resources')

authors = [Author('Arne Hilmann', 'arne.hilmann@gmail.com'),
           Author('Marcel Wolf', 'marcel.wolf@immobilienscout24.de'),
           Author('Maximilien Riehl', 'max@riehl.io')]

description = """YADT - an Augmented Deployment Tool - The Shell Part
- regards the dependencies between services, over different hosts
- updates artefacts in a safe manner
- issues multiple commands in parallel on several hosts

for more documentation, visit http://www.yadt-project.org/
"""

name = 'yadtshell'
license = 'GNU GPL v3'
summary = 'YADT - an Augmented Deployment Tool - The Shell Part'
url = 'https://github.com/yadt/yadtshell'
version = '1.8.2'

default_task = ['clean', 'analyze', 'publish'] 


@init
def set_properties(project):
    project.depends_on('hostexpand')
    project.depends_on('Twisted')
    project.depends_on('PyYAML')
    project.depends_on('simplejson')
    project.depends_on('docopt')

    project.build_depends_on('shtub')
    project.build_depends_on('mock')

    project.set_property('integrationtest_parallel', True)
    project.set_property('integrationtest_cpu_scaling_factor', 8)
    project.set_property('integrationtest_inherit_environment', True)

    project.set_property('flake8_verbose_output', True)
    project.set_property('flake8_include_test_sources', True)
    project.set_property('flake8_ignore', 'E501')
    project.set_property('flake8_break_build', True)

    project.set_property('verbose', True)

    project.set_property('coverage_threshold_warn', 50)
    project.set_property('coverage_break_build', False)

    project.rpm_release = '0'
    project.install_file('share/man/man1/', 'docs/man/yadtshell.1.man.gz')

    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').extend(['setup.cfg', 'docs/man/yadtshell.1.man.gz'])

    project.get_property('filter_resources_glob').extend(['**/yadtshell/__init__.py', '**/setup.cfg'])

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
def set_properties_for_teamcity_builds(project):
    import os
    project.version = '%s-%s' % (project.version, os.environ.get('BUILD_NUMBER', 0))
    project.default_task = ['clean', 'install_build_dependencies', 'publish']
    project.set_property('install_dependencies_index_url', os.environ.get('PYPIPROXY_URL'))
    project.set_property('install_dependencies_use_mirrors', False)
    project.rpm_release = os.environ.get('RPM_RELEASE', 0)


@task
def clean(project, logger):
    import glob
    import os
    import shutil

    for yadtshell_log_dir in glob.glob('/tmp/logs/yadtshell/*'):
        logger.info('Removing log directory {0}'.format(yadtshell_log_dir))
        shutil.rmtree(yadtshell_log_dir)

    for integrationtest_dir in glob.glob('/tmp/integration-test*'):
        logger.info('Removing IT directory {0}'.format(integrationtest_dir))
        shutil.rmtree(integrationtest_dir)

    stubs_dir = '/tmp/yadtshell-it'
    if os.path.exists(stubs_dir):
        logger.info('Removing stubs directory {0}'.format(stubs_dir))
        shutil.rmtree(stubs_dir)


@task
def generate_manpage_with_pandoc(project, logger):
    assert_can_execute(['pandoc', '-v'], 'pandoc', 'generate_manpage_with_pandoc')
    import subprocess
    subprocess.check_output('pandoc -s -t man man-yadtshell.md -o docs/man/yadtshell.1.man', shell=True)
    subprocess.check_output('rm -f docs/man/yadtshell.1.man.gz && gzip -9 docs/man/yadtshell.1.man', shell=True)
