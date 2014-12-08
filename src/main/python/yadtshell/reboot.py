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

import logging
import yadtshell

from yadtshell.actions import ActionPlan, Action, TargetState
from yadtshell.helper import expand_hosts, glob_hosts
from yadtshell.metalogic import (metalogic,
                                 identity,
                                 apply_instructions,
                                 chop_minimal_related_chunks)
from yadtshell.constants import REBOOT_REQUIRED
from yadtshell.components import Service
from yadtshell.settings import DOWN
from yadtshell.util import restore_current_state, dump_action_plan

logger = logging.getLogger('reboot')


def reboot(protocol=None, uris=None, parallel=None, **kwargs):
    try:
        for uri in uris:
            if not uri.startswith("host://"):
                message = "Cannot reboot %s" % uri
                logger.error(message)
                raise ValueError(message)

        components = restore_current_state()
        host_uris = expand_hosts(uris)
        host_uris = glob_hosts(components, host_uris)

        start_actions = []
        stop_actions = []
        reboot_actions = []
        for host_uri in host_uris:
            host = components[host_uri]
            reboot_host = create_reboot_action_for(host)

            stop_all_services_on_host = create_plan_to_stop_all_services_on(host_uri)

            start_after_reboot = create_plan_to_start_all_services_on(host_uri, components)
            stop_actions.extend(stop_all_services_on_host.actions)
            reboot_actions.append(reboot_host)
            start_actions.extend(start_after_reboot.actions)

        all_actions = set(start_actions) | set(stop_actions) | set(reboot_actions)
        all_plan = yadtshell.actions.ActionPlan('all', all_actions)
        all_plan = chop_minimal_related_chunks(all_plan)

        reboot_chunks = set()
        for chunk in all_plan.actions:
            all_chunk_cmds = set(a.cmd for a in chunk.actions)
            if yadtshell.settings.UPDATE in all_chunk_cmds:
                reboot_chunks.add(chunk)
                continue

        plan = ActionPlan('reboot', reboot_chunks)

        plan = apply_instructions(plan, parallel)

        dump_action_plan('reboot', plan)
        return 'reboot'
    except BaseException as e:
        logger.error("Problem white creating plan for reboot: %s" % e)
        import traceback
        logger.debug(traceback.format_exc(e))
        raise


def create_reboot_action_for(host):
    reboot_host_action = Action('update', host.host_uri, 'state', 'rebooted')
    reboot_host_action.kwargs['upgrade_packages'] = False
    reboot_host_action.kwargs[REBOOT_REQUIRED] = True
    for service in host.defined_services:
        reboot_host_action.preconditions.add(
            TargetState(service.uri, 'state', DOWN))

    return reboot_host_action


def create_plan_to_stop_all_services_on(host_uri):
    return yadtshell.metalogic.metalogic(
        yadtshell.settings.STOP,
        [host_uri],
        plan_post_handler=identity)


def create_plan_to_start_all_services_on(host_uri, components):
    all_services_on_host = set(
        [s.uri for s in components.values()
         if isinstance(s, Service) and s.host_uri == host_uri])

    start_after_reboot = metalogic(
        yadtshell.settings.START,
        all_services_on_host,
        plan_post_handler=identity)
    for start_action in start_after_reboot.actions:
        start_action.preconditions.add(
            TargetState(host_uri, 'state', 'rebooted'))

    return start_after_reboot
