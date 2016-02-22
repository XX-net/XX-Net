#!/bin/bash

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPTPATH

if hash python3 2>/dev/null; then
    python3 launcher/start.py
else
    python launcher/start.py
fi
