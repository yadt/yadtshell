#!/usr/bin/python
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

import logging
import subprocess

import yadtshell

yadtshell.settings.ch.setLevel(logging.WARN)

logger = logging.getLogger('sync_logs')

name = yadtshell.settings.TARGET_SETTINGS['name']
hosts = yadtshell.settings.TARGET_SETTINGS['hosts']
log_dir = yadtshell.settings.LOG_DIR_PREFIX

logger.info('syncing/cleaning target %s' % name)
logger.info('local log dir: %s' % log_dir)

def log_output(output, logger):
    for line in output.splitlines():
        if line:
            logger.info(line)

SSH_CALL = ['ssh', '-o BatchMode=yes', '-o CheckHostIP=no', '-o StrictHostKeyChecking=no']

for host in hosts:
    host_logger = logging.getLogger('sync_logs.%s' % host.split('.')[0])
    host_logger.info('starting sync/cleanup')

    host_log_dir_call = subprocess.Popen(
        SSH_CALL + [host, 'sed -n "/YADT_LOG/{s/^.*=//;p}" /etc/default/yadt'],
        stdout=subprocess.PIPE)
    host_log_dir = host_log_dir_call.communicate()[0].strip()
    host_logger.info('host log dir: %s' % host_log_dir)
    rsync_call = subprocess.Popen(
        [
            'rsync',
            '-e', ' '.join(SSH_CALL),
            '-avO', '--no-p',
            '%s:%s/' % (host, host_log_dir), log_dir
        ],
        stdout=subprocess.PIPE)
    log_output(rsync_call.communicate()[0], host_logger)

    host_logger.info('--------')

logger.info('done')

