# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2013  Immobilien Scout GmbH
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


logger = logging.getLogger('update')


def compare_versions(protocol=None, hosts=None, update_plan_post_handler=None, parallel=None, **kwargs):
    components = yadtshell.util.restore_current_state()
    if not update_plan_post_handler:
        update_plan_post_handler = yadtshell.metalogic.chop_minimal_related_chunks

    all_hosts = set([c for c in components.values() if isinstance(c, yadtshell.components.Host)])

    if hosts:
        handled_hosts = yadtshell.helper.expand_hosts(hosts)
        handled_hosts = yadtshell.helper.glob_hosts(components, handled_hosts)
        logger.debug('User requested update for ' + ', '.join(handled_hosts))
    else:
        handled_hosts = [h.uri for h in all_hosts]
        logger.debug('User requested update for all hosts.')

    # create the base rules for starting all services
    all_services = set([s.uri for s in components.values() if isinstance(s, yadtshell.components.Service)])

    start_plan = yadtshell.metalogic.metalogic(yadtshell.settings.START, all_services, plan_post_handler=yadtshell.metalogic.identity)

    hosts_with_update = set([h for h in all_hosts if h.state == yadtshell.settings.UPDATE_NEEDED])
    if hosts_with_update:
        logger.debug('New artefacts found for %s' % ', '.join(h.uri for h in hosts_with_update))

        hosts_with_update = set([h for h in hosts_with_update if h.uri in handled_hosts])
        logger.debug('Handling hosts with new artefacts: %s' % ', '.join(h.uri for h in hosts_with_update))
    else:
        logger.info('No hosts with pending updates.')

    next_artefacts = set([artefact.uri
                         for artefact in components.values()
                         if artefact.type == yadtshell.settings.ARTEFACT
                         and artefact.revision == yadtshell.settings.NEXT
                         and artefact.host_uri in handled_hosts
                          ])

    if yadtshell.settings.reboot_enabled:
        hosts_with_reboot = set([h for h in all_hosts if h.reboot_required and h.uri in handled_hosts])
    else:
        hosts_with_reboot = set()

    host_uris_with_reboot = set([h.uri for h in hosts_with_reboot])

    current_artefacts = [components.get(yadtshell.uri.change_version(next_artefact, 'current'))
                         for next_artefact in next_artefacts]
    current_artefacts = set([current.uri for current in current_artefacts if current])

    logger.debug('next_artefacts: ' + ', '.join(next_artefacts))
    logger.debug('current_artefacts: ' + ', '.join(current_artefacts))

    diff = next_artefacts | current_artefacts | host_uris_with_reboot
    logger.debug('diff: ' + ', '.join(diff))

    if not diff:
        yadtshell.util.dump_action_plan('update', start_plan)
        return 'update'

    stop_plan = yadtshell.metalogic.metalogic(yadtshell.settings.STOP, diff, plan_post_handler=yadtshell.metalogic.identity)
    stopped_services = set()
    for action in stop_plan.actions:
        stopped_services.add(action.uri)

    for action in start_plan.actions:
        if action.uri in stopped_services:
            host_uri = components[action.uri].host_uri
            action.preconditions.add(yadtshell.actions.TargetState(host_uri, 'state', yadtshell.settings.UPTODATE))

    update_actions = set()
    for host in hosts_with_reboot | hosts_with_update:
        action = yadtshell.actions.Action(yadtshell.settings.UPDATE, host.uri, 'state', yadtshell.settings.UPTODATE)
        for needs_host in [components.get(s) for s in stopped_services]:
            if needs_host.host_uri != host.uri:
                continue
            action.preconditions.add(yadtshell.actions.TargetState(needs_host, 'state', yadtshell.settings.DOWN))
        update_actions.add(action)
    for ua in update_actions:
        if ua.uri in host_uris_with_reboot:
            ua.kwargs[yadtshell.constants.REBOOT_REQUIRED] = True

    all_actions = set(start_plan.actions) | set(stop_plan.actions) | update_actions
    all_plan = yadtshell.actions.ActionPlan('all', all_actions)
    all_plan = yadtshell.metalogic.chop_minimal_related_chunks(all_plan)

    update_chunks = set()
    for chunk in all_plan.actions:
        all_chunk_cmds = set(a.cmd for a in chunk.actions)
        if yadtshell.settings.UPDATE in all_chunk_cmds:
            update_chunks.add(chunk)
            continue

    prestart_chunks = set()
    for chunk in all_plan.actions:
        if chunk in update_chunks:
            continue
        prestart_chunks.add(chunk)

    plan = yadtshell.actions.ActionPlan('update', [yadtshell.actions.ActionPlan('prestart', prestart_chunks), yadtshell.actions.ActionPlan('stopupdatestart', update_chunks)], nr_workers=1)
    plan = yadtshell.metalogic.apply_instructions(plan, parallel)
    yadtshell.util.dump_action_plan('update', plan)
    return 'update'
