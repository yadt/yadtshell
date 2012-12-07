#! /usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
import logging
import time

import hostexpand

import yadtshell

logger = logging.getLogger('info')


def _show_host_locking(host):
    if host.is_locked:
        lock_owner = host.lockstate.get("owner", "Unknown")
        reason = host.lockstate.get("message", "--- no message given ---")
        if host.is_locked_by_me:
            print yadtshell.settings.term.render('${BG_YELLOW}${WHITE}${BOLD}')
            print('%10s is locked by me' % host.host)
            print yadtshell.settings.term.render('%10s %s ${NORMAL}' % ('reason:', reason))
        elif host.is_locked_by_other:
            print yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}')
            print('%10s is locked by %s' % (host.host, lock_owner))
            print yadtshell.settings.term.render('%10s %s ${NORMAL}' % ('reason:', reason))

def info(logLevel=None, full=False, **kwargs):
    components = yadtshell.util.restore_current_state()

    result = []
    for component in components.values():
        result.append((component.uri, component.state))

    print
    print yadtshell.settings.term.render('${BOLD}yadt info | %s${NORMAL}' % yadtshell.settings.TARGET_SETTINGS['name'])

    print
    print 'target status'

    artefacts = {}  # TODO refactor: needed anywhere else?
    hosts = sorted([c for c in components.values() if c.type == yadtshell.settings.HOST], key=lambda h: h.uri)
    for host in hosts:
        _show_host_locking(host)

        host_artefacts = artefacts.setdefault(host.host, {})    
        for current_artefact in [
            c for c in components.values() if c.host == host.hostname and c.revision == yadtshell.settings.CURRENT
        ]:
            artefact = host_artefacts.setdefault(current_artefact.name, {})
            artefact[yadtshell.settings.CURRENT] = current_artefact
            next_artefact = components.get(yadtshell.uri.change_version(current_artefact.uri, 'next')) 
            if next_artefact:
                artefact[yadtshell.settings.NEXT] = next_artefact
        for artefact in sorted(host_artefacts.keys()):
            variants = host_artefacts[artefact]
            current_version = variants[yadtshell.settings.CURRENT].version
            if full:
                print '%10s  %40s  %s' % (host.host, variants[yadtshell.settings.CURRENT].name, current_version) 
            if yadtshell.settings.NEXT in variants:
                if not full:
                    print '%10s  %40s  %s' % (host.host, variants[yadtshell.settings.CURRENT].name, current_version) 
                next_version = components[variants[yadtshell.settings.NEXT]].version
                nd_display = []
                for i in range(len(next_version)):
                    try:
                        if current_version[i] == next_version[i]:
                            nd_display.append(next_version[i])
                            continue
                    except:
                        pass
                    nd_display.append('${REVERSE}%s${NORMAL}' % next_version[i])
                print '%10s  %40s  %s' % ('', '(next)', yadtshell.settings.term.render(''.join(nd_display)))
        if full:
            print
    print

    condensed = yadtshell.helper.condense_hosts2(yadtshell.helper.condense_hosts(result))
    components_with_problems = [c for c in condensed
        if (c[0].startswith(yadtshell.settings.ARTEFACT) or
            c[0].startswith(yadtshell.settings.CONFIG)) and yadtshell.util.not_up(c[1])]
    if components_with_problems:
        print 'problems'
        for c in components_with_problems:
            print yadtshell.util.render_component_state(c[0], c[1])
        print

    for missing_component in [c for c in components.values() if isinstance(c,
        yadtshell.components.MissingComponent)]:
        print yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}')
        print 'config problem: missing %s' % missing_component.uri
        print yadtshell.settings.term.render('${NORMAL}')

    for service in [component for component in components.values() if
            isinstance(component, yadtshell.components.Service)]:
        if getattr(service, 'service_artefact_problem', None):
            print yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}')
            print 'problem with %(uri)s' % vars(service)
            print '\t%(service_artefact)s: %(service_artefact_problem)s' % vars(service)
            print '\t-> no artefact dependencies available!'
            print yadtshell.settings.term.render('${NORMAL}')
            print

    info_view_settings = yadtshell.settings.VIEW_SETTINGS.get('info-view', [])
    if 'matrix' in info_view_settings:
        render_services_matrix(components)
    else:
        print 'services'
        def extract_name(s):
            return s.rsplit('/', 1)[1]
        ranks = {}
        services = []
        for host in [component for component in components.values() if component.type == yadtshell.settings.HOST]:
            for service in getattr(host, 'defined_services', set()):
                if not service.name in services:
                    services.append(service.name)
        for rank, name in enumerate(services):
            ranks[name] = rank
        for c in sorted(
            [c for c in condensed if c[0].startswith(yadtshell.settings.SERVICE)],
            key=lambda t: '%03i %s' % (ranks[extract_name(t[0])], t[0])
        ):
            print yadtshell.util.render_component_state(c[0], c[1])

        print
        print 'hosts'
        for c in sorted(
            [c for c in condensed if c[0].startswith(yadtshell.settings.HOST)] 
        ):
            print yadtshell.util.render_component_state(c[0], c[1])

    now = time.time()
    max_age = now - yadtshell.util.get_mtime_of_current_state()
    #for host in [c for c in components.values() if c.type == yadtshell.settings.HOST and not yadtshell.util.not_up(c.state)]:
        #max_age = max(max_age, now - int(host.epoch))
    if max_age > 120:
        max_age = yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}  %.0f  ${NORMAL}' % max_age)
    elif max_age > 60:
        max_age = yadtshell.settings.term.render('${RED}${BOLD}%.0f${NORMAL}' % max_age)
    elif max_age > 20:
        max_age = yadtshell.settings.term.render('${RED}%.0f${NORMAL}' % max_age)
    else:
        max_age = yadtshell.settings.term.render('${GREEN}${BOLD}%.0f${NORMAL}' % max_age)
    print 'queried %s seconds ago' % max_age
    print

    print 'status: ' + yadtshell.util.get_status_line(components)


