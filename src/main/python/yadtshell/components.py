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

import logging
import os
import subprocess
import sys
import yaml
import shlex

from twisted.internet import reactor, task

from yadtshell.util import calculate_max_tries_for_interval_and_delay
from yadtshell.helper import get_user_info
from yadtshell.twisted import YadtProcessProtocol
import yadtshell


logger = logging.getLogger('components')


class Component(object):

    def __init__(self, t, host, name=None, version=None):
        """`self` can be a string/unicode or a Host instance.
        But note that some subclasses require a Host instance in their constructors.
        """
        self.type = t
        if type(host) in [str, unicode]:
            self.host = host
        else:
            self.host = host.host
            self.fqdn = host.fqdn
        self.host_uri = yadtshell.uri.create(yadtshell.settings.HOST, self.host)
        self.name = getattr(self, 'name', name)
        if self.name is not None:
            self.name = self.name.rstrip('/').split('/', 1)[0]
        self.version = version
        if self.version is not None:
            self.version = str(self.version)
        self.uri = yadtshell.uri.create(self.type, self.host, self.name, self.version)
        self.version = yadtshell.uri.parse(self.uri)['version']
        self.name_and_version = yadtshell.uri.as_source_file(self.uri)
        self.state = yadtshell.settings.UNKNOWN
        self.revision = yadtshell.settings.EMPTY
        self.needs = getattr(self, 'needs', set())
        self.needed_by = set()
        self.config_prefix = yadtshell.settings.TARGET_SETTINGS['name']

    def is_touched_also(self, other):
        return True

    def __str__(self):
        return self.uri

    def dump(self):
        res = self.uri + "\n"
        res += yaml.dump(self)
        return res

    def is_up(self):
        return not yadtshell.util.not_up(self.state)

    def is_unknown(self):
        return self.state == yadtshell.settings.UNKNOWN

    def create_remote_log_filename(self, tag=None):
        return yadtshell.loggingtools.create_next_log_file_name(
            yadtshell.settings.TODAY,
            yadtshell.settings.TARGET_SETTINGS['name'],
            yadtshell.settings.STARTED_ON,
            yadtshell.settings.USER_INFO['user'],
            self.host,
            tag
        )

    def remote_call(self, cmd, tag=None, force=False):
        if not cmd:
            return
        if type(cmd) not in [str, unicode]:
            cmd = '\n'.join(cmd)

        ssh_cmd = yadtshell.settings.SSH
        if hasattr(self, 'fqdn'):
            host = self.fqdn
        else:
            # TODO valid for uninitialized hosts
            host = self.host
        # TODO only suitable for service objects!
        service = self.name
        remotecall_script = '/usr/bin/yadt-remotecall'
        log_file = self.create_remote_log_filename(tag=tag)
        owner = get_user_info()['owner']
        force_flag = {False: '', True: ' --force'}[force]
        complete_cmd = '%(ssh_cmd)s %(host)s WHO="%(owner)s" YADT_LOG_FILE="%(log_file)s" "yadt-command %(cmd)s%(force_flag)s" ' % locals()
        return complete_cmd

    def local_call(self, cmd, tag=None, guard=True, force=False, no_subprocess=True):
        if not cmd:
            return
        if type(cmd) is str:
            cmds = cmd
        else:
            cmds = '\n'.join(cmd)
        print cmds
        if no_subprocess:
            return cmds
        if guard:
            sp = self.remote_call(": #check service callable",
                                  tag='check_service_callable',
                                  force=force)
            returncode = yadtshell.util.log_subprocess(sp)
            if returncode != 0:
                return returncode
        pipe = subprocess.Popen(
            cmds,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        pipe.stdin.flush()
        pipe.stdin.close()
        return pipe

    def _create_owner_file(self, lockinfo, filename, force=False, tag=None):
        """@return: integer The error code of the remote call"""
        dirname = os.path.dirname(filename)
        cmd = '''umask 0002 && mkdir -pv %s && echo -e '%s' > %s''' % (
            dirname, yadtshell.util.get_yaml(lockinfo), filename)
        return self.remote_call(cmd, tag, force=force)

    def _remove_owner_file(self, lockinfo, filename, force=False, tag=None):
        """@return: integer The error code of the remote call"""
        cmd = "rm -fv %(filename)s" % locals()
        return self.remote_call(cmd, tag, force=force)


class MissingComponent(Component):

    def __init__(self, s):
        parts = yadtshell.uri.parse(s)
        Component.__init__(self, parts['type'], parts['host'], parts['name'], parts['version'])
        self.state = yadtshell.settings.MISSING


class ComponentDict(dict):

    def __init__(self):
        dict.__init__(self)
        self._add_when_missing_ = False

    def _key_(self, key):
        try:
            return self._key_(key.uri)
        except AttributeError:
            return key

    def __getitem__(self, key):
        if self._key_(key) not in self and self._add_when_missing_:
            logger.debug('missing ' + key)
            self[self._key_(key)] = MissingComponent(self._key_(key))
        return dict.__getitem__(self, self._key_(key))

    def get(self, key, default=None):
        if self._key_(key) not in self and self._add_when_missing_:
            logger.debug('missing' + key)
            self[self._key_(key)] = MissingComponent(key)
        return dict.get(self, self._key_(key), default)

    def __setitem__(self, key, value):
        # logger.debug('adding ' + self._key_(key) + ' ' + getattr(value,
        # 'state', ''))
        return dict.__setitem__(self, self._key_(key), value)


class ComponentSet(set):

    def __init__(self, components=None):
        self.components = components
        self._set = set([])

    def _key_(self, item):
        try:
            return str(item.uri)
        except AttributeError:
            return str(item)

    def add(self, item, check=False):
        key = self._key_(item)
        logger.debug('adding ' + key)
        if key not in self.components and check:
            logger.warning('key %(key)s not found, ignoring' % locals())
            # logger.warning('known keys: ' + ',
            # '.join(self.components.keys()))
            return None
        return self._set.add(key)

    def __iter__(self):
        if self.components is None:
            for item in self._set:
                yield item
        else:
            for item in self._set:
                result = self.components.get(item)
                yield result

    def update(self, other):
        for c in other:
            self.add(c)

    def __contains__(self, item):
        return self._key_(item) in self._set


class Host(Component):

    def __init__(self, fqdn):
        self.fqdn = fqdn
        self.hostname = fqdn.split('.')[0]
        self.next_artefacts = []
        self.services = {}
        self.lockstate = None
        self.is_locked = None
        self.is_locked_by_other = None
        self.is_locked_by_me = None
        self.ssh_poll_max_seconds = yadtshell.constants.SSH_POLL_MAX_SECONDS_DEFAULT
        self.reboot_required_to_activate_latest_kernel = False
        self.reboot_required_after_next_update = False

        Component.__init__(self, yadtshell.settings.HOST, self.hostname)
        self.logger = logging.getLogger(self.uri)

    def set_attrs_from_data(self, data):
        for key, value in data.iteritems():
            if key == "hostname" and value != self.hostname:
                self.logger.warning("Hostname %(hostname)s doesn't match FQDN %(fqdn)." % data)
            setattr(self, key, value)
        self.convert_obsolete_services(self.services)
        self.state = ['update_needed', 'uptodate'][not self.next_artefacts]
        self.loc_type = yadtshell.util.determine_loc_type(self.hostname)
        self.update_attributes_after_status()

    def convert_obsolete_services(self, old_services):
        if len(old_services) > 0 and type(old_services) is list:
            self.services = dict()
            for entry in old_services:
                self.services.update(entry)

    @property
    def reboot_required(self):
        return self.reboot_required_after_next_update or self.reboot_required_to_activate_latest_kernel

    def is_reachable(self):
        return True

    def update(self, reboot_required=False):
        next_artefacts = [uri.replace('/', '-', 1)
                          for uri in self.next_artefacts]
        if not reboot_required:
            return self.remote_call('yadt-host-update %s' % ' '.join(next_artefacts),
                                    '%s_%s' % (self.hostname, yadtshell.settings.UPDATE))

        update_and_reboot_command = self.remote_call(
            'yadt-host-update -r %s' % ' '.join(next_artefacts),
            '%s_%s' % (self.hostname, yadtshell.settings.UPDATE))
        p = YadtProcessProtocol(self, update_and_reboot_command, out_log_level=logging.INFO)
        p.target_state = yadtshell.settings.UPTODATE
        p.state = yadtshell.settings.UNKNOWN

        def handle_rebooting_machine(failure, ssh_poll_max_seconds):
            if failure.value.exitCode == 152:
                raise yadtshell.actions.ActionException(
                    'Timed out while waiting for %s to reboot' % self.uri)
            elif failure.value.exitCode == 255:
                logger.info("%s: rebooting now" % self.uri)
                return poll_rebooting_machine()
            return failure

        def poll_rebooting_machine(count=1):
            max_tries = calculate_max_tries_for_interval_and_delay(interval=self.ssh_poll_max_seconds,
                                                                   delay=yadtshell.constants.SSH_POLL_DELAY)
            logger.info("%s: polling for ssh connect, try %i of %i" %
                        (self.uri, count, max_tries))
            poll_command = self.remote_call('uptime', '%s_poll' % self.hostname)
            poll_protocol = YadtProcessProtocol(self, poll_command, out_log_level=logging.INFO)
            poll_protocol.ssh_poll_count = count
            if (count * yadtshell.constants.SSH_POLL_DELAY) < self.ssh_poll_max_seconds:
                poll_protocol.deferred.addErrback(
                    lambda x: task.deferLater(reactor,
                                              yadtshell.constants.SSH_POLL_DELAY,
                                              poll_rebooting_machine,
                                              count + 1)
                )
            cmdline = shlex.split(poll_protocol.cmd)
            reactor.spawnProcess(poll_protocol, cmdline[0], cmdline, None)

            return poll_protocol.deferred

        p.deferred.addErrback(handle_rebooting_machine, self.ssh_poll_max_seconds)

        def display_reboot_info(protocol):
            if hasattr(protocol, 'ssh_poll_count'):
                logger.info('%s: reboot took %d seconds' %
                            (self.uri, protocol.ssh_poll_count * yadtshell.constants.SSH_POLL_DELAY))
            return protocol
        p.deferred.addCallback(display_reboot_info)

        cmdline = shlex.split(p.cmd.encode('ascii'))
        reactor.spawnProcess(p, cmdline[0], cmdline, None)
        return p.deferred

    def bootstrap(self):
        pass    # TODO to be implemented

    def is_uptodate(self):
        return self.state == yadtshell.settings.UPTODATE

    def is_update_needed(self):
        return self.state == yadtshell.settings.UPDATE_NEEDED

    def probe(self):
        return self.remote_call('yadt-host-status')

    def probe_uptodate(self):
        return yadtshell.util.log_subprocess(self.remote_call('yadt-host-status', '%s_probe' % self.hostname))

    def get_lock_dir(self):
        return self.defaults['YADT_LOCK_DIR']

    def get_ignored_dir(self):
        return self.defaults['YADT_LOCK_DIR']

    def get_lock_owner(self):
        if self.lockstate:
            return self.lockstate["owner"]
        else:
            return None

    def lock(self, message=None, force=False, **kwargs):
        def strip_quotes_from_message(message):
            return message.replace("'", "").replace('"', '')
        if not message:
            raise ValueError('the "message" parameter is mandatory')
        lockinfo = get_user_info()
        lockinfo["message"] = message
        lockinfo["force"] = force
        return self.remote_call(
            "yadt-host-lock '%s'" % strip_quotes_from_message(message),
            'lock_host',
            force)

    def unlock(self, force=False, **kwargs):
        return self.remote_call('yadt-host-unlock', "unlock_host", force)

    def update_attributes_after_status(self):
        self.is_locked = not self.lockstate is None

        lockinfo = get_user_info()
        lock_owner = None
        if self.lockstate:
            lock_owner = self.lockstate.get("owner")
        self.is_locked_by_me = self.is_locked and lock_owner and lock_owner == lockinfo["owner"]
        self.is_locked_by_other = self.is_locked and not self.is_locked_by_me

        logger.debug("is_locked=" + repr(self.is_locked) + ", is_locked_by_me=" + repr(
            self.is_locked_by_me) + ", is_locked_by_other=" + repr(self.is_locked_by_other))


class UnreachableHost(Component):

    def __init__(self, fqdn):
        self.fqdn = fqdn
        self.hostname = fqdn.split('.')[0]
        Component.__init__(self, yadtshell.settings.HOST, self.hostname)

    def is_reachable(self):
        return False

    def is_unknown(self):
        return True

    @property
    def next_artefacts(self):
        return {}

    @property
    def is_locked_by_other(self):
        return False

    @property
    def is_locked_by_me(self):
        return False


class Artefact(Component):

    def __init__(self, host, name, version=None):
        Component.__init__(self, yadtshell.settings.ARTEFACT, host, name, version)
        # self.needs.add(uri.create(settings.HOST, host.host))

    def updateartefact(self):
        return self.remote_call('yadt-artefact-update %s' % self.name,
                                'artefact_%s_%s_%s' % (self.host, self.name, yadtshell.constants.UPDATEARTEFACT))


class Service(Component):

    def __init__(self, host, name, settings=None):
        Component.__init__(self, yadtshell.settings.SERVICE, host, name)

        self.fqdn = host.fqdn
        self.needs_services = []
        self.needs_artefacts = []
        self.needs = set()
        self.needs.add(host.uri)

        for k in settings:
            setattr(self, k, settings[k])
        extras = settings.get('extra', [])
        for k in extras:
            if hasattr(self, k):
                getattr(self, k).extend(extras[k])
            else:
                setattr(self, k, extras[k])

        for n in self.needs_services:
            if n.startswith(yadtshell.settings.SERVICE):
                self.needs.add(n % locals())
            else:
                self.needs.add(yadtshell.uri.create(
                    yadtshell.settings.SERVICE, host.host, n % locals()))
        for n in self.needs_artefacts:
            self.needs.add(yadtshell.uri.create(yadtshell.settings.ARTEFACT,
                                                host.host,
                                                n % locals() + "/" + yadtshell.settings.CURRENT))
        # self.needs.add(uri.create(yadtshell.settings.HOST, host.host))

        self.state = yadtshell.settings.STATE_DESCRIPTIONS.get(
            settings.get('state'),
            yadtshell.settings.UNKNOWN)
        self.script = None

    def stop(self, force=False, **kwargs):
        return self.remote_call(
            self._retrieve_service_call(yadtshell.settings.STOP),
            '%s_%s' % (self.name, yadtshell.settings.STOP), force)

    def start(self, force=False, **kwargs):
        return self.remote_call(
            self._retrieve_service_call(yadtshell.settings.START),
            '%s_%s' % (self.name, yadtshell.settings.START), force)

    def status(self):
        return self.remote_call(
            self._retrieve_service_call(yadtshell.settings.STATUS),
            tag='%s_%s' % (self.name, yadtshell.settings.STATUS))

    def _retrieve_service_call(self, action):
        return 'yadt-service-%s %s' % (action, self.name)

    def ignore(self, message=None, **kwargs):
        if not message:
            raise ValueError('the "message" parameter is mandatory')
        tag = "ignore_%s" % self.name
        force = kwargs.get('force', False)
        return self.remote_call('yadt-service-ignore %s "%s"' % (self.name, message), tag, force)

    def unignore(self, **kwargs):
        tag = "unignore_%s" % self.name
        return self.remote_call('yadt-service-unignore %s' % self.name, tag)


def do_cb(protocol, args, opts):
    return do(args, opts)


def do(args, opts):
    cmd = args[0]
    component_names = args[1:]
    if not component_names:
        logger.error('no components given to "%(cmd)s", aborting' % locals())
        sys.exit(1)

    components = yadtshell.util.restore_current_state()
    component_names = yadtshell.helper.expand_hosts(component_names)
    component_names = yadtshell.helper.glob_hosts(components, component_names)

    for component_name in component_names:
        component = components.get(component_name, None)
        if not component:
            component = components[yadtshell.uri.change_version(component_name, 'current')]
        fun = getattr(component, cmd, None)
        import inspect
        if inspect.ismethod(fun):
            try:
                sp = fun(**opts)
            except TypeError:
                sp = fun()
        else:
            logger.error('"%(cmd)s" is not defined for %(component_name)s, aborting' % locals())
            sys.exit(2)
        logger.debug('%(cmd)sing %(component_name)s' % locals())
        try:
            logger.debug('executing fun ' + str(fun))
            if isinstance(sp, subprocess.Popen):
                exit_code = yadtshell.util.log_subprocess(sp, stdout_level=logging.INFO)
            else:
                exit_code = sp
            logger.debug('exit code %(exit_code)s' % locals())
        except AttributeError, ae:
            logger.warning('problem while executing %(cmd)s on %(component_name)s' % locals())
            logger.exception(ae)
