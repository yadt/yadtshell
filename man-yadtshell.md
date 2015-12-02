% YADTshell(1) YADTshell User Manuals
% The YADT project team
% December 18th, 2014

# NAME

yadtshell - yadt, an augmented deployment tool: the shell part

# SYNOPSIS

yadtshell *command* [*options*] [*component*]...

# DESCRIPTION

yadtshell allows you to control services and deployments, regarding
the dependencies across the whole data center.
The hosts to handle are taken from the *target* file in the current
directory.

# COMPONENTS
* services :
service://*host*/*servicename*

* artefacts :
artefact://*host*/*artefactname*/*version*

* hosts :
host://*host*

(Wildcards `*` and `?`, and ranges `[start..end]` allowed)

# INTERACTIVE USAGE
* enter an interactive session:

  *init-yadtshell*

  or

  *init-yadtshell TARGET* (directly enter TARGET directory and fetch status)

* Switch targets while in an interactive session:

    *using TARGET* (enter TARGET directory and fetch status)

# COMMANDS

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

* restart *SERVICE*:
Stops the specified *SERVICE* (including all dependent services) and then 
starts all services that had been stopped before. 

* info :
Shows the last known state of the target, does not retrieve data from hosts.

* ignore *SERVICES* :
Ignores the specified services all following actions will be skipped and
its results are always successful.

* ignore *HOSTS* :
Ignores the specified hosts and its services so that update waves will not be broken. Service status will not be shown and cannot be changed.

* updateartefact *ARTEFACTS* :
updates the specified artefacts, but _disregarding any service dependencies_.

* lock *HOSTS* :
Locks the host(s), ensuring that only you can perform operations on it.
Requires a message option.

* unlock *HOSTS* :
Releases the host(s) from your lock. This command assumes you own the lock and will fail if you do not. If you do not own the lock on the hosts, use *lock --force* on it first.

* reboot *HOSTS* :
Reboots the host(s), stopping all services and starting them afterwards.
This will always lead to a reboot of the host(s), ignoring whether the kernel is up to date or not. This command will never upgrade any outdated artefacts either.

# OPTIONS
* --reboot :
Reboots machines during an update, either if a pending artefact is configured to
induce a reboot, or if the machine is running an outdated kernel.
If a set of host URIs was passed to the update command, then only those hosts
are eligible for a reboot.
*NOTE* This is a no-op, as rebooting is the default!

* --no-reboot :
Prevents machines from being rebooted if necessary.

* --ignore-unreachable-hosts :
When a machine is not reachable, do not consider this an error and keep going.

* -n :
No operation: change nothing, just show what *would* be done (aka dryrun).

* -p *P-SPEC* :
Runs eligible operations in parallel.
See https://github.com/yadt/yadtshell/wiki/Wave-deployment-with-parallel-actions for more information.

* --force :
Ignores locks. Valid only for the `lock` command. This allows for taking over a lock
in order to release it.

* -m *MESSAGE* :
Adds a message to a command. Valid only for the `lock` and `ignore` commands.

* --no-final-status :
Do not query and display the *status* of the target after an action that changed it
(e.G. *start*, *update*, ...).

* --session-id *ID* :
Set a unique identifier for running commands in a session. With this option,
it is possible to use a lock acquired by locking on another host by using the same *ID* across all commands.

* --force-initial-status :
Force an initial status before calling the command.

# EXAMPLES

* yadtshell status:
retrieves the current state of your target

* yadtshell stop service://\*/\* :
stops all services

* yadtshell update host://foo1 host://foo2 :
updates both hosts

* yadtshell update host://foo1 :
updates or reboots (or possibly both) but only on foo1

* yadtshell update :
updates (and possibly reboots) all servers from the target

* yadtshell update --no-reboot :
updates (but does not reboot) all servers from the target

* yadtshell update host://foo1 --no-reboot :
updates foo1, but does not reboot in any case

* yadtshell updateartefact artefact://foo1/some-config :
updates the package _some-config_ without regarding service dependencies

# SEE ALSO

the yadt project
:   http://www.yadt-project.org/

sources at github
:   https://github.com/yadt

the yadtshell wiki
:   https://github.com/yadt/yadtshell/wiki

Alternatives
:   ansible, saltstack, fabric

# LICENSE

Licensed under the GNU General Public License (GPL), see http://www.gnu.org/licenses/gpl.txt for full license text.
