#!/usr/bin/env python

import os




def run_new_start_script():
    import subprocess, sys

    current_path = os.path.dirname(os.path.abspath(__file__))
    start_sript = os.path.abspath( os.path.join(current_path, os.pardir, "start.py"))
    subprocess.Popen([sys.executable, start_sript], shell=False)

def main():

    import time
    time.sleep(2)
    print "setup start run new launcher"
    run_new_start_script()

if __name__ == "__main__":
    main()
