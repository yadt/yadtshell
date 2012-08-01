#! /usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import os.path
import logging

import yadtshell.helper

logger = logging.getLogger('uri')

def create(type=None, host=None, name=None, version=None, **kwargs):
    if version is None:
        version = ''
    if name is None:
        name = ''
    if host is None or host.strip() == "":
        raise ValueError("Mandatory parameter 'host' is missing or '' or None")
    if type is None or type.strip() == "":
        raise ValueError("Mandatory parameter 'type' is missing or '' or None")
    name = name.strip()
    type = type.strip()
    host = host.strip()
    if name and version.startswith(name):
        #logger.debug('version still starts with name:' + version)
        version = version.replace(name + '/', '')
    uri = '%(type)s://%(host)s/%(name)s/%(version)s' % locals()
    return uri.rstrip('/')

def change_version(uri, version=None):
    uri_obj = parse(uri)
    uri_obj['version'] = version
    return create(**uri_obj)

def as_file(s):
    parts = parse(s)
    return '%(type)s:%(name)s' % parts

def as_source_file(s):
    parts = parse(s)
    version = parts['version']
    if version is None or version == '':
        return '%(name)s' % parts
    return '%(name)s/%(version)s' % parts

def as_path(s):
    parts = parse(s)
    # TODO: What happens if version is None or empty? Should this raise an exception or be silently
    # converted to something else?
    return os.path.join(yadtshell.helper.plural(parts['type']), parts['name'], parts['version'])

def parse(s):
    t, rest = s.split('://', 1)
    try:
        host, name, version = rest.split('/', 2)
    except ValueError:
        try:
            host, name = rest.split('/', 1)
            version = None
        except ValueError:
            host = rest
            name = version = None
    if version is not None:
        name_version = name + '/' + version
    else:
        name_version = name
    return dict(
        type=t,
        host=host,
        name=name,
        version=version,
        name_version=name_version
    )

