# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
#   YADT - an Augmented Deployment Tool
#   Copyright (C) 2010-2015  Immobilien Scout GmbH
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

from __future__ import (absolute_import, print_function)
from logging import getLogger

try:
    from StringIO import StringIO  # py2
except ImportError:
    from io import StringIO  # py3

from twisted.internet import defer, reactor
from twisted.internet.protocol import Protocol
from twisted.python.failure import Failure
from twisted.web.client import Agent, FileBodyProducer
from twisted.web.http_headers import Headers


logger = getLogger("rest_library")


HTTP_CONNECT_TIMEOUT_IN_SECONDS = 30


class HTTP_METHOD(object):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"


def rest_call(url, http_method=HTTP_METHOD.GET, headers=Headers(), data=""):
    """
    Returns a deferred that will callback with the response to a rest call
    or fire its err-back when a response code != 200 is received.

    Required positional arguments:
    -------------------------------

      * url
        The HTTP endpoint URI (string)

    Optional kwargs:
    -------------------------------

      * http_method
        The HTTP method that should be used. Valid methods are fields of
        the rest.HTTP_METHOD enum.
      * headers
        an instance of twisted.web.http_headers.Headers
      * data
        string with data to submit - no special treatment (e.G. no URL encoding!)
    """

    headers.addRawHeader("Content-Type", "text/plain")

    agent = Agent(reactor, None, connectTimeout=HTTP_CONNECT_TIMEOUT_IN_SECONDS)

    deferred = agent.request(http_method,
                             url,
                             headers,
                             FileBodyProducer(StringIO(data)) if data else None)
    deferred.addCallback(read_response)
    return deferred


def read_response(response):
    if response.code != 200:
        return Failure(Exception("Non-OK response for URL: %s" % response))
    d = defer.Deferred()
    response.deliverBody(BodyConsumer(d))
    return d


class BodyConsumer(Protocol):

    def __init__(self, finished):
        self.finished = finished
        self.data = ""

    def connectionMade(self, *args, **kwargs):
        pass

    def dataReceived(self, data):
        self.data += data

    def connectionLost(self, reason):
        self.finished.callback(self.data)
