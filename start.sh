#!/bin/bash

if hash python2 2>/dev/null; then
    python2 launcher/start.py
else
    python launcher/start.py
fi