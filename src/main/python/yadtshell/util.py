# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
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

from __future__ import absolute_import

import logging
import os.path
import pwd
import socket
import sys
import yaml
import shlex

from time import localtime, strftime
from twisted.internet import defer, reactor

import yadtshell.settings
import yadtshell.components


logger = logging.getLogger('util')

try:
    import cPickle as pickle
    logger.debug("using C implementation of pickle")
except ImportError:
    import pickle
    logger.debug("using default pickle")


def determine_loc_type(s):
    return {"host": s, "loc": s[0:3], "type": s[3:6], "loctype": s[0:6], "nr": s[6:8]}


def store(o, filename):
    with open(filename, "w") as f:
        pickle.dump(o, f)


def restore(filename):
    with open(filename) as f:
        return pickle.load(f)


def store2(data, filename):
    f = open(filename, 'w')
    for d in data:
        print >> f, d
    f.close()


def restore2(filename):
    f = open(filename)
    result = []
    for line in f:
        result.append(line.rstrip())
    f.close()
    return result


def dump_plan(flavor, plan):
    filename = flavor + '.plan'
    f = open(os.path.join(yadtshell.settings.OUT_DIR, filename), 'w')
    if not plan:
        logger.debug('%s plan is empty' % flavor)
    else:
        logger.debug('creating %s' % filename)
        yaml.dump(plan, f)
    f.close()


def dump_action_plan(flavor, plan):
    dump_plan(flavor + '-action', plan)


def restore_current_state():
    try:
        return restore(os.path.join(yadtshell.settings.OUT_DIR, 'current_state.components'))
    except IOError:
        logger.warning('no current state stored, try "status" first')
        sys.exit(1)


def get_mtime_of_current_state():
    return os.path.getmtime(os.path.join(yadtshell.settings.OUT_DIR, 'current_state.components'))  # TODO combine this with prev method


def is_up(state):
    return state in [yadtshell.settings.UP, yadtshell.settings.UPTODATE, yadtshell.settings.UPDATE_NEEDED, yadtshell.settings.INSTALLED]


def not_up(state):
    return not is_up(state)
    #return state in [None, settings.UNKNOWN, settings.DOWN, settings.MISSING, settings.UPDATE_NEEDED]


def render_state(state, just='left', width=10):
    if not_up(state):
        color = 'RED'
    else:
        color = 'GREEN'
    if just == 'left':
        state = state.ljust(width)
    else:
        state = state.rjust(width)
    return yadtshell.settings.term.render('${%(color)s}${BOLD}%(state)s${NORMAL}' % locals())


def render_component_state(uri, state):
    return '%s  %8s:%-s' % (
        render_state(str(state), 'right'),
        uri.split(':', 1)[0],
        uri.split(':', 1)[1],
    )


def log_subprocess(pipe, stdout_level=logging.DEBUG, stderr_level=logging.WARNING):
    return_code = pipe.wait()
    for line in pipe.stderr:
        logger.log(stderr_level, 'stderr ' + line.strip())
    for line in pipe.stdout:
        logger.log(stdout_level, 'stdout ' + line.strip())
    logger.debug('return code: %i' % return_code)
    return return_code


def get_locking_user_info():
    """@Deprecated, use Helper.get_user_info() instead"""
    user = pwd.getpwuid(os.getuid())[0]
    yadt_host = socket.getfqdn()
    working_copy = os.getcwd()
    owner = user + '@' + yadt_host + ':' + working_copy
    when = strftime("%a, %d %b %Y %H:%M:%S %Z", localtime())
    pid = os.getpid()

    return {"user": user,
            "yadt_host": yadt_host,
            "working_copy": working_copy,
            "owner": owner,
            "when": when,
            "pid": pid,
            }


def get_yaml(adict):
    return yaml.dump(adict, default_flow_style=False)


