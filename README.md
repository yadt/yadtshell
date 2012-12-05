# [YADTSHELL](http://yadt-project.org) [![Build Status](https://secure.travis-ci.org/yadt/yadtshell.png?branch=master)](http://travis-ci.org/yadt/yadtshell)

The yadtshell controls yadt-clients via ssh, handles service dependencies and package updates.

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
