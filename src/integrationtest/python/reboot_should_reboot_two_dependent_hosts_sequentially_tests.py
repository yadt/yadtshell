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

host_1 = """{
  "hostname":"host1",
  "fqdn":"host1.domain",
  "current_artefacts":[
    "yit/0:0.0.1",
    "yat/0:0.0.7"
  ],
  "next_artefacts":{
    "foo/0:0.0.0":"yit/0:0.0.1",
    "yat/0:0.0.8":"yat/0:0.0.7"
  },
  "services":[
    "host1service":{
        "needs_services": ["service://host2/host2service"],
    }
  ]
}"""

host_2 = """{
  "hostname":"host2",
  "fqdn":"host2.domain",
  "current_artefacts":[
    "yit/0:0.0.1",
    "yat/0:0.0.7"
  ],
  "next_artefacts":{
    "foo/0:0.0.0":"yit/0:0.0.1",
    "yat/0:0.0.8":"yat/0:0.0.7"
  },
  "services":[
    "host2service":{
    }
  ]
}"""


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('host1.domain', 'host2.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('host1.domain').and_input('/usr/bin/yadt-status') \
                .then_write(host_1)
            when.calling('ssh').at_least_with_arguments('host1.domain', 'yadt-command yadt-service-status host1service').then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('host1.domain', 'yadt-command yadt-host-update -r').then_return(255)
            when.calling('ssh').at_least_with_arguments('host1.domain').then_return(0)

            when.calling('ssh').at_least_with_arguments('host2.domain').and_input('/usr/bin/yadt-status') \
                .then_write(host_2)
            when.calling('ssh').at_least_with_arguments('host2.domain', 'yadt-command yadt-service-status host2service').then_return(3).then_return(0)
            when.calling('ssh').at_least_with_arguments('host2.domain', 'yadt-command yadt-host-update -r').then_return(255)
            when.calling('ssh').at_least_with_arguments('host2.domain').then_return(0)

        reboot_return_code = self.execute_command('yadtshell reboot host://* -v')

        self.assertEqual(0, reboot_return_code)

        with self.verify() as outer_verify:
            with outer_verify.filter_by_argument("host1.domain") as verify:
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', '-O', 'check')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', 'yadt-command yadt-service-stop host1service')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', 'yadt-command yadt-service-status host1service')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', 'yadt-command yadt-host-update -r ')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', 'yadt-command yadt-service-start host1service')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain', 'yadt-command yadt-service-status host1service')
                verify.called('ssh').at_least_with_arguments(
                    'host1.domain').and_input('/usr/bin/yadt-status')

            with outer_verify.filter_by_argument("host2.domain") as verify:
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', '-O', 'check')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', 'yadt-command yadt-service-stop host2service')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', 'yadt-command yadt-service-status host2service')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', 'yadt-command yadt-host-update -r ')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', 'yadt-command yadt-service-start host2service')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain', 'yadt-command yadt-service-status host2service')
                verify.called('ssh').at_least_with_arguments(
                    'host2.domain').and_input('/usr/bin/yadt-status')

            outer_verify.finished()

if __name__ == '__main__':
    unittest.main()
