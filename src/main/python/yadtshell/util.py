#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
from time import localtime, strftime
import os.path
import logging
import pwd
import socket
import threading
import yaml
import sys
import subprocess

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


def retrieve_hostloctype_data(loc_type, d, fallback={}):
    if not type(d) is dict:
        return fallback
    for key in [loc_type[k] for k in ['host', 'loctype', 'type', 'loc']] + ['all']:
        if key in d:
            logger.debug('key %s matches for loc_type %s' % (key, loc_type))
            return d.get(key)
    return fallback

def flatten_data(data):
    for r in data:
        if type(r) is dict:
            yield r.keys()[0]
        else:
            yield r

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
    for host in hosts:
        ssh_check_cmds = ['ssh',
            '-o', 'ControlPath=%s' % yadtshell.settings.SSH_CONTROL_PATH, 
            '-O', 'check', host]
        ssh_check_call = subprocess.Popen(ssh_check_cmds, stderr=subprocess.PIPE)
        ssh_check_call.communicate()
        if ssh_check_call.returncode != 0:
            start_multiplexing_call = ['ssh', '-fN', '-o', 'ControlPath=%s' % yadtshell.settings.SSH_CONTROL_PATH, '-o', 'ControlMaster=yes', host]
            logger.debug(' '.join(start_multiplexing_call))
            is_started = subprocess.call(start_multiplexing_call)
            logger.debug(is_started)
            logger.debug('multiplexed ssh connection to %(host)s created' % locals())

def stop_ssh_multiplexed(ignored, hosts=None):
    if not hosts:
        hosts = yadtshell.settings.TARGET_SETTINGS['hosts']
    for host in hosts:
        logger.debug('multiplexed ssh connections to %(host)s removed' % locals())
        ssh_check_cmds = ['ssh',
            '-o', 'ControlPath=%s' % yadtshell.settings.SSH_CONTROL_PATH, 
            '-O', 'exit', host]
        #ignore = subprocess.call(ssh_check_call)
        stop_multiplexing_call = subprocess.Popen(ssh_check_cmds, stderr=subprocess.PIPE)
        stop_multiplexing_call.communicate()
    return ignored







## {{{ http://code.activestate.com/recipes/483752/ (r1)
class TimeoutError(Exception):
    pass

def timelimit(timeout):
    def internal(function):
        def internal2(*args, **kw):
            class Calculator(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None
                def run(self):
                    try:
                        self.result = function(*args, **kw)
                    except:
                        self.error = sys.exc_info()[0]
            c = Calculator()
            c.start()
            c.join(timeout)
            if c.isAlive():
                raise TimeoutError
            if c.error:
                raise c.error
            return c.result
        return internal2
    return internal


class Timeout(object):
    def __init__(self, seconds):
        self.seconds = seconds
        
    def __call__(self, fun):
        pass
    
    
    
@timelimit(2)
def test_timeout():
    print 'started'
    import time
    time.sleep(4)
    print 'stopped'

if __name__ == '__main__':
    timelimit(2)
    sys.exit(0)
    try:
        test_timeout()
    except TimeoutError:
        print 'TIMEOUT'

    print 'done'
