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

__author__ = 'Arne Hilmann, Marcel Wolf, Maximilien Riehl, Valentin Haenel'

import string
import unittest
import integrationtest_support

import yadt_status_answer

STATUS_JSON_TEMPLATE = string.Template("""
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
    "service":{
        "needs_services": ["service://foo/missing_service"],
        "needs_artefacts": ["missing_artefact"],
    }
  ]
}
""")


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('it01.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain', template=STATUS_JSON_TEMPLATE))
            when.calling('ssh').at_least_with_arguments('foo',
                                                        'yadt-command yadt-service-status missing_service').then_return(3)

        actual_return_code = self.execute_command('yadtshell status -v')

        self.assertEqual(0, actual_return_code)

        with self.verify() as verify:
            # fetch full initial status
            verify.called('ssh').at_least_with_arguments(
                'it01.domain').and_input('/usr/bin/yadt-status')
            # fetch missing read-only information
            verify.called('ssh').at_least_with_arguments('foo',
                                                         'yadt-command yadt-service-status missing_service')


if __name__ == '__main__':
    unittest.main()
