#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH

if python -V | grep -q "Python 3" ;then
    PYTHON="python2"
else
    PYTHON="python"
fi



# launch xx-net service by ignore hungup signal
function launchWithNoHungup() {
    nohup ${PYTHON} launcher/start.py 2&> /dev/null &
}

# launch xx-net service by hungup signal
function launchWithHungup() {
    ${PYTHON} launcher/start.py
}

# get operating system name
os_name=`uname -s`

# Darwin for os x
if [ $os_name = 'Darwin' ];then
	launchWithNoHungup
else
	launchWithHungup
fi