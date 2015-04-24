#!/usr/bin/env python2
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import yaml


def get_launcher_version_from_config():
    config_path = os.path.abspath( os.path.join(current_path, os.pardir, 'data', 'launcher', 'config.yaml'))
    if not os.path.isfile(config_path):
        return False

    try:
        config = yaml.load(open(config_path, 'r'))
        launcher_version = config["modules"]["launcher"]["current_version"]
        return launcher_version
    except yaml.YAMLError as exc:
        print "Error in configuration file:", exc
    except Exception as e:
        print "get_launcher_version_from_config:", e

    return False

def scan_launcher_version():
    for filename in os.listdir(current_path):
        if os.path.isdir(os.path.join(current_path, filename)):
            return filename
    return False

def create_data_path():
    data_path = os.path.abspath( os.path.join(current_path, os.pardir, 'data'))
    if not os.path.isdir(data_path):
        os.mkdir(data_path)

    data_launcher_path = os.path.abspath( os.path.join(current_path, os.pardir, 'data', 'launcher'))
    if not os.path.isdir(data_launcher_path):
        os.mkdir(data_launcher_path)

    data_goagent_path = os.path.abspath( os.path.join(current_path, os.pardir, 'data', 'goagent'))
    if not os.path.isdir(data_goagent_path):
        os.mkdir(data_goagent_path)

def main():
    create_data_path()

    launcher_version = get_launcher_version_from_config()
    if not launcher_version or not os.path.isdir(os.path.join(current_path, launcher_version)):
        launcher_version = scan_launcher_version()
    print "launcher version:", launcher_version
    launcher_path = os.path.join(current_path, launcher_version)
    sys.path.insert(0, launcher_path)
    from start import main as launcher_main
    launcher_main()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
