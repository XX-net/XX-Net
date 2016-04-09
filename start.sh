#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH

# launch xx-net service by ignore hungup signal
function launchWithNoHungup() {
	if hash python2 2>/dev/null; then
	    nohup python2 launcher/start.py 2&> /dev/null &
	else
	    nohup python launcher/start.py 2&> /dev/null &
	fi
}

# launch xx-net service by hungup signal
function launchWithHungup() {
	if hash python2 2>/dev/null; then
	    python2 launcher/start.py
	else
	    python launcher/start.py
	fi
}

# get operating system name
os_name=`uname -s`

# Darwin for os x
if [ $os_name = 'Darwin' ];then
	launchWithNoHungup
else
	launchWithHungup
fi