def render_services_matrix(components=None, **kwargs):
    if not components:
        components = yadtshell.util.restore_current_state()
    he = hostexpand.HostExpander.HostExpander()
    for hosts in yadtshell.settings.TARGET_SETTINGS['original_hosts']:
        _render_services_matrix(components, he.expand(hosts), *kwargs)
    render_legend()

def _render_services_matrix(components, hosts, enable_legend=False):
    host_components = set()
    for host in hosts:
        found = components.get(host)
        if not found:
            for c in [h for h in components.values() if type(h) is yadtshell.components.Host]:
                if getattr(c, 'hostname', None) == host:
                    found = c
                    break
                if getattr(c, 'fqdn', None) == host:
                    found = c
                    break
        if not found:
            print 'ERROR: cannot find host %s' % host
            continue
        host_components.add(found)
    hosts = sorted(host_components, key=lambda h: h.uri)

    ranks = {}
    services = []
    for host in hosts:
        for servicedef in getattr(host, 'services', []):
            service = servicedef.keys()[0]
            if not service in services:
                services.append(service)
    for rank, name in enumerate(services):
        ranks[name] = rank

    info_view_settings = yadtshell.settings.VIEW_SETTINGS.get('info-view', [])

    icons = get_icons()
    separator = ''
    if 'maxcols' in info_view_settings:
        separator = '  '
        for icon, string in icons.iteritems():
            icons[icon] = '    %s    ' % string
    elif '3cols' in info_view_settings:
        separator = ' '
        for icon, string in icons.iteritems():
            icons[icon] = ' %s ' % string
    if 'color' in info_view_settings:
        icons = colorize(icons)
    if 'maxcols' in info_view_settings:
        print '  %s' % separator.join(['%-9s' % host.host for host in hosts])
    elif '3cols' in info_view_settings:
        def print_3cols(start, end):
            line = []
            for name in [host.host for host in hosts]:
                line.append(name[start:end])
            print '   %s' % separator.join(['%3s' % string for string in line])
        print_3cols(0, 3)
        print_3cols(3, 6)
        print_3cols(6, 9)
    else:
        last = None
        names = []
        max_len = 0
        for name in [host.host for host in hosts]:
            if not last:
                names.append(name)
                max_len = len(name)
            else:
                new_name = []
                for i in range(0, len(name)):
                    if name[i] == last[i]:
                        new_name.append(' ')
                    else:
                        new_name.append(name[i])
                names.append(separator.join(new_name))
            last = name
        for i in range(max_len):
            line = []
            for name in names:
                line.append(name[i])
            print '  %s' % ''.join(line)
    print
    for name in sorted(ranks, key=lambda x: ranks[x]):
        s = []
        for host in hosts:
            uri = yadtshell.uri.create(yadtshell.settings.SERVICE, host.host, name)
            service = components.get(uri, None)
            if service:
                if getattr(service, 'ignored', False):
                    if service.is_up():
                        s.append(icons['UP_IGNORED'])
                    elif service.is_unknown():
                        s.append(icons['UNKNOWN_IGNORED'])
                    else:
                        s.append(icons['DOWN_IGNORED'])
                else:
                    if service.is_up():
                        s.append(icons['UP'])
                    elif service.is_unknown():
                        s.append(icons['UNKNOWN'])
                    else:
                        s.append(icons['DOWN'])
            else:
                s.append(icons['NA'])
            suffix = ''
            if getattr(service, 'is_frontservice', False):
                suffix = '(frontservice)'
        print '  %s  service %s %s' % (separator.join(s), name, suffix)
    s = []
    for host in hosts:
        if host.is_uptodate():
            s.append(icons['UPTODATE'])
        elif host.is_update_needed():
            s.append(icons['UPDATE_NEEDED'])
        else:
            s.append(icons['NA'])
    print '  %s  %s' % (separator.join(s), 'host uptodate')
    s = []
    for host in hosts:
        if host.is_locked_by_other:
            s.append(icons['LOCKED_BY_OTHER'])
        elif host.is_locked_by_me:
            s.append(icons['LOCKED_BY_ME'])
        elif host.is_unknown():
            s.append(icons['UNKNOWN'])
        else:
            s.append(icons['NOT_LOCKED'])
    print '  %s  %s' % (separator.join(s), 'host access')
    print

    if enable_legend:
        render_legend()


