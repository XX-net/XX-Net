
import os
import shutil
import time


from xlog import getLogger
xlog = getLogger("gae_proxy")
from config import config

class Scan_ip_log():
    max_lines_per_log_file = 3000

    def __init__(self):
        self.log_path = os.path.join(config.DATA_PATH, "scan_ip.log")
        self.open_log()

    def get_log_content(self):
        if not os.path.isfile(self.log_path):
            return ""

        with open(self.log_path, "r") as fd:
            content = fd.read()
            return content

    def open_log(self):
        if os.path.isfile(self.log_path):
            with open(self.log_path, "r") as fd:
                lines = fd.readlines()
                line_num = len(lines)
            if line_num >= self.max_lines_per_log_file:
                self.roll_log()

        self.log_fd = open(self.log_path, "a")

    def roll_log(self):
        for i in range(1000):
            file_name = os.path.join(config.DATA_PATH, "scan_ip.%d.log" % i)
            if os.path.isfile(file_name):
                continue

            xlog.info("scan_ip_log roll %s -> %s", self.log_path, file_name)
            shutil.move(self.log_path, file_name)
            return

    def log(self, level, fmt, *args, **kwargs):
        string = '%s - [%s] %s\n' % (time.ctime()[4:-5], level, fmt % args)
        #print string
        #sys.stderr.write(string)
        self.log_fd.write(string)
        try:
            self.log_fd.flush()
        except:
            pass

    def debug(self, fmt, *args, **kwargs):
        self.log('DEBUG', fmt, *args, **kwargs)

    def info(self, fmt, *args, **kwargs):
        self.log('INFO', fmt, *args)

    def warn(self, fmt, *args, **kwargs):
        self.log('WARNING', fmt, *args, **kwargs)

scan_ip_log = Scan_ip_log()


if __name__ == '__main__':
    scan_ip_log.info("ADD abc")
    scan_ip_log.info("ADD ab1")
    scan_ip_log.info("ADD ab2")
    scan_ip_log.info("ADD ab3")