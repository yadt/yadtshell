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
from __future__ import print_function
import logging
import sys
from subprocess import Popen, PIPE
import time

import hostexpand
import yadtshell

logger = logging.getLogger('info')


def render_green(text):
    return yadtshell.settings.term.render('${BG_GREEN}${WHITE}${BOLD}%s${NORMAL}' % text)


def render_yellow(text):
    return yadtshell.settings.term.render('${BG_YELLOW}${BOLD}%s${NORMAL}' % text)


def render_red(text):
    return yadtshell.settings.term.render('${BG_RED}${WHITE}${BOLD}%s${NORMAL}' % text)


def _show_host_locking_or_unreachable(host):
    if not host.is_reachable():
        print(render_red('\n%10s is unreachable!\n' % (host.host)))
        return
    if host.is_locked:
        lock_owner = host.lockstate.get("owner", "Unknown")
        reason = host.lockstate.get("message", "--- no message given ---")
        if host.is_locked_by_me:
            print(render_yellow('\n%10s is locked by me\n%10s %s\n' %
                  (host.host, "reason", reason)))
        elif host.is_locked_by_other:
            print(render_red('\n%10s is locked by %s\n%10s %s\n' %
                  (host.host, lock_owner, "reason", reason)))


def _show_ignored_services(services):
    ignored_services = False
    for service in services:
        if hasattr(service, 'ignored'):
            ignored_services = True
            print(render_yellow('\n%20s is ignored\n%10s' %
                  (service, service.ignored.get('message', 'no message'))))

    if ignored_services:
        print()  # separate ignored services from locked hosts


def info(logLevel=None, full=False, components=None, **kwargs):
    if not components:
        logger.debug("loading current state")
        try:
            components = yadtshell.util.restore_current_state()
        except IOError:
            logger.critical("cannot restore current state")
            logger.info("call 'yadtshell status' first")
            sys.exit(1)

    result = []
    for component in components.values():
        result.append((component.uri, component.state))

    print()
    print(yadtshell.settings.term.render(
        '${BOLD}yadt info | %s${NORMAL}' % yadtshell.settings.TARGET_SETTINGS['name']))

    print()
    print('target status')

    services = [component for component in components.values()
                if isinstance(component, yadtshell.components.Service)]

    _show_ignored_services(services)

    hosts = sorted(
        [c for c in components.values() if c.type == yadtshell.settings.HOST], key=lambda h: h.uri)
    for host in hosts:
        _show_host_locking_or_unreachable(host)
        if isinstance(host.next_artefacts, dict):
            _render_updates_based_on_key_value_schema(components, host, full)
        else:
            _render_updates_based_on_name_schema(components, host, full)

    print()

    condensed = yadtshell.helper.condense_hosts2(
        yadtshell.helper.condense_hosts(result))
    components_with_problems = [c for c in condensed
                                if (c[0].startswith(yadtshell.settings.ARTEFACT) or c[0].startswith(yadtshell.settings.CONFIG))
                                and yadtshell.util.not_up(c[1])]
    if components_with_problems:
        print('problems')
        for c in components_with_problems:
            print(yadtshell.util.render_component_state(c[0], c[1]))
        print()

    for missing_component in [c for c in components.values() if isinstance(c,
                              yadtshell.components.MissingComponent)]:
        print(render_red('\nconfig problem: missing %s\n' %
              missing_component.uri))

    for service in services:
        if getattr(service, 'service_artefact_problem', None):
            print(
                render_red('problem with %(uri)s\n\t%(service_artefact)s: %(service_artefact_problem)s\n\t-> no artefact dependencies available!\n' % vars(service)))
            print()

    render_services_matrix(components)

    now = time.time()
    max_age = now - yadtshell.util.get_mtime_of_current_state()
    if max_age > 20:
        max_age = render_red('  %.0f  ' % max_age)
    else:
        max_age = render_green('  %.0f  ' % max_age)
    print('queried %s seconds ago' % max_age)
    print()

    print('status: ' + yadtshell.util.get_status_line(components))


