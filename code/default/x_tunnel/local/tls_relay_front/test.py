#!/usr/bin/env python2
# coding:utf-8

import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
front_path = os.path.abspath( os.path.join(current_path, os.pardir))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
module_data_path = os.path.join(data_path, 'x_tunnel')
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


def t1():
    content, status, response = tls_relay.front.request("GET", "scan1.xx-net.net", timeout=1000)
    print(status)

    tls_relay.front.stop()


if __name__ == '__main__':
    try:
        t1()
    except KeyboardInterrupt:
        import sys

        sys.exit()
