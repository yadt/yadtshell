#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import os.path
import pprint
import sys
import logging
import time
import filecmp
import shutil
import re

import yaml

import hostexpand.HostExpander

import yadtshell.TerminalController
from yadtshell.helper import condense_hosts, condense_hosts2, get_user_info, create_log_filename
import yadtshell.helper  # TODO refactor imports

sys.path.append('/etc/yadtshell')

USER_INFO = get_user_info()
OUTPUT_DIR = os.path.expanduser('~%s/.yadtshell' % USER_INFO['user'])

OUT_DIR = os.path.join(OUTPUT_DIR, 'tmp', os.getcwd().lstrip('/'))   # TODO rename to TMP_DIR?

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

sf = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', '%Y%m%d-%H%M%S')
mf = logging.Formatter('%(levelname)8s %(name)25s  %(message)s', '%Y%m%d-%H%M%S')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(mf)
root_logger.addHandler(ch)

logger = logging.getLogger('settings')


try:
    from loggingconf import *
except Exception, e:
    root_logger.debug(e)
    LOG_DIR_PREFIX = '/var/log/yadtshell'


class DummyBroadcaster(object):
    def addOnSessionOpenHandler(self, *args, **kwargs):
        pass

    def sendServiceChange(self, data):
        pass

    def sendFullUpdate(self, data):
        pass

    def connect(self):
        pass

    def publish_cmd(self, *args, **kwargs):
        pass

broadcasterconf_imported = False

try:
    sys.path.append("/etc/yadtbroadcast-client/")
    import broadcasterconf
    sys.path.pop()
    broadcasterconf_imported = True
except Exception, e:
    logger.warn('no broadcaster config found')
    logger.warn(e)


def load_settings():

    os.umask(2)

    try:
        os.makedirs(OUT_DIR)
    except OSError, e:
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

    TARGET_SETTINGS_FILE = 'target'
    try:
        settings_file = open(TARGET_SETTINGS_FILE)
    except IOError:
        root_logger.critical('cannot find target definition file, aborting')
        sys.exit(1)
    global TARGET_SETTINGS
    TARGET_SETTINGS = yaml.load(settings_file)
    settings_file.close()

    TARGET_SETTINGS.setdefault('name', os.path.basename(os.getcwd()))

    global ybc
    if broadcasterconf_imported:
        ybc = broadcasterconf.create(TARGET_SETTINGS['name'])
    else:
        ybc = DummyBroadcaster()

    LOG_DIR = os.path.join(LOG_DIR_PREFIX, TODAY)
    try:
        os.makedirs(LOG_DIR)
    except OSError, e:
        if e.errno != 17:   # 17: file exists
            root_logger.critical('cannot write to log dir %s' % LOG_DIR)
            root_logger.exception(e)
            sys.exit(1)

    tag_args = sys.argv
    if os.path.basename(tag_args[0]) == 'yadtshell':
        tag_args = tag_args[1:]
    tag = '_'.join(tag_args)
    tag = tag.replace('://', '_')
    tag = tag.replace('/', '_')
    tag = tag.replace('-', '')
    tag = re.sub('[:\*\[\]]*', '', tag).lower()
    tag = re.sub('^_', '', tag)
    tag = re.sub('_$', '', tag)
    global log_file
    log_file = create_log_filename(
        LOG_DIR,
        TARGET_SETTINGS['name'],
        STARTED_ON,
        USER_INFO['user'],
        USER_INFO['yadt_host'].split('.')[0],
        tag=tag
    )

    ih = logging.FileHandler(log_file)
    ih.setLevel(logging.DEBUG)
    ih.setFormatter(sf)
    root_logger.addHandler(ih)

    logger.debug(yaml.dump(USER_INFO, default_flow_style=False))
    logger.debug(' '.join(sys.argv))
    logger.debug('\ncmd: %s %s' % (
        os.path.basename(sys.argv[0]).replace('.py', '').replace('components', '').replace('metalogic', '').lower(),
        ' '.join(sys.argv[1:])
    ))

    logger.debug('output dir is %s' % OUTPUT_DIR)

    he = hostexpand.HostExpander.HostExpander(outputformat=hostexpand.HostExpander.HostExpander.FQDN)
    TARGET_SETTINGS['original_hosts'] = TARGET_SETTINGS['hosts']
    TARGET_SETTINGS['hosts'] = he.expand(TARGET_SETTINGS['hosts'])

    CENTRAL_LOG_SITE = TARGET_SETTINGS.get('central_log_site')

    OUT_TARGET_FILE = os.path.join(OUT_DIR, TARGET_SETTINGS_FILE)
    try:
        changed = not filecmp.cmp(TARGET_SETTINGS_FILE, OUT_TARGET_FILE)
    except OSError:
        changed = True
    if changed:
        logger.info('target settings have changed since last call, thus cleaning cached data')
        shutil.rmtree(OUT_DIR)
        os.makedirs(OUT_DIR)
        shutil.copy2(TARGET_SETTINGS_FILE, OUT_TARGET_FILE)

    global VIEW_SETTINGS
    VIEW_SETTINGS = {'info-view': ['matrix', 'color', 'maxcols']}
    VIEW_SETTINGS_FILE = 'view'
    try:
        view_file = open(VIEW_SETTINGS_FILE)
        VIEW_SETTINGS = yaml.load(view_file)
        view_file.close()

    except:
        logger.debug('"view" file not found, falling back to default values: %s' %
                VIEW_SETTINGS)

    hosts_condensed_file = open(os.path.join(OUT_DIR, 'hosts_condensed'), 'w')
    print >> hosts_condensed_file, ', '.join(condense_hosts2(condense_hosts(TARGET_SETTINGS['hosts'])))
    hosts_condensed_file.close()

    def list_selected_hosts():
        return 'You are working now on %s\n\nas full list: %s\n' % (
            term.render('${BOLD}') + ', '.join(condense_hosts2(condense_hosts(TARGET_SETTINGS['hosts']))) + term.render('${NORMAL}'),
            ', '.join(TARGET_SETTINGS['hosts']),
        )

    pp = pprint.PrettyPrinter(indent=4)

    identity = TARGET_SETTINGS.get('identity')
    login = TARGET_SETTINGS.get('login')
    credentials = ''
    if identity:
        credentials += ' -i %(identity)s' % locals()
    if login:
        credentials += ' -l %(login)s' % locals()
    CONNECTIONS_DIR = os.path.join(OUTPUT_DIR, 'connections')
    #SSH_CONTROL_PATH = os.path.join(CONNECTIONS_DIR, '%r@%l_%h_%p')
    global SSH_CONTROL_PATH
    SSH_CONTROL_PATH = os.path.join(CONNECTIONS_DIR, '%h')
    try:
        os.makedirs(CONNECTIONS_DIR)
    except OSError:
        pass
    global SSH
    SSH = 'ssh -o ControlPath=%s -A %s -T -o ConnectTimeout=4 -o BatchMode=yes -o CheckHostIP=no -o StrictHostKeyChecking=no' % (SSH_CONTROL_PATH, credentials)

# TODO move constants to constants
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