# YADTSHELL [![Build Status](https://secure.travis-ci.org/yadt/yadtshell.png?branch=master)](http://travis-ci.org/yadt/yadtshell)


## Prerequisites 

Make sure that the target hosts are accessible via ssh passwordless.

## Getting Background Information: the Yadt Model, Components, and Uris 
## Components 
*Note:* Components are always host-specific.

 * Hosts
 * Services
 * Artefacts (here: rpms)

### Uris 
 * denote components: ```<type>://<host>[/<name>[/<version>]]```
 * simple examples: 
   * ```host://berhost``` 
   * ```service://berhost/tomcat6```
   * ```artefact://berhost/yadt-client/0:0.36```
 * multiple Uris may be given using wildcards, alternatives, or range expressions:
  * example: all services on a host - ```service://host/*```
  * example: just two artefacts with same name, different hosts - ```artefact://{host01|host33}/yadt-client ```
  * example: hosts 10 to 13 - ```host://host[10..13]```

### Dependencies 
 * Components may need other components.
 * example: service://berhost/httpd needs service://berhost/tomcat6
 * example: service://berhost/tomcat6 needs artefact://berhost/jdk/6.0.12
 * if a component changes (gets started, stopped, updated), all depending components gets notified, resulting (normally) in a restart (if it is a service).
 * example: Changing the jdk artefact on ```berhost``` triggers the restart of the tomcat6 service, this triggers the restart of the httpd service.
 * Yadt takes care of these dependencies and creates an *ActionPlan* with the appropriate actions, in the appropriate order.

## Getting Started: the yadtshell 

### ``` init-yadtshell ```
or ``` source yadtshell-activate``` 

 * provides autocompletion and an informative bash prompt
 * defines some aliases: ```yadtshell``` as command not needed
 * provides the function ```deactivate``` for restoring the old shell settings
 
## Getting Help: the --help option 
When a command is given, the ```--help``` option lists the command-specific options, too.

## Getting General Options
The following options are available for all yadtshell commands:

* ```-n``` dryrun/do nothing, just print
* ```-v``` verbose output


## Getting Information: status / info / dump 

### Defining the intended audience: the target file 
yadt-shell uses a file named ```target``` in the current working directory.
A minimal example:

    hosts:
    - foohost[1..4] barhost[1..4]


### ``` status``` 
 * queries all target hosts via ssh
 * accepts host status in yaml format
 * prints short summary (using ```info```)

### ``` info``` 
 * displays a short summary of all services running on target hosts.

### ``` dump [uri-query0 [uri-query1 ...]]``` 
 * displays low-level data of components (in yaml format)
 * takes uri parts as query parameter
 * example: dump info of all services

    ```dump service://```


## Getting Things Done: the Actions start, stop, and update 
### ``` start <service_uri> [<service_uri> ...]``` 
 * starts a service, regarding its dependencies (i.e. starting needed services in the correct order)
 * example: start all services

    ```start service://*```

### ``` stop <service_uri> [<service_uri> ...]``` 
 * counterpart to start.

*Note:* stopping service A and starting it again may not yield the result you would expect:

 * stopping service A results in stopping *all* services depending on A.
 * Starting service A simple starts A, *not* the depending services. (How should Yadt know, which services you want to start again?)
 * Make sure that you start your most depending services. Starting these will result in starting service A, too. Or simply start all services as shown in the ```start``` example.

### ``` update``` 
 * if there are any updates, yadt installs updates and starts/stops the relevant services for you

### ``` updateartefact <artefact_uri> [<artefact_uri> ...]``` 
 * simply updates artefacts, ignoring all service dependencies
 * Use on your own risk.


## Getting Collaboration: lock, unlock, ignore, and unignore 

### ``` lock -m "lock reason" [--force] <host_uri> [<host_uri> ...]``` 
 * lock a host: only you can issue yadt commands on the locked hosts, and only from your current working dir
 * example: lock a single host 

    ```lock -m "lockreason" host://berhost01```
 * example: lock all hosts in your target

    ```lock -m "lockreason" host://*```
 * example: break an existing lock, locking the host by yourself

    ```lock -m "reason" --force host://*```

### ``` unlock <host_uri> [<host_uri] ...]``` 
 * releasing an own lock
 * example: unlock all hosts in your target

    ```unlock host://* ```
 * to break a lock not owned by you, use ```lock --force ...```

### ``` ignore -m "ignore reason" <service_uri> [<service_uri> ...]``` 
 * ignores a services, assuming all operations on that service as successfull
 * needed when it is known that a service could not be accessed temporarily
 * example: nagios server down, ignore all nagios checks

    ```ignore -m "server down" service://*/nagios```

### ``` unignore <service_uri> [<service_uri> ...]``` 
 * unignoring services on host


## Getting Things Done, Part 2: Parallel Actions
The parallel option ```-p``` is available for all commands acting on multiple components 
(e.g. start/stop/update/lock/...):

* ```-p <p-spec>``` parallel execution according to p-spec

Formats of the p-spec:

* ```-p <number>``` use ```number``` parallel workers for each plan (even
  nested ones)

  example: start all services with 10 parallel workers
  
  ``` start service://* -p 10```

* ```-p "<plan>=<items>_<workers>_<errors>"``` 

  * plan: name of the subplan (use ```-n``` to see the actionplan)
  * items: number of items in the given plan to apply the following parameters
  * workers: number of parallel executions on given items
  * errors: tolerated errors during execution
  * an asterisk ```*``` translates to *up to all remaining items*

  example: during an update, start all unaffected services as fast as possible
  (or: in parallel)
  
  ```update -n -p "update/prestart=*_*_0"```

  *Note:* only the prestart plan gets executed in parallel, all other plans
  (notably the /update/stopupdate/start plan) gets executed sequentially.

* ```-p "<plan>=<items>_<workers>_<errors>[:<items>_<workers>_<errors>[...]] [<plan>=...]"```
  * more complex specification
  * splits a plan in severall parallel plans, configures multiple plans


* Complex Example: Pilot Phase Updates
  * try an update on the first chunk, fail on any error
  * try an update on the next 5 chunks with 2 workers, fail on 2nd error
  * update all remaining chunks with 10 workers, fail on an error rate &gt;10%

  ```update -n -p "update/prestart=*_*_0
  update/stopupdatestart=1_1_0:5_2_1:*_10_10%"```

