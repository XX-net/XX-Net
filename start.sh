#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH

if python -V | grep -q "Python 3" ;then
    PYTHON="python2"
else
    PYTHON="python"
fi


if [ -f code/version.txt ]; then
  VERSION=`cat code/version.txt`
else
  VERSION="default"
fi


if [ ! -d "code/$VERSION" ]; then
  VERSION="default"
fi
echo "XX-Net version:$VERSION"


# launch xx-net service by ignore hungup signal
function launchWithNoHungup() {
    nohup ${PYTHON} code/${VERSION}/launcher/start.py 2&> /dev/null &
}

# launch xx-net service by hungup signal
function launchWithHungup() {
    ${PYTHON} code/${VERSION}/launcher/start.py
}

# get operating system name
os_name=`uname -s`

# Darwin for os x
if [ $os_name = 'Darwin' ];then
	PYTHON="/usr/bin/python2.7"
	launchWithNoHungup
else
	launchWithHungup
fi