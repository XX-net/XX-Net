#!/usr/bin/env python2
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import yaml

current_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath( os.path.join(current_path, os.pardir, 'data', 'launcher', 'config.yaml'))

config = {}

try:
    config = yaml.load(file(data_path, 'r'))
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc


launcher_version = config["modules"]["launcher"]["current_version"]

import subprocess
start_script = os.path.abspath( os.path.join(current_path, launcher_version, "start.py"))
subprocess.call([sys.executable, start_script], shell=False)
