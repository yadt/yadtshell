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

logger = logging.getLogger('restart')


def restart(protocol=None, uris=None, **opts):
    logger.info("restarting %s" % uris)
    logger.info("opts: %s" % opts)

    components = yadtshell.util.restore_current_state()

    service_uris = yadtshell.helper.expand_hosts(uris)
    service_uris = yadtshell.helper.glob_hosts(components, service_uris)

    logging.info("service uris: %s" % service_uris)

    stop_plan = yadtshell.metalogic.metalogic(
        yadtshell.settings.STOP,
        uris,
        plan_post_handler=yadtshell.metalogic.identity)

    orig_state = {}
    for action in stop_plan.actions:
        orig_state[action.uri] = components[action.uri].state

    logging.info("current states: %s" % orig_state)

    for line in stop_plan.dump(include_preconditions=True).splitlines():
        logging.info(line)

    logging.info("restarting NOW")
    start_uris = [uri for uri, state in orig_state.iteritems()
                  if state == "up"]
    logging.info("starting %s" % start_uris)
    start_plan = yadtshell.metalogic.metalogic(
        yadtshell.settings.START,
        start_uris,
        plan_post_handler=yadtshell.metalogic.identity)

    for line in start_plan.dump(include_preconditions=True).splitlines():
        logging.info(line)

    logger.critical("Not Yet Implemented")
    raise Exception("Not Yet Implemented")
