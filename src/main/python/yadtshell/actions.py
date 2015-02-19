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

    def __eq__(self, other):
        return (
            isinstance(other, TargetState) and
            self.uri == other.uri and
            self.attr == other.attr and
            self.target_value == other.target_value
        )

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
        self.args = args if args else []
        self.kwargs = kwargs if kwargs else {}
        self.rank = self.uri

    def are_all_preconditions_met(self, components):
        for precondition in self.preconditions:
            if not precondition.is_reached(components):
                return False
        return True

    def __str__(self):
        return self.dump(include_preconditions=False)

    def __eq__(self, other):
        preconditions_match = reduce(lambda a, b: a and b,
                                     # we use the list __contains__ for value equality
                                     [own_precondition in list(getattr(other, "preconditions", []))
                                      for own_precondition in self.preconditions],
                                     True)
        return (
            isinstance(other, Action) and
            self.cmd == other.cmd and
            self.uri == other.uri and
            self.attr == other.attr and
            self.target_value == other.target_value and
            self.kwargs == other.kwargs and
            self.executed == other.executed and
            len(self.preconditions) == len(other.preconditions) and
            preconditions_match
        )

    def dump(self, depth=0, include_preconditions=True, include_target_value=True):
        indent = ' ' * depth * 4
        text = indent
        text += '%(cmd)s the %(uri)s' % vars(self)
        if include_target_value:
            if self.attr and self.target_value:
                text += ', set %(attr)s to "%(target_value)s"' % vars(self)
        aux_text = [key for key, value in self.kwargs.iteritems() if value]
        if aux_text:
            text += " (%s)" % " ".join(aux_text)
        if include_preconditions:
            text += '\n'
            for precondition in self.preconditions:
                text += precondition.dump(depth + 1, 'when ')
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

    @property
    def list_actions(self):
        for plan_or_action in self.actions:
            if isinstance(plan_or_action, ActionPlan):
                for a in plan_or_action.list_actions:
                    yield a
            else:
                yield plan_or_action

    @property
    def is_empty(self):
        return len(self.actions) == 0

    @property
    def is_not_empty(self):
        return not self.is_empty