def _render_updates_based_on_name_schema(components, host, full):
        # DEPRECATED: is used for old BASH client only.

        host_artefacts = {}
        for current_artefact in [
            c for c in components.values() if (c.type == yadtshell.settings.ARTEFACT
                                               and c.host == host.hostname
                                               and c.revision == yadtshell.settings.CURRENT)
        ]:
            artefact = host_artefacts.setdefault(current_artefact.name, {})
            artefact[yadtshell.settings.CURRENT] = current_artefact
            next_artefact = components.get(
                yadtshell.uri.change_version(current_artefact.uri, 'next'))
            if next_artefact:
                artefact[yadtshell.settings.NEXT] = next_artefact
        for artefact in sorted(host_artefacts.keys()):
            variants = host_artefacts[artefact]
            current_version = variants[yadtshell.settings.CURRENT].version
            if full:
                print('%10s  %40s  %s' %
                      (host.host, variants[yadtshell.settings.CURRENT].name, current_version))
            if yadtshell.settings.NEXT in variants:
                if not full:
                    print('%10s  %40s  %s' %
                          (host.host, variants[yadtshell.settings.CURRENT].name, current_version))
                next_version = components[
                    variants[yadtshell.settings.NEXT]].version
                nd_display = []
                for i in range(len(next_version)):
                    try:
                        if current_version[i] == next_version[i]:
                            nd_display.append(next_version[i])
                            continue
                    except:
                        pass
                    nd_display.append(
                        '${REVERSE}%s${NORMAL}' % next_version[i])
                print('%10s  %40s  %s' %
                      ('', '(next)', yadtshell.settings.term.render(''.join(nd_display))))
        if full:
            print()


def _render_updates_based_on_key_value_schema(components, host, *args, **kwargs):
    for next_artefact_uri, old_artefact_uri in host.next_artefacts.iteritems():
        # TODO better as helper method in Uri?
        next_artefact = components[
            "artefact://%s/%s" % (host.host, next_artefact_uri)]
        old_artefact = components[
            "artefact://%s/%s" % (host.host, old_artefact_uri)]
        next_artefact_name = next_artefact.name if next_artefact.name != old_artefact.name else ''
        print('%10s  %40s  %s' %
              (host.host, old_artefact.name, old_artefact.version))
        print('%10s  %40s  %s' % ('',
                                  '(next) ' + render_highlighted_differences(
                                      old_artefact.name, next_artefact_name),
                                  render_highlighted_differences(old_artefact.version, next_artefact.version)))
    return


def highlight_differences(reference, text):
    result = []
    for i in range(len(text)):
        if text[i] != reference[i]:
            result.append('${REVERSE}')
            result.extend(text[i:])
            result.append('${NORMAL}')
            break
        result.append(text[i])
    return ''.join(result)


def render_highlighted_differences(*args):
    return yadtshell.settings.term.render(highlight_differences(*args))


def calculate_info_view_settings():
    original_hosts = yadtshell.settings.TARGET_SETTINGS['original_hosts']
    try:
        stty = Popen(
            ['stty', 'size'], stdout=PIPE, stderr=PIPE).communicate()[0]
        cols = int(stty.split()[1])
    except:
        cols = 80

    logger.debug("expanding hosts")
    he = hostexpand.HostExpander.HostExpander()
    max_row_length = max([len(he.expand(hosts)) for hosts in original_hosts])
    logger.debug("expanded hosts")

    width = '1col'

    RIGHT_MARGIN_WIDTH = 40

    if max_row_length * 4 + RIGHT_MARGIN_WIDTH <= cols:
        width = '3cols'
    if max_row_length * 10 + RIGHT_MARGIN_WIDTH <= cols:
        width = 'maxcols'

    return ['matrix', 'color', width]


def render_readonly_services(components):
    for ro_service in yadtshell.util.filter_missing_services(components):
        print("%s: %s" % (ro_service.uri, ro_service.state))


def render_services_matrix(components=None, **kwargs):
    if not components:
        components = yadtshell.util.restore_current_state()
    info_view_settings = calculate_info_view_settings()
    he = hostexpand.HostExpander.HostExpander()
    for hosts in yadtshell.settings.TARGET_SETTINGS['original_hosts']:
        _render_services_matrix(
            components, he.expand(hosts), info_view_settings, *kwargs)
    render_readonly_services(components)
    render_legend(info_view_settings)


