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

import unittest
import integrationtest_support

import yadt_status_answer

import threading

parallel = False


class Chunk (threading.Thread):

    def __init__(self, chunkId, fun, *args, **kwargs):
        threading.Thread.__init__(self)
        self.chunkId = chunkId
        self.fun = fun
        self.args = args
        self.kwargs = kwargs
        self.exitcode = None

    def run(self):
        print "starting %s: %s '%s'" % (self.chunkId, self.fun.__name__, " ".join(self.args))
        self.exitcode = self.fun(*self.args, **self.kwargs)
        print "exiting %s, exitcode %s" % (self.chunkId, self.exitcode)


class Test (integrationtest_support.IntegrationTestSupport):

    def test(self):
        self.write_target_file('it01.domain it02.domain')

        with self.fixture() as when:
            when.calling('ssh').at_least_with_arguments('it01.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it01.domain'))
            when.calling('ssh').at_least_with_arguments('it02.domain').and_input('/usr/bin/yadt-status') \
                .then_write(yadt_status_answer.stdout('it02.domain'))

            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-stop frontend-service') \
                .then_return(0, milliseconds_to_wait=0)
            when.calling('ssh').at_least_with_arguments('it01.domain', 'yadt-command yadt-service-status frontend-service')\
                .then_return(1)

            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-stop frontend-service') \
                .then_return(0, milliseconds_to_wait=0)
            when.calling('ssh').at_least_with_arguments('it02.domain', 'yadt-command yadt-service-status frontend-service')\
                .then_return(1)

        status_return_code = self.execute_command('yadtshell status -v')

        if (parallel):
            chunks = [
                Chunk("chunk1", self.execute_command,
                      'yadtshell stop service://it01/frontend-service -v'),
                Chunk("chunk2", self.execute_command,
                      'yadtshell stop service://it02/frontend-service -v')
            ]
            [chunk.start() for chunk in chunks]
            [chunk.join(20) for chunk in chunks]
            for chunk in chunks:
                if chunk.isAlive():
                    print "%s timed out!" % chunk.chunkId
                else:
                    print "%s returned %s" % (chunk.chunkId, chunk.exitcode)
            stop1_return_code = chunks[0].exitcode
            stop2_return_code = chunks[1].exitcode
        else:
            stop1_return_code = self.execute_command(
                'yadtshell stop service://it01/frontend-service -v')
            stop2_return_code = self.execute_command(
                'yadtshell stop service://it02/frontend-service -v')

        with self.verify() as complete_verify:
            self.assertEquals(0, status_return_code)
            self.assertEquals(0, stop1_return_code)
            self.assertEquals(0, stop2_return_code)

            with complete_verify.filter_by_argument('it01.domain') as verify:
                verify.called('ssh').at_least_with_arguments(
                    'it01.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-stop frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it01.domain', 'yadt-command yadt-service-status frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it01.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'it01.domain').and_input('/usr/bin/yadt-status')

            with complete_verify.filter_by_argument('it02.domain') as verify:
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain').and_input('/usr/bin/yadt-status')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-stop frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain', 'yadt-command yadt-service-status frontend-service')
                verify.called('ssh').at_least_with_arguments(
                    'it02.domain').and_input('/usr/bin/yadt-status')

            complete_verify.finished()


if __name__ == '__main__':
    unittest.main()
