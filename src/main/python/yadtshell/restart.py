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

from yadtshell.actions import ActionPlan
from yadtshell.helper import expand_hosts, glob_hosts
from yadtshell.metalogic import metalogic, identity, apply_instructions, chop_minimal_related_chunks
from yadtshell.settings import STOP, START, UP
from yadtshell.util import restore_current_state, dump_action_plan, log_exceptions

logger = logging.getLogger('restart')


@log_exceptions(logger)
def restart(protocol=None, uris=None, parallel=None, **kwargs):
    logger.debug("uris: %s" % uris)
    logger.debug("parallel: %s" % parallel)
    logger.debug("kwargs: %s" % kwargs)

    components = restore_current_state()
    service_uris = expand_hosts(uris)
    service_uris = glob_hosts(components, service_uris)

    logging.debug("service uris: %s" % service_uris)

    plan_all = []
    stop_plan = metalogic(STOP, uris, plan_post_handler=identity)
    stop_plan = chop_minimal_related_chunks(stop_plan)
    for chunk in stop_plan.actions:
        stops = ActionPlan("stop", chunk.actions)

        service_states = {}
        for action in chunk.actions:
            service_states[action.uri] = components[action.uri].state
        logging.debug("current states: %s" % service_states)

        start_uris = [uri for uri, state in service_states.iteritems()
                      if state == UP]
        start_uris = set(start_uris)
        logging.info("restarting %s" % ", ".join(start_uris))
        starts = metalogic(START, start_uris, plan_post_handler=identity)

        plan_all.append(ActionPlan("chunk", [stops, starts], nr_workers=1))

    plan = ActionPlan('restart', plan_all)

    for line in plan.dump(include_preconditions=True).splitlines():
        logging.info(line)

    plan = apply_instructions(plan, parallel)
    dump_action_plan('restart', plan)
    return 'restart'
