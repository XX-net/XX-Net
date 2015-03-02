#!/bin/bash

SCRIPTPATH=`dirname "${BASH_SOURCE[0]}"`
cd $SCRIPTPATH

if hash python2 2>/dev/null; then
    python2 launcher/start.py
else
    python launcher/start.py
fi