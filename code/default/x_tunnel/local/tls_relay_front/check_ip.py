#!/usr/bin/env python
# coding:utf-8

import sys
import os


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir))
python_path = root_path

sys.path.append(root_path)

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


import env_info
import xlog
logger = xlog.getLogger("tls_relay")
logger.set_buffer(500)

from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
from front_base.check_ip import CheckIp

from x_tunnel.local.tls_relay_front.config import Config
from x_tunnel.local.tls_relay_front.host_manager import HostManager

data_path = env_info.data_path
module_data_path = os.path.join(data_path, 'x_tunnel')


if __name__ == "__main__":
    # case 1: only ip
    # case 2: ip + domain
    #    connect use domain
    # case 3: ip domain path

    wait_time = 0
    ip = "127.0.0.1:60000"
    top_domain = "agentnobody.pics"
    path = "/"
    headers = {
        "xx-account": "test@xx-net.com",
        "X-Host": "scan1.xx-net.org",
        "X-Path": "/"
    }

    if len(sys.argv) > 1:
        ip = sys.argv[1]
        if len(sys.argv) > 2:
            top_domain = sys.argv[2]
            if len(sys.argv) > 3:
                path += sys.argv[3]
    else:
        print("Usage: check_ip.py [ip] [top_domain] [wait_time=0]")

    print(("test ip:%s" % ip))
    print("sni: %s" % top_domain)
    print("path: %s" % path)

    config_path = os.path.join(module_data_path, "tls_relay.json")
    config = Config(config_path)

    openssl_context = SSLContext(logger)

    host_fn = os.path.join(module_data_path, "tls_host.json")
    host_manager = HostManager(host_fn)
    connect_creator = ConnectCreator(logger, config, openssl_context, host_manager)
    check_ip = CheckIp(logger, config, connect_creator)

    res = check_ip.check_ip(ip, sni=top_domain, host=top_domain, wait_time=wait_time, path=path, headers=headers)
    if not res:
        print("connect fail")
    elif res.ok:
        print(("Check success, domain:%s handshake:%d" % (res.host, res.handshake_time)))
    else:
        print("not support")

    sys.exit(0)
