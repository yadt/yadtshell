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
from yadtshell.update import get_all_adjacent_needed_hosts
from yadtshell.metalogic import (metalogic,
                                 identity,
                                 apply_instructions,
                                 chop_minimal_related_chunks)
from yadtshell.constants import REBOOT_REQUIRED
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

        hosts_to_reboot = uris
        stop_plan = create_plan_to_stop_all_services_on(hosts_to_reboot)

        all_stopped_services = set()
        for action in stop_plan.actions:
            all_stopped_services.add(action.uri)

        start_plan = create_plan_to_start_services_after_rebooting(all_stopped_services,
                                                                   hosts_to_reboot,
                                                                   components)

        reboot_actions = set([create_reboot_action_for(components[host_uri]) for host_uri in hosts_to_reboot])

        all_actions = set(start_plan.actions) | set(
            stop_plan.actions) | reboot_actions
        all_plan = ActionPlan('all', all_actions)
        all_plan = chop_minimal_related_chunks(all_plan)

        reboot_chunks = set()
        for chunk in all_plan.actions:
            all_chunk_cmds = set(a.cmd for a in chunk.actions)
            if yadtshell.settings.UPDATE in all_chunk_cmds:
                reboot_chunks.add(chunk)
                continue

        prestart_chunks = set()
        for possible_prestart_chunk in all_plan.actions:
            if possible_prestart_chunk in reboot_chunks:
                continue
            if possible_prestart_chunk.is_not_empty:
                prestart_chunks.add(possible_prestart_chunk)

        plan = ActionPlan(
            'update', [ActionPlan('prestart', prestart_chunks),
                       ActionPlan('stoprebootstart', reboot_chunks)
                       ], nr_workers=1)
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


def create_plan_to_stop_all_services_on(host_uris):
    return metalogic(
        yadtshell.settings.STOP,
        host_uris,
        plan_post_handler=identity)


def create_plan_to_start_services_after_rebooting(services, rebooted_hosts, components):
    start_plan = metalogic(
        yadtshell.settings.START,
        services,
        plan_post_handler=identity)

    for start_action in start_plan.actions:
        if start_action.uri in services:
            for host_uri in get_all_adjacent_needed_hosts(start_action.uri, components):
                if host_uri in rebooted_hosts:
                    start_action.preconditions.add(yadtshell.actions.TargetState(
                        host_uri, 'state', 'rebooted'))

    return start_plan
