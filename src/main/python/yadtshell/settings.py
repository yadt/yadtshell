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

import os.path
import sys
import logging
import time
import filecmp
import shutil
import yaml

import hostexpand.HostExpander

import yadtshell.TerminalController
from yadtshell.helper import condense_hosts, condense_hosts2, get_user_info
from yadtshell.loggingtools import create_next_log_file_name_with_command_arguments_as_tag
import yadtshell.helper
from yadtshell.loggingtools import configure_logger_output_stream_by_level

sys.path.append('/etc/yadtshell')

DEFAULT_LOG_DIR = '/tmp/logs/yadtshell'
USER_INFO = get_user_info()
OUTPUT_DIR = os.path.expanduser('~%s/.yadtshell' % USER_INFO['user'])

OUT_DIR = os.path.join(OUTPUT_DIR, 'tmp', os.getcwd().lstrip('/'))
TODAY = None
STARTED_ON = None
SSH = 'ssh'  # overwritten later for SSH multiplexing

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

message_formatter = logging.Formatter('%(levelname)-8s %(message)s')
# DO NOT USE A KWARG : it's 'strm' in python<2.6 and has
# been renamed to 'stream' in 2.7 with NO DOCUMENTATION...
console_stdout_handler = logging.StreamHandler(sys.stdout)
console_stderr_handler = logging.StreamHandler(sys.stderr)
configure_logger_output_stream_by_level(
    console_stderr_handler, console_stdout_handler)
console_stdout_handler.setFormatter(message_formatter)
console_stderr_handler.setFormatter(message_formatter)
root_logger.addHandler(console_stdout_handler)
root_logger.addHandler(console_stderr_handler)

# default values used when file can't be loaded and in unit tests.
VIEW_SETTINGS = {'info-view': ['matrix', 'color', 'maxcols']}


class SettingsError(BaseException):
    pass

logger = logging.getLogger('settings')

try:
    from loggingconf import *  # NOQA
except Exception as e:
    root_logger.debug(e)
    if not os.path.isdir(DEFAULT_LOG_DIR):
        os.makedirs(DEFAULT_LOG_DIR)  # pragma: no cover
    LOG_DIR_PREFIX = DEFAULT_LOG_DIR


def initialize_broadcast_client():  # pragma: no cover
    global DummyBroadcaster, broadcasterconf_imported, broadcasterconf, e

    class DummyBroadcaster(object):

        def __init__(self):
            self.target = 'dummy-target'

        def addOnSessionOpenHandler(self, *args, **kwargs):
            pass

        def sendServiceChange(self, data, **kwargs):
            pass

        def sendFullUpdate(self, data, **kwargs):
            pass

        def connect(self):
            pass

        def publish_cmd(self, *args, **kwargs):
            pass

        def _sendEvent(self, *args, **kwargs):
            pass

    broadcasterconf_imported = False
    try:
        sys.path.append("/etc/yadtbroadcast-client/")
        import broadcasterconf  # NOQA
        sys.path.pop()
        broadcasterconf_imported = True
    except Exception as e:
        logger.warn('no broadcaster config found')
        logger.warn(e)


def _load_target_file(target_filename, targets_dir, target_basename, visited=None):
    if not visited:
        visited = []

    if target_filename in visited:
        return {}

    visited.append(target_filename)

    try:
        settings_file = open(target_filename)
    except EnvironmentError:
        raise SettingsError(
            'cannot find target definition file %s, aborting' % target_filename)
    target_settings = yaml.load(settings_file)
    settings_file.close()

    if target_settings.get('hosts') is None:  # hosts:\n means hosts==None in YAML
        target_settings['hosts'] = []         # so either the key is missing OR hosts is a null-value
    for include in target_settings.get('includes', []):
        subtarget_filename = os.path.join(
            targets_dir, include, target_basename)
        subtarget_settings = _load_target_file(
            subtarget_filename, targets_dir, target_basename, visited)
        target_settings['hosts'].extend(subtarget_settings.get('hosts', []))
    return target_settings


def load_target_file(target_basename):
    targets_dir = os.getenv("TARGETS_DIR", os.path.dirname(os.getcwd()))
    target_name = os.path.basename(os.getcwd())
    target_filename = os.path.join(targets_dir, target_name, target_basename)
    target_settings = _load_target_file(
        target_filename, targets_dir, target_basename)
    target_settings.setdefault('name', target_name)
    target_settings = expand_hosts(target_settings)
    return target_settings


def expand_hosts(target_settings):
    he = hostexpand.HostExpander.HostExpander(
        outputformat=hostexpand.HostExpander.HostExpander.FQDN)
    target_settings['original_hosts'] = target_settings['hosts']
    target_settings['hosts'] = he.expand(target_settings['hosts'])
    return target_settings