def _render_services_matrix(components, hosts, info_view_settings, enable_legend=False):
    host_components = set()
    for host in hosts:
        found = components.get(host)
        if not found:
            for c in [h for h in components.values() if type(h) is yadtshell.components.Host or type(h) is yadtshell.components.UnreachableHost]:
                if getattr(c, 'hostname', None) == host:
                    found = c
                    break
                if getattr(c, 'fqdn', None) == host:
                    found = c
                    break
        if not found:
            print('ERROR: cannot find host %s' % host)
            continue
        host_components.add(found)
    hosts = sorted(host_components, key=lambda h: h.uri)

    ranks = {}
    services = []
    for host in hosts:
        for servicedef in getattr(host, 'services', []):
            try:
                service = servicedef.keys()[0]
            except:
                service = servicedef
            if service not in services:
                rank = components[yadtshell.uri.create(
                    yadtshell.settings.SERVICE, host.hostname, service)].dependency_score
                services.append((rank, service))

    for rank, name in services:
        ranks[name] = rank

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
        print('  %s' % separator.join(['%-9s' % host.host for host in hosts]))
    elif '3cols' in info_view_settings:
        def print_3cols(start, end):
            line = []
            for name in [host.host for host in hosts]:
                line.append(name[start:end])
            print('   %s' %
                  separator.join(['%3s' % string for string in line]))
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
            print('  %s' % ''.join(line))
    print()

    for name in sorted(ranks, key=lambda x: ranks[x]):
        s = []
        for host in hosts:
            uri = yadtshell.uri.create(
                yadtshell.settings.SERVICE, host.host, name)
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
        print('  %s  service %s %s' % (separator.join(s), name, suffix))
    s = []
    for host in hosts:
        if not host.is_reachable():
            s.append(icons['UNKNOWN'])
        elif host.is_uptodate():
            s.append(icons['UPTODATE'])
        elif host.is_update_needed():
            s.append(icons['UPDATE_NEEDED'])
        else:
            s.append(icons['NA'])
    print('  %s  %s' % (separator.join(s), 'host uptodate'))

    s = []
    for host in hosts:
        if not host.is_reachable():
            s.append(icons['UNKNOWN'])
        elif host.reboot_required_to_activate_latest_kernel:
            s.append(icons['REBOOT_NOW'])
        elif host.reboot_required_after_next_update:
            s.append(icons['REBOOT_AFTER_UPDATE'])
        else:
            s.append(icons['UP'])
    print('  %s  %s' % (separator.join(s), 'reboot required'))

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
    print('  %s  %s' % (separator.join(s), 'host access'))
    print()

    if enable_legend:
        render_legend(info_view_settings)


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
        'REBOOT_NOW': 'R',
        'REBOOT_AFTER_UPDATE': 'r',
        'NOT_LOCKED': '|'
    }


def colorize(icons):
    icons['REBOOT_AFTER_UPDATE'] = render_yellow(icons['REBOOT_AFTER_UPDATE'])
    icons['REBOOT_NOW'] = render_red(icons['REBOOT_NOW'])
    icons['UP'] = render_green(icons['UP'])
    icons['DOWN'] = render_red(icons['DOWN'])
    icons['UNKNOWN'] = render_red(icons['UNKNOWN'])
    icons['UP_IGNORED'] = render_yellow(icons['UP_IGNORED'])
    icons['DOWN_IGNORED'] = render_yellow(icons['DOWN_IGNORED'])
    icons['UNKNOWN_IGNORED'] = render_yellow(icons['UNKNOWN_IGNORED'])
    icons['NOT_LOCKED'] = icons['UP']
    icons['LOCKED_BY_ME'] = render_yellow(icons['LOCKED_BY_ME'])
    icons['LOCKED_BY_OTHER'] = render_red(icons['LOCKED_BY_OTHER'])
    icons['UPTODATE'] = icons['UP']
    icons['UPDATE_NEEDED'] = render_yellow(icons['UPDATE_NEEDED'])
    return icons


def render_legend(info_view_settings):
    icons = get_icons()
    if 'color' in info_view_settings:
        icons = colorize(icons)

    print(
        'legend: %(UP)s up(todate),accessible  %(DOWN)s down  %(UNKNOWN)s unknown  %(UP_IGNORED)s%(DOWN_IGNORED)s%(UNKNOWN_IGNORED)s ignored (up,down,unknown)' %
        icons)
    print(
        '        %(LOCKED_BY_ME)s%(LOCKED_BY_OTHER)s locked by me/other  %(UPDATE_NEEDED)s update pending' %
        icons)
    print(
        '        %(REBOOT_AFTER_UPDATE)s%(REBOOT_NOW)s reboot needed (after update/due to new kernel)' %
        icons)
    print()


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
