#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH

if hash python2 2>/dev/null; then
    python2 launcher/start.py
else
    python launcher/start.py
fi
