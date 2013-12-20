# [YADTSHELL](http://yadt-project.org) 

[![Build Status](https://secure.travis-ci.org/yadt/yadtshell.png?branch=master)](http://travis-ci.org/yadt/yadtshell)

[![Build Status](https://drone.io/github.com/yadt/yadtshell/status.png)](https://drone.io/github.com/yadt/yadtshell/latest)

[![PyPI version](https://badge.fury.io/py/yadtshell.png)](https://badge.fury.io/py/yadtshell)


The yadtshell controls hosts with a _yadt-minion_ via ssh, handles service dependencies and package updates.

## Installation with pip
It is considered good practice to install all packages available via pip & easy_install in a
[virtual environment](http://pypi.python.org/pypi/virtualenv) so that your development dependencies are isolated from the system-wide dependencies.
```bash
# create a virtual environment for installation
virtualenv ve
# activate the virtual environment
source ve/bin/activate
# install the yadtshell from the PyPi cheeseshop
pip install yadtshell
```

## Developer setup
This module uses the [pybuilder](http://pybuilder.github.io).
We're running CI builds on [travis-ci](http://travis-ci.org/yadt/yadtshell) and on [drone.io](https://drone.io/github.com/yadt/yadtshell/latest).

```bash
git clone https://github.com/yadt/yadtshell
cd yadtshell
virtualenv venv
. venv/bin/activate
pip install pybuilder
pyb install_dependencies
```
Or you could use [pyb_init](https://github.com/mriehl/pyb_init) and run
```bash
pyb_init https://github.com/yadt/yadtshell
```

## Running the tests
```bash
pyb verify
```

## Generating a setup.py
```bash
pyb
cd target/dist/yadtshell-$VERSION
./setup.py <whatever you want>
```

## Looking at the coverage
```bash
pyb analyze
cat target/reports/coverage
```
