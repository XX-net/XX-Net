
import os, sys
import logging

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

import yaml




current_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'data', 'launcher', 'config.yaml'))

config = {}

def load():
    global config, data_path
    try:
        config = yaml.load(file(data_path, 'r'))
        #print yaml.dump(config)
    except yaml.YAMLError, exc:
        print "Error in configuration file:", exc


def save():
    global config, data_path
    try:
        yaml.dump(config, file(data_path, "w"))
    except Exception as e:
        logging.warn("save config %s fail %s", data_path, e)

def main():
    load()
    #config["tax"] = 260
    #save()
    print yaml.dump(config)

if __name__ == "__main__":
    main()