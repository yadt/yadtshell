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

from __future__ import absolute_import

import yadtshell.settings
import yadtshell.components
import yadtshell.constants
import yadtshell.util
import yadtshell.metalogic
import yadtshell.helper
import yadtshell.update
import yadtshell.uri
from yadtshell.actionmanager import ActionManager

import yadtshell.twisted
import yadtshell.defer

from yadtshell.status import status
from yadtshell.info import info
from yadtshell.dump import dump


VERSION = '${version}'


def decode1364(encoded_string):
    return encoded_string.decode('rot13').decode('base64')


def initialize_logging():
    pass
