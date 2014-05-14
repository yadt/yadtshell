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

import socket
import yadtshell


def broadcast_yadtshell_call_information():
    yadtshell.settings.ybc._sendEvent(
        'call-info', data=None,
        tracking_id=yadtshell.settings.tracking_id,
        target=yadtshell.settings.ybc.target,
        host=socket.gethostname(),
        log_file=yadtshell.settings.log_file)
