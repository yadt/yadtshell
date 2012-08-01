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
services:
- frontend-service:
    needs_services: [backend-service]
    state: 0
    service_artefact: yit-frontend-service
    toplevel_artefacts: [yit-config-$host]
- backend-service:
    state: 0
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

def output (host):
    
    placeholders = {
        'date': datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y"), 
        'host': host[0:host.index('.')], 
        'host_fqdn': host, 
        'timestamp': int(time.time())}
    
    return STATUS_TEMPLATE.substitute(placeholders)
