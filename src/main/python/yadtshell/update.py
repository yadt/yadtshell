#! /usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
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
        logger.info('handling ' + ', '.join(handled_hosts))
    else:
        handled_hosts = [h.uri for h in all_hosts]
        logger.info('updating all hosts')

    # create the base rules for starting all services
    all_services = set([s.uri for s in components.values() if isinstance(s, yadtshell.components.Service)])

    start_plan = yadtshell.metalogic.metalogic(yadtshell.settings.START, all_services, plan_post_handler=yadtshell.metalogic.identity)
#    for action in start_plan.actions:
#        host_uri = components[action.uri].host_uri
#        action.preconditions.add(yadtshell.actions.TargetState(host_uri, 'state', yadtshell.settings.UPTODATE))
    
    hosts_with_update = [h for h in all_hosts if h.state == yadtshell.settings.UPDATE_NEEDED]
    logger.info('new artefacts found for %s' % ', '.join(h.uri for h in hosts_with_update))
    hosts_with_update = [h for h in hosts_with_update if h.uri in handled_hosts]
    logger.info('handling hosts with new artefacts: %s' % ', '.join(h.uri for h in hosts_with_update))

    next_artefacts = set([artefact.uri
        for artefact in components.values()
            if artefact.type == yadtshell.settings.ARTEFACT
                and artefact.revision == yadtshell.settings.NEXT
                and artefact.host_uri in handled_hosts
    ])
    
    if not next_artefacts:
        yadtshell.util.dump_action_plan('update', start_plan)
        return 'update'
    
    current_artefacts = [components.get(yadtshell.uri.change_version(next_artefact, 'current'))
        for next_artefact in next_artefacts
    ]
    current_artefacts = set([current.uri for current in current_artefacts if current])

    logger.debug('next_artefacts: ' + ', '.join(next_artefacts))
    logger.debug('current_artefacts: ' + ', '.join(current_artefacts))

    diff = next_artefacts | current_artefacts
    logger.info('diff: ' + ', '.join(diff))

    if not diff:
        yadtshell.util.dump_action_plan('update', start_plan)
        return 'update'


    stop_plan = yadtshell.metalogic.metalogic(yadtshell.settings.STOP, diff, plan_post_handler=yadtshell.metalogic.identity)
    stopped_services = set()
    for action in stop_plan.actions:
        stopped_services.add(action.uri)
        #host_uri = components[action.uri].host_uri
        #action.preconditions.add(yadtshell.actions.TargetState(host_uri, 'state', yadtshell.settings.UPDATE_NEEDED))
    
    for action in start_plan.actions:
        if action.uri in stopped_services:
            host_uri = components[action.uri].host_uri
            action.preconditions.add(yadtshell.actions.TargetState(host_uri, 'state', yadtshell.settings.UPTODATE))

    update_actions = set()
    for host in hosts_with_update:
        action = yadtshell.actions.Action(yadtshell.settings.UPDATE, host.uri, 'state', yadtshell.settings.UPTODATE)
        #for needs_host in [s for s in host.needed_by if s.startswith('service://')]:
        for needs_host in [components.get(s) for s in stopped_services]:
            if needs_host.host_uri != host.uri:
                continue
            action.preconditions.add(yadtshell.actions.TargetState(needs_host, 'state', yadtshell.settings.DOWN))
        update_actions.add(action)

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

