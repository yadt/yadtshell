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

"""
	This module contains all function used by the command line interface.
"""

import logging
import yadtshell
import sys

COMMANDS_WHICH_REQUIRE_AT_LEAST_ONE_COMPONENT_URI = ['start', 'stop', 'ignore', 'unignore', 'lock', 'unlock', 'updateartefact']
EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT = 1

LOGGER = logging.getLogger()


def ensure_command_has_required_arguments(command, arguments, show_help_callback):
    if command in COMMANDS_WHICH_REQUIRE_AT_LEAST_ONE_COMPONENT_URI and not arguments:
        LOGGER.warning('Command "{0}" requirest at least one component uri!'.format(command))
        show_help_callback()
        sys.exit(EXIT_CODE_MISSING_COMPONENT_URI_ARGUMENT)
