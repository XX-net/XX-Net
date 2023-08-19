#!/usr/bin/env python2
# coding:utf-8

import os
import sys
import time

current_path = os.path.dirname(os.path.abspath(__file__))
front_path = os.path.abspath( os.path.join(current_path, os.pardir))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir))
python_path = root_path

sys.path.append(root_path)
sys.path.append(front_path)

noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform.startswith("linux"):
    linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)
elif sys.platform == "darwin":
    darwin_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(darwin_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python"
    sys.path.append(extra_lib)

import tls_relay_front as tls_relay
from xlog import getLogger
xlog = getLogger("tls_relay")
import env_info

data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')


def t1():
    content, status, response = tls_relay.front.request("GET", "scan1.xx-net.org", timeout=1000)
    print(status)

    tls_relay.front.stop()


def get_dns():
    start_time = time.time()
    # content, status, response = front.request("GET", "scan1.xx-net.org", "/", timeout=10)
    content, status, response = tls_relay.front.request("GET", "dns.xx-net.org", path="/query?domain=www.google.com")

    time_cost = time.time() - start_time
    xlog.info("GET cost:%f", time_cost)
    xlog.info("status:%d content:%s", status, content)
    tls_relay.front.stop()


if __name__ == '__main__':
    try:
        # t1()
        get_dns()
    except KeyboardInterrupt:
        import sys

        sys.exit()
