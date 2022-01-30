import logging
import sys
import os
from subprocess import Popen, PIPE, STDOUT

from logging import getLogger
xlog = getLogger("test")
xlog.setLevel(logging.DEBUG)

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.path.pardir, os.path.pardir))


class T(object):
    def start_xxnet(self):
        py_bin = sys.executable
        start_script = os.path.join(default_path, "launcher", "start.py")
        cmd = [py_bin, start_script]
        xlog.info("cmd: %s" % cmd)
        try:
            self.pth = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT, bufsize=1)  # , preexec_fn=os.setsid
            # for line in stream.stdout:
            for line in iter(self.pth.stdout.readline, b''):
                line = line.strip()
                xlog.info(b"LOG|%s" % line)
                print(line)
                # self.assertNotIn(b"[ERROR]", line)
        except Exception as e:
            xlog.exception("run %s error:%r", cmd, e)

        xlog.info("xxnet exit.")
        self.running = False
        self.th = None


if __name__ == "__main__":
    t = T()
    t.start_xxnet()
