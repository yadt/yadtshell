#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import logging
import yaml
import fnmatch

import yadtshell

logger = logging.getLogger('metalogic')

def run_along_services2(components, services, indent = 0, key = 'needed_by'):
    result = {} 
    for service_uri in services:
        service = components[service_uri]
        if service.type not in [yadtshell.settings.HOST, yadtshell.settings.SERVICE]:
            continue
        dependent = run_along_services2(
            components,
            getattr(service, key, []),
            indent + 1,
            key
        )
        if dependent:
            result[service] = dependent
        else:
            result[service] = None
    return result

def depth_first(d, indent = 0, handled = None):
    if d is None:
        return
    if handled is None:
        handled = set()
    for key in d.keys():
        for y in depth_first(d[key], indent + 1):
            yield(y)
    for key in d.keys():
        yield(key, indent)

def depth_first_per_toplevel(d, indent = 0, handled = None):
    if handled is None:
        handled = set()
    for toplevel in d.keys():
        for (k, i) in depth_first(d[toplevel], indent + 1, handled):
            if k not in handled:
                handled.add(k)
                yield(k, i)
        if toplevel not in handled:
            yield(toplevel, indent)
        yield(None, -1)

def collect_parallel_tasks(g):
    last_indent = -2
    pt = set()
    for (key, indent) in g:
        if (indent < 0):
            continue
        if last_indent != indent or last_indent == -1:
            if last_indent >= 0:
                yield(pt, last_indent)
            last_indent = indent
            pt.clear()
        pt.add(key)
        if last_indent == -2:
            last_indent = indent
    yield(pt, last_indent)


def metalogic(cmd, args, plan_post_handler=None):
    components = yadtshell.util.restore_current_state()
    if not plan_post_handler:
        plan_post_handler = chop_minimal_related_chunks

    if cmd is None:
        cmd = args[0]
        args = args[1:]
    if not args:
        args = ''

    KEYS = {
        yadtshell.settings.STOP: ('needed_by', 'needs', yadtshell.settings.DOWN),
        yadtshell.settings.START: ('needs', 'needed_by', yadtshell.settings.UP),
    }
    key, _, target_state = KEYS.get(cmd, ('needs', 'needed_by', None))

    touched_uris = yadtshell.helper.expand_hosts(args)
    touched_uris = yadtshell.helper.glob_hosts(components, touched_uris)

    touched_components = yadtshell.components.ComponentSet(components)
    for touched_uri in touched_uris:
        touched_components.add(touched_uri, True)
    for c in touched_components:
        logger.debug('touched component: %s' % c.uri)

    logger.debug('search recursivly for dependent components')
    new_components = True
    while new_components:
        new_components = set()
        for component in touched_components:
            logger.debug('  processing %s' % component.uri)
            for dependent_uri in getattr(component, key, []):
                dependent = components[dependent_uri]
                logger.debug('    checking %s' % dependent.uri)
                if dependent in touched_components:
                    logger.debug('    already found: %s' % dependent_uri)
                    continue
                if dependent.is_touched_also(component):
                    new_components.add(dependent)
        touched_components.update(new_components)
        logger.debug('    new found: %s' % ', '.join(map(str, new_components)))

    for component in touched_components:
        logger.debug('touched component: %s' % component.uri)

    for component in touched_components:
        if isinstance(component, yadtshell.components.MissingComponent):
            logger.error('unknown component %(uri)s' % vars(component))

    action_set = set()
    for touched_component in touched_components:
        if not hasattr(touched_component, cmd):
            continue
        action = yadtshell.actions.Action(cmd, touched_component.uri, 'state', target_state)
        action.preconditions = set([
                yadtshell.actions.TargetState(d, 'state', target_state) 
                for d in getattr(touched_component, key, set())
                if yadtshell.uri.parse(d)['type'] == yadtshell.settings.SERVICE
            ])
        action_set.add(action)

    dependencies = yadtshell.actions.ActionPlan('%s' % cmd, action_set)
    return plan_post_handler(dependencies)


def merge_chunks(component_to_chunk, old, new):
    if old == new:
        return
    logger.debug('    merging chunk %(old)s with chunk %(new)s' % locals())
    for uri, old_chunk_nr in component_to_chunk.iteritems():
        if old_chunk_nr == old:
            component_to_chunk[uri] = new


def identity(x):
    return x

