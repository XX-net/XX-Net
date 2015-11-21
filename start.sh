#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Please run as root"
    exit 1
fi

SCRIPTPATH=`dirname "${BASH_SOURCE[0]}"`
cd $SCRIPTPATH

if hash python2 2>/dev/null; then
    python2 launcher/start.py
else
    python launcher/start.py
fi
