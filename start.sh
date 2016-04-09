#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH
if python -V | grep -q "Python 3" ;then
    PYTHON="/usr/bin/python2"
else
    PYTHON="python"
fi

${PYTHON} launcher/start.py