def get_icons():
    return {
        'NA': ' ',
        'UP': '|',
        'DOWN': 'O',
        'UNKNOWN': '?',
        'UP_IGNORED': 'i',
        'DOWN_IGNORED': 'o',
        'UNKNOWN_IGNORED': '?',
        'LOCKED_BY_ME': 'l',
        'LOCKED_BY_OTHER': 'L',
        'UPTODATE': '|',
        'UPDATE_NEEDED': 'u',
    }

def colorize(icons):
    icons['UP'] = yadtshell.settings.term.render('${BG_GREEN}${WHITE}${BOLD}%s${NORMAL}' % icons['UP'])
    icons['DOWN'] = yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}%s${NORMAL}' % icons['DOWN'])
    icons['UNKNOWN'] = yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}%s${NORMAL}' % icons['UNKNOWN'])
    icons['UP_IGNORED'] = yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % icons['UP_IGNORED'])
    icons['DOWN_IGNORED'] = yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % icons['DOWN_IGNORED'])
    icons['UNKNOWN_IGNORED'] = yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % icons['UNKNOWN_IGNORED'])
    icons['NOT_LOCKED'] = icons['UP']
    icons['LOCKED_BY_ME'] = yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % icons['LOCKED_BY_ME'])
    icons['LOCKED_BY_OTHER'] = yadtshell.settings.term.render('${BG_RED}${BOLD}${WHITE}%s${NORMAL}' % icons['LOCKED_BY_OTHER'])
    icons['UPTODATE'] = icons['UP']
    icons['UPDATE_NEEDED'] = yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % icons['UPDATE_NEEDED'])
    return icons

def render_legend():
    info_view_settings = yadtshell.settings.VIEW_SETTINGS.get('info-view', [])

    icons = get_icons()
    if 'color' in info_view_settings:
        icons = colorize(icons)

    print 'legend: %(UP)s up(todate),accessible  %(DOWN)s down  %(UNKNOWN)s unknown  %(UP_IGNORED)s%(DOWN_IGNORED)s%(UNKNOWN_IGNORED)s ignored (up,down,unknown)' % icons
    print '        %(LOCKED_BY_ME)s%(LOCKED_BY_OTHER)s locked by me/other  %(UPDATE_NEEDED)s update pending' % icons
    print


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('', '--full', action='store_true',
        dest='full', default=False)
    parser.add_option('', '--services-matrix-only', action='store_true',
        dest='services_matrix_only', default=False)
    opts, args = parser.parse_args()

    if opts.services_matrix_only:
        render_services_matrix(enable_legend=False)
    else:
        info(**vars(opts))

