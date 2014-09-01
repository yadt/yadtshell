# [YADTSHELL](http://yadt-project.org)

[![Build Status](https://secure.travis-ci.org/yadt/yadtshell.png?branch=master)](http://travis-ci.org/yadt/yadtshell)
[![Build Status](https://drone.io/github.com/yadt/yadtshell/status.png)](https://drone.io/github.com/yadt/yadtshell/latest)
[![PyPI version](https://badge.fury.io/py/yadtshell.png)](https://badge.fury.io/py/yadtshell)

# try it out

If you want to try out how ```yadt``` works, please check out our [how to](https://github.com/yadt/try-it-yourself) and the [project](http://www.yadt-project.org/) page.

## the Yadt concept

![concept yadtshell and yadtminion](https://raw.githubusercontent.com/yadt/try-it-yourself/master/images/yadtshell_to_yadtminion.png)

The ```yadtshell```(server part) controls hosts with a ```yadt-minion```(client part) via ```passwordless ssh``` with a minimal configuration, it handles service dependencies and package updates.
- A```target``` is a set of hosts which belong together [[wiki](https://github.com/yadt/yadtshell/wiki/Target)]
- A```service``` in yadt is the representation of a service on a host with a LSB compatible init script
- A```service dependency``` is the dependency between two services and its not limited to a service on the same host. (e.g httpd -> loadbalancer) [[wiki](https://github.com/yadt/yadtshell/wiki/Metatargets,-Dependencies-and-Readonly-Services)]

## developer setup
We're running CI builds on [travis-ci](http://travis-ci.org/yadt/yadtshell) and on [drone.io](https://drone.io/github.com/yadt/yadtshell/latest).

### prerequisites
- ```git```
- ```python 2.6/2.7```
- ```python-devel```
- ```virtualenv```

### getting started

```bash
git clone https://github.com/yadt/yadtshell
cd yadtshell
virtualenv venv
. venv/bin/activate
pip install pybuilder
pyb install_dependencies
```

The yadt project is using the pybuilder as a build automation tool for python. The yadtshell project has a clear project structure.

```
├── integrationtest
│   └── python  # here you can find the integration tests, the tests have to end with ```*_tests.py```
├── main
│   ├── python
│   │   └── yadtshell # here you can find the program modules
│   └── scripts # for the executable scripts
└── unittest
    └── python #  here you can find the unit tests, the test have to end with ```*_tests.py```
```

### running the tests
```bash
pyb verify
```

### running code linting

```bash
pyb analyze
```

```
...
All unittests passed.
[INFO]  Executing flake8 on project sources.
[INFO]  Executing frosted on project sources.
[INFO]  Executing jedi linter on project sources.
...
```

### generating a setup.py
```bash
pyb
cd target/dist/yadtshell-$VERSION
./setup.py <whatever you want>
```

### running all tasks together
```bash
pyb
```

## find help

[wiki](https://github.com/yadt/yadtshell/wiki/)

[issues page](https://github.com/yadt/yadtshell/issues)

[twitter](https://twitter.com/yadtproject)
