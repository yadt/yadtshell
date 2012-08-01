#! /usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import logging
import re

import util

logger = logging.getLogger('dump')

def dump(args = [], mode='all', attribute=None, filter=None, **kwargs):
    if filter == 'pending-updates':
        args = ['host://']
        attribute = 'next_artefacts'
    if filter == 'current-artefacts':
        args = ['host://']
        attribute = 'handled_artefacts'
    components = util.restore_current_state()
    result = set()
    for uri in components.keys():
        if len(args) > 0:
            all_matched = reduce(
                lambda result, arg: result & (re.search(arg, uri) is not None), 
                args, 
                True
            )
            if not all_matched:
                continue
        component = components[uri]
        if attribute:
            a = getattr(component, attribute, None)
            if not a:
                continue
            if isinstance(a, list):
                result = result.union(a)
            else:
                result.add(a)
        else:
            if uri != component.uri:
                print uri, '- also known as'
            print component.dump()
    if attribute:
        print '\n'.join(result)

