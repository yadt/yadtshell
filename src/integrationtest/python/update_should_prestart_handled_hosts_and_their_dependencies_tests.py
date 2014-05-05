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

import string
import unittest
import integrationtest_support

import yadt_status_answer


template_it01_domain = string.Template("""
{
  "hostname":"$host",
  "fqdn":"$host_fqdn",
  "current_artefacts":[
    "yit/0:0.0.1",
    "yat/0:0.0.7"
  ],
  "next_artefacts":{
    "foo/0:0.0.0":"yit/0:0.0.1",
    "yat/0:0.0.8":"yat/0:0.0.7"
  },
  "services":[
    "foo_service":{
        "needs_services": ["service://it02/spam_service"],
    },
    "bar_service":{
    }
  ]
}
""")


template_it02_domain = string.Template("""
{
  "hostname":"$host",
  "fqdn":"$host_fqdn",
  "current_artefacts":[
    "yit/0:0.0.1",
    "yat/0:0.0.7"
  ],
  "next_artefacts":{
    "foo/0:0.0.0":"yit/0:0.0.1",
    "yat/0:0.0.8":"yat/0:0.0.7"
  },
  "services":[
    "spam_service":{
        "needs_services": ["service://it02/ham_service"],
    },
    "ham_service":{
    },
    "eggs_service":{
    }
  ]
}
""")


class TestWithDependencies(integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('it01.domain', 'it02.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input(
                '/usr/bin/yadt-status').then_write(yadt_status_answer.stdout('it01.domain', template=template_it01_domain))
            when.calling('ssh').at_least_with_arguments(
                'it01.domain').then_return(0)
            when.calling('ssh').at_least_with_arguments('it02.domain').and_input(
                '/usr/bin/yadt-status').then_write(yadt_status_answer.stdout('it02.domain', template=template_it02_domain))
            when.calling('ssh').at_least_with_arguments(
                'it02.domain').then_return(0)

        status_return_code = self.execute_command('yadtshell status')
        update_return_code = self.execute_command(
            'yadtshell update host://it01 --no-final-status')

        with self.verify() as verify:
            self.assertEqual(0, status_return_code)
            verify.called('ssh').with_input('/usr/bin/yadt-status')
            verify.called('ssh').with_input('/usr/bin/yadt-status')

            self.assertEqual(0, update_return_code)
            # status before update
            verify.called('ssh').with_input('/usr/bin/yadt-status')
            verify.called('ssh').with_input('/usr/bin/yadt-status')

            verify.called('ssh').at_least_with_arguments(
                '-O', 'check')
            verify.called('ssh').at_least_with_arguments(
                '-O', 'check')

            # prestart of it01.domain services w/o dependencies
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start bar_service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status bar_service')

            # prestart of it02.domain services that are needed
            verify.called('ssh').at_least_with_arguments(
                'it02.domain', 'yadt-command yadt-service-start ham_service')
            verify.called('ssh').at_least_with_arguments(
                'it02.domain', 'yadt-command yadt-service-status ham_service')
            verify.called('ssh').at_least_with_arguments(
                'it02.domain', 'yadt-command yadt-service-start spam_service')
            verify.called('ssh').at_least_with_arguments(
                'it02.domain', 'yadt-command yadt-service-status spam_service')

            # prestart of the it01.domain service that had the it02 dependency
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-start foo_service')
            verify.called('ssh').at_least_with_arguments(
                'it01.domain', 'yadt-command yadt-service-status foo_service')

            # the eggs_service has NOT been started

            # update
            verify.called('ssh').at_least_with_arguments(
                'yadt-command yadt-host-update yat-0:0.0.8 foo-0:0.0.0', 'it01.domain')


if __name__ == '__main__':
    unittest.main()
