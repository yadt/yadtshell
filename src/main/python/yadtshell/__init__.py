from __future__ import absolute_import

import yadtshell.settings
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

