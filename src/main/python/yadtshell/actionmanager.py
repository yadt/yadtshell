# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
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
from __future__ import print_function

import yaml
import pickle
import logging
import os.path
import re
import shlex
import copy
import sys

import twisted.internet.reactor as reactor
import twisted.internet.defer as defer
import twisted.python.failure as failure
from twisted.internet.task import deferLater

import yadtshell
from yadtshell.commandline import (confirm_transaction_by_user,
                                   EXIT_CODE_CANCELED_BY_USER)


class ActionManager(object):

    class Task(object):

        def __init__(self, fun, action, path=None):
            self.fun = fun
            self.action = action
            self.path = path

    def __init__(self):
        self.logger = logging.getLogger('actionmanager')
        self.finish_fun = self.log_host_finished
        self.logger.info('log file: "{0}"'.format(yadtshell.settings.log_file))

    def get_state_info(self, action):
        component = self.components[action.uri]
        if action.attr:
            component_state = getattr(component, action.attr, '')
            return [action.cmd, action.uri, action.attr, component_state,
                    getattr(action, 'target_value', None)]
        else:
            return [action.cmd, action.uri, None, None, None]

    def probe(self, component, delay=0, target_state=None):
        def store_host_exit_code(result):
            if isinstance(result, failure.Failure):
                result = result.value.exitCode
            else:
                result = 0
            component.state = yadtshell.constants.HOST_STATE_DESCRIPTIONS.get(
                result, result)
            self.logger.info(
                yadtshell.util.render_component_state(component.uri, component.state))
            self.pi.update(('status', component), '%s' % result)
            return
        if isinstance(component, yadtshell.components.Host):
            deferred = self.issue_command(component, 'probe')
            deferred.addBoth(store_host_exit_code)
            return deferred

        def store_service_exit_code(result):
            if result and not isinstance(result, int):
                if isinstance(result, failure.Failure):
                    result = result.value.exitCode
                else:
                    result = 0
            component.state = yadtshell.settings.STATE_DESCRIPTIONS.get(
                result, component.state)
            self.logger.info(
                yadtshell.util.render_component_state(component.uri, component.state))
            self.pi.update(('status', component), '%s' % result)
            yadtshell.settings.ybc.sendServiceChange(
                [{'uri': component.uri, 'state': component.state}], tracking_id=yadtshell.settings.tracking_id)
            self.logger.debug("storing new state for %s: %s" %
                              (component.uri, component.state))
            self.orig_components[component.uri].state = component.state
            return
        if isinstance(component, yadtshell.components.Service):
            status_cmd = 'status'
            if hasattr(component, 'immediate_status'):
                status_cmd = 'immediate_status'
            deferred = deferLater(
                reactor, delay, self.issue_command, component, status_cmd)
            deferred.addErrback(
                self.handle_ignored_or_locked, status_cmd, component, target_state)
            deferred.addBoth(store_service_exit_code)
            return deferred
        self.logger.critical('do not know how to probe %s: unknown type %s' %
                             (component.uri, type(component)))

    def set_probed_state(self, protocol, component):
        setattr(component, 'recheck', yadtshell.constants.PROBED)
        return protocol

    def mark_action_as_finished(self, ignored, action):
        action.state = yadtshell.actions.State.FINISHED
        return ignored

    def handle_action(self, protocol=None, plan=None, path=None):
        action = plan
        self.logger.debug('executing action %s' % action)
        cmd, uri, _, _, target_state = self.get_state_info(action)
        action.state = yadtshell.actions.State.RUNNING
        component = self.components[uri]
        deferred = None

        action_to_execute = '/' + '/'.join(path)
        if self.dryrun:
            self.logger.info(action_to_execute)
        else:
            self.logger.debug(action_to_execute)
        if cmd == yadtshell.settings.FINISH:
            if self.finish_fun:
                self.finish_fun(action)
            return defer.succeed(None)

        if self.dryrun:
            if action.attr:
                self.logger.debug(
                    '        dryrun %(cmd)s, setting %(attr)s to %(target_value)s on %(uri)s' % vars(action))
                setattr(component, action.attr, action.target_value)
            else:
                self.logger.debug(
                    '        dryrun %(cmd)s on %(uri)s' % vars(action))
            # return defer.succeed(None)
            deferred = defer.Deferred()
            reactor.callLater(0, deferred.callback, None)
            return deferred

            # deferred dryrun
            # reactor.callLater(.5, setattr, component, action.attr, action.target_value)
            # deferred = defer.Deferred()
            # reactor.callLater(1, deferred.callback, None)
            # return deferred

        if cmd == yadtshell.constants.PROBE:
            deferred = self.probe(component)
            deferred.addCallback(self.set_probed_state, component)
        out_log_level = logging.DEBUG

        if cmd in [yadtshell.settings.UPDATE, yadtshell.constants.UPDATEARTEFACT]:
            out_log_level = logging.INFO

        if out_log_level == logging.INFO:
            self.logger.info(
                '-' * 20 + ' verbatim stdout of %s follows this line ' % cmd + '-' * 20)

        if not deferred:
            deferred = self.issue_command(component,
                                          cmd,
                                          target_state,
                                          out_log_level=out_log_level,
                                          args=getattr(action, 'args', []),
                                          kwargs=getattr(action, 'kwargs', {}))
        if out_log_level == logging.INFO:
            deferred.addBoth(self.mark_end_of_verbatim_stdout)
        deferred.addErrback(
            self.handle_ignored_or_locked, cmd, component, target_state)
        deferred.addCallback(self.handle_output, cmd, component, target_state)
        deferred.addBoth(self.mark_action_as_finished, action)
        deferred.addErrback(yadtshell.twisted.report_error, self.logger.error)
        return deferred

    def mark_end_of_verbatim_stdout(self, ignored):
        self.logger.info('-' * 20 + ' end of verbatim stdout ' + '-' * 20)
        return ignored

    def handle_ignored_or_locked(self, failure, cmd, component, target_state):
        exitCode = getattr(failure.value, 'exitCode', None)
        if exitCode == 151:   # TODO use constant here
            self.logger.info(
                '%s is ignored, assuming successfull %s' % (component.uri, cmd))
            component.state = target_state
            self.pi.update((cmd, component), 'i')
            return
        if exitCode == 150:   # TODO use constant here
            self.logger.critical('%s %s failed, because %s is locked' %
                                 (cmd, component.uri, component.host_uri))
        return failure

    def handle_output(self, ignored, cmd, component, target_state=None, tries=0):
        if target_state:
            if component.state == target_state:
                self.pi.update((cmd, component), '0')
                self.logger.debug(
                    'successfully %sed %s' % (cmd, component.uri))
            elif target_state == yadtshell.settings.UPTODATE:
                component.state = target_state
                self.logger.debug('successfully updated %s' % component.uri)
            else:
                max_tries = getattr(component, 'status_max_tries', 1)
                if tries < max_tries:
                    delay = 0
                    if tries > 0:
                        self.logger.info('    %s %s, try %i of %i' %
                                         (cmd, component.uri, tries, max_tries - 1))
                        delay = 1
                    self.pi.update((cmd, component))
                    deferred = self.probe(
                        component, delay=delay, target_state=target_state)
                    deferred.addCallback(
                        self.handle_output, cmd, component, target_state, tries + 1)
                    deferred.addErrback(
                        yadtshell.twisted.report_error, self.logger.warning)
                    return deferred
                self.pi.update((cmd, component), 't')
                raise yadtshell.actions.ActionException(
                    '%s could not reach target state %s, is still %s' % (component.uri, target_state, component.state), 1)
        return ignored

    def issue_command(self,
                      component,
                      cmd,
                      target_state=None,
                      args=[],
                      kwargs={},
                      out_log_level=logging.DEBUG,
                      err_log_level=logging.WARN):
        cmdline = None
        try:
            fun = getattr(component, cmd, None)
            if fun:
                try:
                    cmdline = fun(*args, **kwargs)
                except TypeError:
                    try:
                        cmdline = fun(*args)
                    except TypeError:
                        try:
                            cmdline = fun(**kwargs)
                        except TypeError:
                            cmdline = fun()
        except ValueError, ve:
            print(str(ve))
            # self.logger.exception(ve)
            raise ve
        except Exception, ae:
            print(str(ae))
            self.logger.exception(ae)
            raise yadtshell.actions.ActionException(
                'problem during %s %s' % (cmd, component.uri), 1, ae)
        if not cmdline:
            self.logger.error('no cmdline?')
            raise yadtshell.actions.ActionException(
                'problem during %s %s: could not determine the cmdline' % (cmd, component.uri), 1, None)

        if isinstance(cmdline, defer.Deferred):  # TODO rename cmdline here
            self.logger.debug('deferred returned directly')
            self.pi.update((cmd, component))
            return cmdline

        p = yadtshell.twisted.YadtProcessProtocol(component,
                                                  cmd,
                                                  self.pi,
                                                  out_log_level=out_log_level,
                                                  err_log_level=err_log_level,
                                                  log_prefix=re.sub('^.*://', '', component.uri))
        p.target_state = target_state
        p.state = yadtshell.settings.UNKNOWN

        # if self.pi:
            # self.pi.observables.append(p)
        cmdline = shlex.split(cmdline.encode('ascii'))
        self.logger.debug('cmd: %s' % cmdline)
        reactor.spawnProcess(p, cmdline[0], cmdline, None)
        return p.deferred

    def log_host_finished(self, action):
        self.logger.info(yadtshell.settings.term.render(
            '    ${BOLD}%(uri)s finished successfully${NORMAL}' % vars(action)))

    def next_with_preconditions(self, queue):
        for task in queue:
            action = task.action
            if not isinstance(action, yadtshell.actions.ActionPlan):
                if action.state != yadtshell.actions.State.PENDING:
                    continue
                if not action.are_all_preconditions_met(self.components):
                    continue
            queue.remove(task)
            return task
        return None

    def calc_nr_workers(self, plan):
        if not self.parallel:
            return 1
        if self.parallel == 'max':
            return len(plan.actions)
        try:
            return int(self.parallel)
        except:
            return 1

    def report_plan_finished(self, result, plan, plan_name):
        self.logger.debug('%s finished' % plan_name)
        return result

    def handle_cb(self, protocol, plan, path=[]):
        return self.handle(plan, path)

    def handle(self, plan, path=[]):
        queue = []
        if isinstance(plan, yadtshell.actions.Action):
            action = plan
            this_path = path + [' %s@%s' % (action.cmd, action.uri)]
            queue.append(yadtshell.ActionManager.Task(
                fun=self.handle_action, action=action, path=this_path))
            plan_name = '/' + '/'.join(this_path)
            return yadtshell.defer.DeferredPool(plan_name, queue)

        if not len(plan.actions):
            deferred = defer.Deferred()
            reactor.callLater(0, deferred.callback, None)
            return deferred

        if not plan.nr_workers:
            plan.nr_workers = self.calc_nr_workers(plan)
        this_path = path + [plan.name]
        plan_name = '/' + '/'.join(this_path)

        for action in plan.actions:
            queue.append(yadtshell.ActionManager.Task(
                fun=self.handle, action=action, path=this_path))
        plan.nr_workers = min(plan.nr_workers, len(queue))
        self.logger.debug('%s : %s' % (plan_name, plan.meta_info()))

        pool = yadtshell.defer.DeferredPool(
            plan_name,
            queue,
            nr_workers=plan.nr_workers,
            next_task_fun=self.next_with_preconditions,
            nr_errors_tolerated=plan.nr_errors_tolerated)
        pool.addCallback(self.report_plan_finished, plan, plan_name)
        return pool

    def action(self,
               flavor,
               info_mode=False,
               dryrun=False,
               parallel=None,
               forcedyes=False,
               **kwargs):
        if not parallel:
            parallel = 1
        self.parallel = parallel
        self.dryrun = dryrun
        self.components = yadtshell.util.restore_current_state()
        self.orig_components = copy.deepcopy(self.components)
        action_plan_file = os.path.join(
            yadtshell.settings.OUT_DIR, flavor + '-action.plan')
        self.logger.debug('using action plan %s' % action_plan_file)

        yadtshell.settings.ybc.connect()

        action_plan = None
        try:
            f = open(action_plan_file)
            action_plan = yaml.load(f)
            f.close()
        except IOError, e:
            self.logger.warning(str(e))
            # return defer.succeed(None)
            deferred = defer.Deferred()
            reactor.callLater(0, deferred.errback, e)
                              # TODO mhhh: good practice?
            return deferred

        if not action_plan:
            self.logger.debug(
                '%s is empty, thus doing nothing' % action_plan_file)
            return defer.succeed(None)
        if dryrun:
            self.logger.debug('dryrun\ndryrun')
            self.logger.info('dryrun ' * 10)

        for service in [s for s in self.components.values() if s.type == yadtshell.settings.SERVICE]:
            service.state = yadtshell.settings.UNKNOWN
        for host in [h for h in self.components.values() if isinstance(h, yadtshell.components.Host)]:
            host.state = yadtshell.settings.UNKNOWN
            host.probed = yadtshell.settings.UNKNOWN

        if dryrun:
            log_plan_fun = self.logger.info
        else:
            log_plan_fun = self.logger.debug
        log_plan_fun('-' * 20 + ' plan dump ' + '-' * 20)
        for line in action_plan.dump(include_preconditions=True).splitlines():
            log_plan_fun(line)
        log_plan_fun('-' * 51)

        def remove_plan_file(result):
            if not self.dryrun:
                self.logger.debug(
                    'no problems so far, thus removing action plan %s' % action_plan_file)
                try:
                    os.remove(action_plan_file)
                except:
                    pass
            f = open(
                os.path.join(yadtshell.settings.OUT_DIR, 'current_state.components'), "w")
            pickle.dump(self.orig_components, f)
            f.close()
            return result

        def finish_progress_indicator(result, pi):
            if pi:
                pi.finish()
            return result

        if _user_should_acknowledge_plan(dryrun, flavor, forcedyes):
            dangerous_actions = filter_dangerous_actions(action_plan.list_actions)
            if dangerous_actions:
                print("\n\nThe following actions might be dangerous (i.e. host reboot), please confirm :\n")
                for da in dangerous_actions:
                    print(da.dump(depth=1, include_preconditions=False, include_target_value=False))
                print()
                if not confirm_transaction_by_user():
                    yadtshell.twisted.stop_and_return(EXIT_CODE_CANCELED_BY_USER)
                    return defer.succeed(None)

        self.pi = yadtshell.twisted.ProgressIndicator()
        deferred = None
        if not dryrun:
            deferred = yadtshell.util.start_ssh_multiplexed()
        try:
            if deferred:
                deferred.addCallback(self.handle_cb, action_plan)
            else:
                deferred = self.handle(action_plan)
        except ValueError, ve:
            reactor.callLater(0, deferred.errback, ve)
            return deferred

        deferred.addErrback(yadtshell.twisted.report_error, self.logger.error)
        deferred.addCallback(remove_plan_file)
        deferred.addBoth(finish_progress_indicator, self.pi)

        if not dryrun:
            deferred.addBoth(yadtshell.util.stop_ssh_multiplexed)

        return deferred


def filter_dangerous_actions(actions):
    def is_a_dangerous_action(action):
        return action.cmd in ['update'] and action.kwargs.get(yadtshell.constants.REBOOT_REQUIRED, False)
    return filter(is_a_dangerous_action, actions)


def _user_should_acknowledge_plan(dryrun, flavor, forcedyes):
    if dryrun:
        return False
    if forcedyes:
        return False
    if not sys.stdout.isatty():
        return False
    return flavor in ('update')
