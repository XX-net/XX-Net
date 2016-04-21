# Required for auto-update from 2.x, this folder will be automatically deleted once migration to 3.0 is completed.

import os, sys
import subprocess

current_path = os.path.dirname(os.path.abspath(__file__))
start_sript = os.path.abspath(os.path.join(current_path, os.pardir, "code", "default", "launcher", "start.py"))

subprocess.Popen([sys.executable, start_sript])