def load_settings_and_create_dirs(log_to_file=True):
    TARGET_BASENAME = 'target'

    global TARGET_SETTINGS
    TARGET_SETTINGS = load_target_file(TARGET_BASENAME)

    initialize_broadcast_client()

    os.umask(2)

    try:
        os.makedirs(OUT_DIR)
    except OSError as e:
        if e.errno != 17:   # 17: file exists
            root_logger.critical('cannot write to out dir %s' % OUT_DIR)
            root_logger.exception(e)
            sys.exit(1)
        pass

    global TODAY
    TODAY = time.strftime('%Y-%m-%d')

    TIME_FORMAT = '%Y-%m-%d--%H-%M-%S'
    global STARTED_ON
    STARTED_ON = time.strftime(TIME_FORMAT)

    global term
    term = yadtshell.TerminalController.TerminalController()

    global ybc
    if broadcasterconf_imported:
        ybc = broadcasterconf.create(TARGET_SETTINGS['name'])
    else:
        ybc = DummyBroadcaster()

    LOG_DIR = os.path.join(LOG_DIR_PREFIX, TODAY)
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        if e.errno != 17:   # 17: file exists
            root_logger.critical('cannot write to log dir %s' % LOG_DIR)
            root_logger.exception(e)
            sys.exit(1)

    global log_file
    log_file = create_next_log_file_name_with_command_arguments_as_tag(
        log_dir=LOG_DIR,
        target_name=TARGET_SETTINGS['name'],
        command_start_timestamp=STARTED_ON,
        user_name=USER_INFO['user'],
        source_host=USER_INFO['yadt_host'].split('.')[0],
        command_arguments=sys.argv
    )

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s', '%Y%m%d-%H%M%S')

    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logger.debug(yaml.dump(USER_INFO, default_flow_style=False))
    logger.debug('Called "{0}"'.format(' '.join(sys.argv)))
    logger.debug('output dir is %s' % OUTPUT_DIR)

    OUT_TARGET_FILE = os.path.join(OUT_DIR, TARGET_BASENAME)
    try:
        changed = not filecmp.cmp(TARGET_BASENAME, OUT_TARGET_FILE)
        if changed:
            logger.info(
                'target settings have changed since last call, thus cleaning cached data')
    except OSError:
        changed = True

    if changed:
        shutil.rmtree(OUT_DIR)
        os.makedirs(OUT_DIR)
        shutil.copy2(TARGET_BASENAME, OUT_TARGET_FILE)

    global VIEW_SETTINGS
    VIEW_SETTINGS_FILE = 'view'
    try:
        view_file = open(VIEW_SETTINGS_FILE)
        VIEW_SETTINGS = yaml.load(view_file)
        view_file.close()
    except:
        logger.debug(
            '"view" file not found, falling back to default values: %s' %
            VIEW_SETTINGS)
    hosts_condensed_filename = os.path.join(OUT_DIR, 'hosts_condensed')
    with open(hosts_condensed_filename, 'w') as hosts_condensed_file:
        condensed = condense_hosts2(condense_hosts(TARGET_SETTINGS['hosts']))
        hosts_condensed_file.write(' '.join(condensed))

    def list_selected_hosts():
        return 'You are working now on %s\n\nas full list: %s\n' % (
            term.render('${BOLD}') + ', '.join(
                condense_hosts2(
                    condense_hosts(
                        TARGET_SETTINGS['hosts']))) + term.render('${NORMAL}'),
            ', '.join(TARGET_SETTINGS['hosts']),
        )

    identity = TARGET_SETTINGS.get('identity')
    login = TARGET_SETTINGS.get('login')
    credentials = ''
    if identity:
        credentials += ' -i %(identity)s' % locals()
    if login:
        credentials += ' -l %(login)s' % locals()
    CONNECTIONS_DIR = os.path.join(OUTPUT_DIR, 'connections')

    global SSH_CONTROL_PATH
    SSH_CONTROL_PATH = os.path.join(CONNECTIONS_DIR, '%h')
    try:
        os.makedirs(CONNECTIONS_DIR)
    except OSError:
        pass
    global SSH
    SSH = 'ssh -o ControlPath=%s -A %s -T -o ConnectTimeout=4 -o BatchMode=yes -o CheckHostIP=no -o StrictHostKeyChecking=no -q' % (
        SSH_CONTROL_PATH, credentials)

    global tracking_id
    tracking_id = None


HOST = "host"
SERVICE = "service"
ARTEFACT = "artefact"
CONFIG = 'config'
TARGET = 'target'
REVISION = 'revision'

CURRENT = 'current'
NEXT = 'next'
PREVIOUS = 'previous'

DIFFERENT_VERSION = "version mismatch"
OUTDATED_DEPENDENCY = "outdated dependency"


START = 'start'
STOP = 'stop'
STATUS = 'status'
INSTALL = 'install'
PURGE = 'purge'
UPDATE = 'update'
BOOTSTRAP = 'bootstrap'


INSTALLED = 'installed'
UNKNOWN = 'unknown'
DOWN = 'down'
UP = 'up'
UPTODATE = 'uptodate'
UPDATE_NEEDED = 'update_needed'
SUCCESS = 'success'
FINISH = 'finish'


MISSING = 'missing'
EMPTY = ''

STATE_DESCRIPTIONS = {
    0: UP,
    1: DOWN,
    2: DOWN,
    3: DOWN,
    UP: UP,
    DOWN: DOWN,
    UNKNOWN: UNKNOWN,
}
