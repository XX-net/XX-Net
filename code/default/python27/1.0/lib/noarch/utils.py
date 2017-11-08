import re
import os
import threading

g_ip_check = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')

def check_ip_valid(ip):
    ret = g_ip_check.match(ip)
    if ret is not None:
        "each item range: [0,255]"
        for item in ret.groups():
            if int(item) > 255:
                return 0
        return 1
    else:
        return 0


def str2hex(data):
    return ":".join("{:02x}".format(ord(c)) for c in data)


def generate_random_lowercase(n):
    min_lc = ord(b'a')
    len_lc = 26
    ba = bytearray(os.urandom(n))
    for i, b in enumerate(ba):
        ba[i] = min_lc + b % len_lc # convert 0..255 to 97..122
    #sys.stdout.buffer.write(ba)
    return ba


class SimpleCondition(object):
    def __init__(self):
        self.lock = threading.Condition()

    def notify(self):
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()

    def wait(self):
        self.lock.acquire()
        self.lock.wait()
        self.lock.release()


def split_domain(host):
    hl = host.split(".")
    return hl[0], ".".join(hl[1:])
