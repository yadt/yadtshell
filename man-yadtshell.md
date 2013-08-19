YADTSHELL(1) YadtShell User Manuals
===================================

## NAME

yadtshell - yadt, an augmented deployment tool: the shell part

## SYNOPSIS

yadtshell *command* [*options*] [*component*]...

## DESCRIPTION

yadtshell allows you to control services and deployments, regarding
the dependencies across the whole data center.
The hosts to handle are taken from the *target* file in the current
directory.

## COMPONENTS
service://*host*/*servicename*

artefact://*host*/*artefactname*/*version*

host://*host*

(Wildcards `*` and `?`, and ranges `[start..end]` allowed)

## COMMANDS
status
:   Retrieves the actual state of all target hosts
(see also https://github.com/yadt/yadtshell/wiki/Status-Information)

start *SERVICES*
:   Starts all specified *SERVICES*, regarding the correct order

stop *SERVICES*
:   Stops all specified *SERVICES*, regarding the correct order

info
:   Shows the last known state of the target, does not retrieve data from hosts

ignore *SERVICES*
:   ignores the specified services: all following actions will be skipped and
its results are always successfull

## OPTIONS
-n
:   No operation: change nothing, just show what *would* be done (aka dryrun)

## EXAMPLES

yadtshell status
:   retrieves the current state of your target


## SEE ALSO

the yadt project
:   http://www.yadt-project.org/

sources at github
:   https://github.com/yadt

Alternatives
:   puppet, chef

## LICENSE

Licensed under the GNU General Public License (GPL), see http://www.gnu.org/licenses/gpl.txt for full license text.
