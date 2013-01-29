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

