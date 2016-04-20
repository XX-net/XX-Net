import os
import sys
import re
import stat
import shutil

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))

from instances import xlog
import config

def older_or_equal(version, reference_version):
    p = re.compile(r'([0-9]+)\.([0-9]+)\.([0-9]+)')
    m1 = p.match(version)
    m2 = p.match(reference_version)
    v1 = map(int, map(m1.group, [1,2,3]))
    v2 = map(int, map(m2.group, [1,2,3]))
    return v1 <= v2

def run(last_run_version):
    if config.get(["modules", "launcher", "auto_start"], 0):
        import autorun
        autorun.enable()

    dirs = []
    files = []
    unix_exec = None

    with open(os.path.join(top_path, 'manifest.txt')) as f:
        for line in f:
            filename = line.rstrip('\n')[2:]
            if line.startswith('D '):
                dirs.append(filename)
            if line.startswith('F '):
                files.append(filename)
            if line.startswith('X '):
                unix_exec = filename
                files.append(filename)

#    if older_or_equal(last_run_version, '3.0.4'):
#        xlog.info("migrating to latest version")
    if dirs and files and unix_exec:
        for filename in os.listdir(top_path):
            filepath = os.path.join(top_path, filename)
            if os.path.isfile(filepath):
                if sys.platform != 'win32' and filename == unix_exec:
                    st = os.stat(filepath)
                    os.chmod(filepath, st.st_mode | stat.S_IEXEC)
                if not filename.startswith('.') and filename not in files:
                    os.remove(filepath)
            else:
                if not filename.startswith('.') and filename not in dirs:
                    shutil.rmtree(filepath)
