#!/usr/bin/python
import logging
import subprocess
import sys
import datetime

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

