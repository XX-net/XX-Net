#!/usr/bin/env python2
# coding:utf-8

import os
import sys
import time

if __name__ == '__main__':
    current_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir))
    data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
    data_gae_proxy_path = os.path.join(data_path, 'x_tunnel')
    python_path = os.path.abspath( os.path.join(root_path, 'python27', '1.0'))

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




from xlog import getLogger
xlog = getLogger("cloudflare_front")
xlog.set_buffer(2000)

import connect_control
import http_dispatcher


class Front():
    def __init__(self):
        self.dispatchs = {}

    def request(self, method, host, path, headers, body):
        if host not in self.dispatchs:
            self.dispatchs[host] = http_dispatcher.HttpsDispatcher(host)

        dispatcher = self.dispatchs[host]
        return dispatcher.request(method, host, path, headers, body)

    def get(self, method, host, path, headers, body):
        response = self.request(method, host, path, headers, body)
        length = response.task.content_length
        content = response.task.read(size=length)
        return content


def main():


    xlog.debug("## GAEProxy set keep_running: %s", connect_control.keep_running)
    # to profile gae_proxy, run proxy.py, visit some web by proxy, then visit http://127.0.0.1:8084/quit to quit and print result.

    front = Front()
    response = front.get("GET", "center6.xx-net.net", "/", {}, "")
    print(response)

    while connect_control.keep_running:
        time.sleep(1)

    xlog.info("Exiting gae_proxy module...")
    xlog.debug("## GAEProxy set keep_running: %s", connect_control.keep_running)


if __name__ == '__main__':
    import traceback

    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stdout)
    except KeyboardInterrupt:
        sys.exit()
