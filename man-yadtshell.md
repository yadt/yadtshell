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

* status :
Retrieves the actual state of all target hosts
(see also https://github.com/yadt/yadtshell/wiki/Status-Information)

* update [*HOSTS*] :
Updates the specified hosts / all hosts by stopping related services
and restarting them afterwards. Guarantees that all services will be running
after a successful updates.

* start *SERVICES* :
Starts all specified *SERVICES*, regarding the correct order

* stop *SERVICES* :
Stops all specified *SERVICES*, regarding the correct order

* info :
Shows the last known state of the target, does not retrieve data from hosts

* ignore *SERVICES* :
ignores the specified services all following actions will be skipped and
its results are always successfull

* updateartefact *ARTEFACTS* :
updates the specified artefacts, but _disregarding any service dependencies_

* lock *HOSTS* :
Locks the host(s), ensuring that only you can perform operations on it.
Needs a message option.

## OPTIONS
* -n :
No operation: change nothing, just show what *would* be done (aka dryrun)

* -p *P-SPEC* :
Runs eligible operations in parallel.
See https://github.com/yadt/yadtshell/wiki/Wave-deployment-with-parallel-actions for more information.

## EXAMPLES

* yadtshell status:
retrieves the current state of your target

* yadtshell stop service://*/* :
stops all services

* yadtshell update host://foo1 host://foo2 :
updates both hosts

* yadtshell updateartefact artefact://foo1/some-config :
updates the package _some-config_ without regarding service dependencies

## SEE ALSO

the yadt project
:   http://www.yadt-project.org/

sources at github
:   https://github.com/yadt

Alternatives
:   puppet, chef

## LICENSE

Licensed under the GNU General Public License (GPL), see http://www.gnu.org/licenses/gpl.txt for full license text.