def chop_minimal_related_chunks(plan):
    component_to_chunk = {}
    for nr, action in enumerate(plan.actions):
        cmd = action.cmd
        uri = action.uri
        logger.debug('uri found: %s' % uri)
        if uri not in component_to_chunk:
            component_to_chunk[uri] = nr + 1
    logger.debug(yaml.dump(component_to_chunk))

    for action in plan.actions:
        cmd = action.cmd
        uri = action.uri
        chunk_nr = component_to_chunk.get(uri, None)
        logger.debug('uri: %(uri)s, chunk: %(chunk_nr)s' % locals())
        preconds = action.preconditions
        for precond in preconds:
            puri = precond.uri
            if puri in component_to_chunk:
                chunk_nr = min(component_to_chunk[puri], chunk_nr)
                logger.debug('    chunk member found: %(puri)s' % locals())
        logger.debug('    new chunk nr: %s' % chunk_nr)
        merge_chunks(component_to_chunk, component_to_chunk[uri], chunk_nr)
        for precond in preconds:
            puri = precond.uri
            precond_chunk_nr = component_to_chunk.get(puri)
            if not precond_chunk_nr:
                logger.debug('        interesting, %s not in plan, assuming up' % puri)
                continue
            logger.debug('    precond: %(puri)s %(precond_chunk_nr)s' % locals())
            merge_chunks(component_to_chunk, precond_chunk_nr, chunk_nr)

    chunk_plans = set()
    for nr, chunk_nr in enumerate(set(component_to_chunk.values())):
        logger.debug('collecting components in chunk %s' % chunk_nr)
        chunk_actions = set()
        for action in plan.actions:
            if component_to_chunk[action.uri] == chunk_nr:
                chunk_actions.add(action)
        chunk_plan = yadtshell.actions.ActionPlan('chunk_%s' % nr, chunk_actions)
        chunk_plans.add(chunk_plan)
    if (len(chunk_plans) > 1):
        logger.info('%i independent chunks found' % len(chunk_plans))

    return yadtshell.actions.ActionPlan(plan.name, chunk_plans)




def apply_instructions(plan, instructions):
    logger = logging.getLogger('apply_instructions')
    logger.debug('-' * 20 + ' original plan ' + '-' * 20)
    for line in str(plan).splitlines():
        logger.debug(line)
    logger.debug('-' * 60)
    if not instructions:
        instructions = 1

    subplans_ordered = []
    subplans = {}
    for sp in plan.list_subplans():
        subplans[sp[0]] = sp[1]
        subplans_ordered.append(sp[0])

    try:
        instructions = int(instructions)
        for sp in subplans.values():
            if not sp.nr_workers:
                sp.nr_workers = instructions
        #print plan
        return plan
    except:
        pass

    for instruction in instructions.split():
        name_re, parts = instruction.split('=')
        results = fnmatch.filter(subplans.keys(), name_re)
        for name, p in [(name, subplans.get(name)) for name in subplans_ordered if name in results]:
            if p.nr_workers:
                logger.debug('skipping %s due to already defined nr_workers' % name)
                continue
            chunks = []
            start = 0
            end = 0
            for part in parts.split(':'):
                nr_chunks, nr_workers, nr_errors_tolerated = part.split('_')
                logger.info('augmenting %s: %s = %s chunks, %s workers, %s errors tolerated' % (name, name_re, nr_chunks, nr_workers, nr_errors_tolerated))
                if nr_chunks == '*':
                    nr_chunks = len(p.actions) - start
                nr_chunks = int(nr_chunks)
                if not nr_chunks:
                    continue
                end = min(start + nr_chunks, len(p.actions))
                acs = p.actions[start:end]
                if not acs:
                    break
                if nr_workers in ['*', 'max']:
                    nr_workers = len(acs)
                nr_workers = int(nr_workers)
                
                if nr_errors_tolerated.endswith('%'):
                    nr_errors_tolerated = int(len(acs) * int(nr_errors_tolerated.rstrip('%')) / 100)
                    
                chunks.append(yadtshell.actions.ActionPlan('%s_applied_%i' % (p.name, len(chunks)), acs, nr_workers=nr_workers, nr_errors_tolerated=nr_errors_tolerated))
                start = end
            p.actions = chunks
            p.nr_workers = 1
    logger.debug('-' * 20 + ' augmented plan ' + '-' * 20)
    for line in str(plan).splitlines():
        logger.debug(line)
    logger.debug('-' * 60)
    return plan
    
