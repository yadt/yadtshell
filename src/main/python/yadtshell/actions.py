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

class ActionException(Exception):
    def __init__(self, message, exitcode, rootcause=None):
        self.message = message
        self.exitcode = exitcode
        self.rootcause = rootcause
        self.args = [message]
        self.orig_protocol = None

class TargetState(object):
    def __init__(self, uri, attr, target_value):
        self.uri = uri
        self.attr = attr
        self.target_value = target_value

    def is_reached(self, components):
        return getattr(components[self.uri], self.attr, None) == self.target_value

    def __str__(self):
        return self.dump(0)

    def dump(self, depth, prefix=''):
        indent = ' ' * depth * 4
        return indent + prefix + '%(attr)s of %(uri)s is "%(target_value)s"\n' % vars(self)

class State(object):
    PENDING, RUNNING, FINISHED = ['PENDING', 'RUNNING', 'FINISHED']

class Action(object):
    def __init__(self, cmd, uri, attr=None, target_value=None, preconditions=None, args=None, kwargs=None):
        self.cmd = cmd
        self.uri = uri
        self.attr = attr
        self.target_value = target_value
        if preconditions:
            self.preconditions = preconditions
        else:
            self.preconditions = set()
        self.executed = False
        self.name = '%s %s' % (cmd, uri)
        self.state = State.PENDING
        self.args = args
        self.kwargs = kwargs
        self.rank = self.uri
        
    def are_all_preconditions_met(self, components):
        for precondition in self.preconditions:
            if not precondition.is_reached(components):
                return False
        return True

    def __str__(self):
        return self.dump(include_preconditions=False)

    def dump(self, depth=0, include_preconditions=True):
        indent = ' ' * depth * 4
        text = indent
        text += '%(cmd)s the %(uri)s' % vars(self)
        if self.attr and self.target_value:
            text += ', set %(attr)s to "%(target_value)s"' % vars(self)
        text += '\n'
        if include_preconditions:
            if self.args:
                text += indent + '    args: ' + ', '.join(self.args) + '\n'
            if self.kwargs:
                text += indent + '    kwargs: ' + ', '.join(['%s: %s' % (key, value) for key, value in self.kwargs.iteritems()]) + '\n'
            for precondition in self.preconditions:
                text += precondition.dump(depth + 1, 'when ')
            #text += '\n'
        return text

    def mark_executed(self):
        self.executed = True

    def is_executed(self):
        return getattr(self, 'executed', False)

    def __lt__(self, other):
        return self.rank < other.rank

class ActionPlan(object):
    def __init__(self, name, actions, nr_workers=None, nr_errors_tolerated=0):
        self.name = name
        if isinstance(actions, list):
            self.actions = actions
        else:
            self.actions = tuple(sorted(actions))
        if self.actions:
            self.rank = self.actions[0].rank  
        else:
            # TODO: yes, plans without actions feel and fail miserably
            self.rank = -1
        self.nr_workers = nr_workers
        self.nr_errors_tolerated = nr_errors_tolerated
        
    def __str__(self):
        return self.dump(include_preconditions=False)

    def meta_info(self):
        if self.nr_workers:
            if self.nr_workers == 1:
                workers_str = ', sequential'
            else:
                workers_str = ', %s workers' % str(self.nr_workers)
        else:
            workers_str = ', workers *undefined*'
        return '%i items%s, %s errors tolerated' % (len(self.actions), workers_str, str(self.nr_errors_tolerated))
        
    def dump(self, depth=0, include_preconditions=True):
        indent = ' ' * depth * 4
        text = '%s%s [%s]:\n' % (indent, self.name, self.meta_info())
        for action in self.actions:
            text += action.dump(depth + 1, include_preconditions)
        return text
    
    def __lt__(self, other):
        return self.rank < other.rank

    def search(self, name):
        name = name.lstrip('/')
        if self.name == name:
            return self
        if '/' in name:
            name, rest = name.split('/', 1)
            for action in self.actions:
                if action.name == name:
                    return action.search(rest)
        return None
    
    def list_subplans(self):
        yield (self.name, self)
        for plan in [p for p in self.actions if isinstance(p, ActionPlan)]:
            for sp in plan.list_subplans():
                yield ('%s/%s' % (self.name, sp[0]), sp[1])
                
