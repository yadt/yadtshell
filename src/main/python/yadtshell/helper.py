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

import fnmatch
import re
import pwd
import os
import socket
import time
import linecache

cmd_counter = 0


def condense_hosts(words):
    wgs = {}
    for word in words:
        if type(word) is tuple:
            aux = word[1]
            word = word[0]
        else:
            aux = None
        mo = re.search('\d\d', word)
        if mo:
            wgs.setdefault((word[:mo.start()], word[mo.end():], aux), []).append(word[mo.start():mo.end()])
        else:
            wgs.setdefault((word, aux), []).append('')
    chunks = {}
    for wg in wgs.keys():
        chunk = (None, None)
        for nr in sorted(wgs[wg]):
            if chunk[1] is not None and chunk[1] == nr:
                continue
            if chunk[1] is not None and int(chunk[1]) + 1 == int(nr):
                chunk = (chunk[0], nr)
                continue
            else:
                if chunk[0] is not None:
                    chunks.setdefault(wg, []).append(chunk)
                chunk = (nr, nr)
        if chunk[0] is not None:
            chunks.setdefault(wg, []).append(chunk)
    results = []
    for wg in sorted(chunks.keys()):
        result = []
        brackets_needed = len(chunks[wg]) > 1
        for chunk in chunks[wg]:
            if chunk[0] == chunk[1]:
                result.append(chunk[0])
            else:
                brackets_needed = True
                result.append('..'.join(list(chunk)))
        if brackets_needed:
            result = '[' + ','.join(result) + ']'
        else:
            result = result[0]
        prefix = wg[0]
        if wg[1]:
            suffix = wg[1].rstrip('/')
        else:
            suffix = ''
        if len(wg) > 2 and wg[2] is not None:
            results.append((prefix + result + suffix, wg[2]))
        else:
            results.append(prefix + result + suffix)
    return results


def expand_hosts(words):
    def add_result(host, aux):
        if host.startswith('host://'):
            host = host.rstrip('/')
        if aux is not None:
            results.append((host, aux))
        else:
            results.append(host)
    results = []
    for word in words:
        if type(word) is tuple:
            aux = word[1]
            word = word[0]
        else:
            aux = None
        ranges_start = word.find('[')
        if ranges_start < 0:
            add_result(word, aux)
            continue
        ranges_end = word.find(']', ranges_start)
        prefix = word[:ranges_start]
        suffix = word[ranges_end + 1:]
        ranges = word[ranges_start + 1:ranges_end]
        for r in ranges.split(','):
            if r.find('..') < 0:
                r = int(r)
                add_result('%(prefix)s%(r)02i%(suffix)s' % locals(), aux)
                continue
            pmin, pmax = r.split('..')
            for i in range(int(pmin), int(pmax) + 1):
                add_result('%(prefix)s%(i)02i%(suffix)s' % locals(), aux)
    return results


def glob_hosts(components, words):
    results = []
    for w in words:
        if w.find('*') >= 0 or w.find('?') >= 0:
            results.extend(fnmatch.filter(components.keys(), w))
        else:
            results.append(w)
    return results


def condense_hosts2(words):
    ws = {}
    for word in words:
        if type(word) is tuple:
            aux = word[1]
            word = word[0]
        else:
            aux = None
        try:
            prefix, rest = word.split('://', 1)
            prefix = prefix + '://'
        except:
            prefix = ''
            rest = word
        var = rest[:3]
        rest = rest[3:]
        ws.setdefault((prefix, rest, aux), []).append(var)
    result = []
    for constant, variables in ws.iteritems():
        if len(variables) <= 1:
            condensed = constant[0] + variables[0] + constant[1]
        else:
            condensed = constant[0] + '[' + ','.join(variables) + ']' + constant[1]
        if constant[2] is None:
            result.append(condensed)
        else:
            result.append((condensed, constant[2]))
    return result


def get_user_info():
    user = pwd.getpwuid(os.getuid())[0]
    yadt_host = socket.gethostname()
    working_copy = os.getcwd()
    owner = user + '@' + yadt_host + ':' + working_copy
    when = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime())
    pid = os.getpid()

    return {"user": user,
            "yadt_host": yadt_host,
            "working_copy": working_copy,
            "owner": owner,
            "when": when,
            "pid": pid,
    }


def create_log_filename(log_dir, target_name, started_on, user, host, tag=None):
    global cmd_counter
    log_file = '%s/yadtshell.%s.%s.%s.%s' % (log_dir, target_name, started_on, user, host)
    cmd_counter = cmd_counter + 1
    if tag:
        log_file = '%s.%s' % (log_file, tag)
    return '%s.log' % log_file


def plural(string):
    return string + 's'


def locate(pattern, root=os.curdir, blacklist=None):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory, follows symbolic links.'''
    if not blacklist:
        blacklist = set(['.svn', 'out', 'logs', 'config'])
    for path, dirs, files in os.walk(os.path.abspath(root)):
        if blacklist:
            for blacklisted in blacklist:
                if blacklisted in dirs:
                    dirs.remove(blacklisted)
        for d in dirs:
            if os.path.islink(d):
                for filename in locate(pattern,
                        root=os.path.realpath(os.path.join(path, d)), blacklist=blacklist):
                    yield filename
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


def _traceit(frame, event, arg):
    '''http://www.dalkescientific.com/writings/diary/archive/2005/04/20/tracing_python_code.html'''
    if event == "line":
        lineno = frame.f_lineno
        filename = frame.f_globals["__file__"]
        if (filename.endswith(".pyc") or filename.endswith(".pyo")):
            filename = filename[:-1]
        name = frame.f_globals["__name__"]
        line = linecache.getline(filename, lineno)
        print "%s  # %s:%s" % (line.rstrip(), name, lineno,)
    return _traceit
#    sys.settrace(_traceit)

