import os
import shutil

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))

from xlog import getLogger
xlog = getLogger("launcher")
from config import config


def check():
    import update_from_github
    current_version = update_from_github.current_version()
    last_run_version = config.last_run_version
    if last_run_version == "0.0.0":
        postUpdateStat = "isNew"
    elif last_run_version != current_version:
        postUpdateStat = "isPostUpdate"
        run(last_run_version)
    else:
        return
    config.postUpdateStat = postUpdateStat
    config.last_run_version = current_version
    config.save()


def run(last_run_version):
    if config.auto_start == 1:
        import autorun
        autorun.enable()

    if os.path.isdir(os.path.join(top_path, 'launcher')):
        shutil.rmtree(os.path.join(top_path, 'launcher'))  # launcher is for auto-update from 2.X