def get_status_line(components):
    nr_services_total = nr_services_up = 0
    nr_frontservices_total = nr_frontservices_up = 0
    for service in [s for s in components.values() if isinstance(s, yadtshell.components.Service)]:
        nr_services_total += 1
        if service.is_up():
            nr_services_up += 1
        if getattr(service, 'is_frontservice', False):
            nr_frontservices_total += 1
            if service.is_up():
                nr_frontservices_up += 1

    nr_hosts_uptodate = nr_hosts_total = 0
    for host in [h for h in components.values() if isinstance(h, yadtshell.components.Host)]:
        nr_hosts_total += 1
        if host.is_uptodate():
            nr_hosts_uptodate += 1

    if nr_hosts_total == 0:
        return 'no hosts configured'

    services_desc = 'services'
    if nr_frontservices_total > 0:
        nr_services_up = nr_frontservices_up
        nr_services_total = nr_frontservices_total
        services_desc = 'frontservices'
    if nr_services_up > 0:
        services_up_ratio = 100 * nr_services_up / nr_services_total
    else:
        services_up_ratio = 0
    hosts_uptodate_ratio = 100 * nr_hosts_uptodate / nr_hosts_total

    return '%3.0f%% %3.0f%% | %i/%i %s up, %i/%i hosts uptodate' % (
        services_up_ratio, hosts_uptodate_ratio,
        nr_services_up, nr_services_total, services_desc,
        nr_hosts_uptodate, nr_hosts_total)


def start_ssh_multiplexed(hosts=None):
    if not hosts:
        hosts = yadtshell.settings.TARGET_SETTINGS['hosts']

    def start_ssh(protocol, host):
        logger.debug('start_ssh %s' % host)
        start_multiplexing_call = shlex.split('%s -fN -o ControlMaster=yes %s' % (yadtshell.settings.SSH, host))
        p = yadtshell.twisted.YadtProcessProtocol(host, 'start_ssh', wait_for_io=False)
        p.deferred = defer.Deferred()
        logger.debug('cmd: %s' % start_multiplexing_call)
        reactor.spawnProcess(p, start_multiplexing_call[0], start_multiplexing_call, None)
        return protocol

    def check_ssh(host):
        ssh_check_cmds = shlex.split('%s -O check %s' % (yadtshell.settings.SSH, host))
        p = yadtshell.twisted.YadtProcessProtocol(host, 'check_ssh')
        p.deferred = defer.Deferred()
        logger.debug('cmd: %s' % ssh_check_cmds)
        reactor.spawnProcess(p, ssh_check_cmds[0], ssh_check_cmds, None)
        p.deferred.addErrback(start_ssh, host)
        return p.deferred

    return defer.DeferredList([check_ssh(host) for host in hosts])


def stop_ssh_multiplexed(ignored, hosts=None):

    def stop_ssh(host):
        ssh_stop_cmds = shlex.split('%s -O exit %s' % (yadtshell.settings.SSH, host))
        p = yadtshell.twisted.YadtProcessProtocol(host, 'stop_ssh')
        p.deferred = defer.Deferred()
        logger.debug('cmd: %s' % ssh_stop_cmds)
        reactor.spawnProcess(p, ssh_stop_cmds[0], ssh_stop_cmds, None, childFDs={2: 3})
        return p.deferred

    if not hosts:
        hosts = yadtshell.settings.TARGET_SETTINGS['hosts']

    dl = defer.DeferredList([stop_ssh(host) for host in hosts])

    dl.addCallback(lambda _: ignored)
    return dl


def inbound_deps(service, components):
    inbound_services = [s for s in service.needed_by]
    for dependent_service in service.needed_by:
        inbound_services.extend(inbound_deps(components[dependent_service], components))
    return inbound_services


def outbound_deps(service, components):
    outbound_services = [s for s in service.needs if 'service://' in s]
    for needed_service in [s for s in service.needs if 'service://' in s]:
        outbound_services.extend(outbound_deps(components[needed_service], components))
    return outbound_services


def compute_dependency_scores(components):
    servicedefs = dict((component.uri, component) for component in components.values() if isinstance(component, yadtshell.components.Service))
    for service, servicedef in servicedefs.iteritems():
        outbound_edges = len(outbound_deps(servicedef, components))
        inbound_edges = len(inbound_deps(servicedef, components))
        servicedef.dependency_score = inbound_edges - outbound_edges
