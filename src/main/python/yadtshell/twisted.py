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

from __future__ import absolute_import

from twisted.internet import protocol, reactor, defer
import twisted.python.failure as failure

import sys
import logging

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

logger = logging.getLogger('twisted')


class SshFailure(failure.Failure):
    pass


class ProgressIndicator(object):
    PROGRESS_LABEL = 'progress: '

    def __init__(self, histo_threshold=40):
        self.observables = []
        self.progress = {}
        self.rendered = ['|', '/', '-', '\\']
        self.histo_threshold = histo_threshold
        self.finished = set()
        self.logger = logging.getLogger('progress')

    def update(self, observable, newvalue=None):
        observable = "justone"
        if isinstance(observable, list):
            observable = ' '.join(map(str, observable))
        if observable not in self.observables:
            self.observables.append(observable)
        if newvalue:
            self.finished.add(observable)
        else:
            value = self.progress.setdefault(observable, 0)
            if isinstance(value, int):
                self.progress[observable] = int(value) + 1
        self._update()

    def finish(self):
        if len(self.progress):
            self._overwrite_remaining_progress_with_blanks()

    def _overwrite_remaining_progress_with_blanks(self):
        remaining_progress_character_count = len(self.PROGRESS_LABEL) + 1
        print '\r' + remaining_progress_character_count * ' ' + '\r'

    def _render_value(self, value):
        if not value:
            return '?'
        if type(value) is int:
            return self.rendered[value % len(self.rendered)]
        return value

    def _render_compressed(self):
        rendered = [self._render_value(self.progress.get(o))
                    for o in self.observables]
        finished = [r for r in rendered if r not in self.rendered]
        unfinished = [r for r in rendered if r in self.rendered]
        finished_histo = dict((i, finished.count(i)) for i in set(finished))
        return ''.join(['%(count)i*%(key)s ' % locals() for key, count in finished_histo.iteritems()]) + ''.join([str(o) for o in unfinished])

    def _update(self):
        if sys.stderr.isatty():
            if len(self.observables) > self.histo_threshold:
                sys.stderr.write('\r' + self.PROGRESS_LABEL + self._render_compressed() + '\r')
            else:
                rendered = [self._render_value(self.progress.get(o)) for o in self.observables]
                sys.stderr.write('\r' + self.PROGRESS_LABEL + ''.join([str(o) for o in rendered]) + '\r')


class YadtProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, component, cmd, pi=None, out_log_level=logging.DEBUG,
                 err_log_level=logging.WARN, log_prefix='', wait_for_io=True):
        self.deferred = defer.Deferred()
        # self.deferred.name = component  # TODO(rwill): what's this needed for?
        try:
            self.component_name = component.encode('ascii')
        except AttributeError:
            self.component_name = component
        self.cmd = cmd.encode('ascii')
        self.wait_for_io = wait_for_io
        self.data = ""
        self.pi = pi
        if not log_prefix:
            log_prefix = '*YPP*'
        self.logger = logging.getLogger(log_prefix)
        self.out_log_level = out_log_level
        self.err_log_level = err_log_level

    def connectionMade(self):
        self.logger.debug("starting query: %s" % self.cmd)
        self.transport.write(self.cmd)
        self.transport.closeStdin()  # tell them we're done
        if self.pi:
            self.pi.update((self.cmd, self.component_name))

    def outReceived(self, data):
        for line in data.splitlines():
            self.logger.log(self.out_log_level,
                            '{0}: {1}'.format(self.component_name, line))
        self.data = self.data + data
        if self.pi:
            self.pi.update((self.cmd, self.component_name))

    def errReceived(self, data):
        for line in data.splitlines():
            self.logger.log(self.err_log_level,
                            '{0} {1} stderr: {2}'.format(self.component_name,
                                                         self.cmd,
                                                         line))
        if self.pi:
            self.pi.update((self.cmd, self.component_name))

    def processExited(self, reason):
        self.logger.debug("%s@%s exited, exit code %s" % (self.cmd,
                                                          self.component_name,
                                                          str(reason.value.exitCode)))
        if not self.wait_for_io:
            self.finish(reason)

    def processEnded(self, reason):
        self.logger.debug("%s@%s ended, exit code %s" % (self.cmd,
                                                         self.component_name,
                                                         str(reason.value.exitCode)))
        if self.wait_for_io:
            self.finish(reason)

    def finish(self, reason):
        self.exitcode = reason.value.exitCode
        if self.pi:
            self.pi.update((self.cmd, self.component_name), str(self.exitcode))
        if reason.value.exitCode == 0:
            self.deferred.callback(self)
        else:
            reason.value.component = self.component_name
            reason.value.orig_protocol = self
            self.deferred.errback(reason.value)


def stop_yadt(args=None):
    if reactor.running:
        reactor.stop()


def stop_and_return(return_code):
    if type(return_code) == int:
        reactor.return_code = return_code
    elif isinstance(return_code, failure.Failure):
        if hasattr(return_code.value, 'exitCode'):
            reactor.return_code = return_code.value.exitCode
        else:
            reactor.return_code = 1
    else:
        reactor.return_code = 0
    stop_yadt()


def _determine_issued_command(failure):
    try:
        return '%s@' % failure.value.orig_protocol.cmd
    except AttributeError:
        return ''


def report_error(failure, line_fun=None, include_stacktrace=True):
    if line_fun is None:
        def line_fun(line):
            logger.debug(line)
    if isinstance(failure, SshFailure):
        return failure
    if hasattr(failure.value, 'component'):
        line_fun('%s%s: %s' % (_determine_issued_command(failure),
                               failure.value.component,
                               failure.getErrorMessage()))
    else:
        line_fun(failure.getErrorMessage())
        if include_stacktrace:
            for line in failure.getBriefTraceback().splitlines():
                line_fun(line)
    return failure


def trace(arg, args='argh'):
    print 'trace: ' + args
    return arg
