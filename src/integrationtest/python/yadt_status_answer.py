#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2012  Immobilien Scout GmbH
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

__author__ = 'Alexander Metzner, Michael Gruber'


import datetime
import string
import time


STATUS_TEMPLATE = string.Template("""
hostname: "$host"
fqdn: "$host_fqdn"
uptime: " 10:02:31 up 156 days, 4:57, 0 users, load average: 0.38, 0.12, 0.09"
date: "$date"
epoch: $timestamp
ip: "127.0.0.1"
interface:
  lo0: 127.0.0.1
pwd: /home/yadt-integration-test-user
age_of_cached_structure: 1
defaults:
  YADT_EXITCODE_HOST_LOCKED: 150
  YADT_EXITCODE_SERVICE_IGNORED: 151
  YADT_LOCK_DIR: /var/lock/yadt

services:
- frontend-service:
    needs_services: [backend-service]
    state: $frontend_service_state
    service_artefact: yit-frontend-service
    toplevel_artefacts: [yit-config-$host]
- backend-service:
    state: $backend_service_state
    service_artefact: yit-backend-service
    toplevel_artefacts: [yit-config-$host]
artefact_names_handled_by_yadt:
- yit-frontend-service
- yit-backend-service
- yit-config-$host
current_artefacts:
- yit-frontend-service/0:0.0.1-1
- yit-backend-service/0:0.0.1-1
- yit-config-$host/0:0.0.1-1
handled_artefacts:
- yit-frontend-service/0:0.0.1-1
- yit-backend-service/0:0.0.1-1
- yit-config-$host/0:0.0.1-1
age_of_cached_artefacts: 1
next_artefacts:
- yit-config-$host/0:0.0.1-2
artefacts_query_epoch: $timestamp
state: uptodate
query_time: 1
""")


def stdout (host, frontend_service_state=0, backend_service_state=0):
    date = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")
    
    placeholders = {
        'backend_service_state'  : backend_service_state,
        'date'                   : date,
        'frontend_service_state' : frontend_service_state,
        'host'                   : host[0:host.index('.')], 
        'host_fqdn'              : host, 
        'timestamp'              : int(time.time())}
    
    return STATUS_TEMPLATE.substitute(placeholders)
