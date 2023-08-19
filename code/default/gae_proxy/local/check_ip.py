#!/usr/bin/env python2
# coding:utf-8

import sys
import os
import threading

current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

if __name__ == "__main__":
    sys.path.append(default_path)

    noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath(os.path.join(default_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.abspath(os.path.join(default_path, 'lib', 'linux'))
        sys.path.append(linux_lib)
    elif sys.platform == "darwin":
        darwin_lib = os.path.abspath(os.path.join(default_path, 'lib', 'darwin'))
        sys.path.append(darwin_lib)
        extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python"
        sys.path.append(extra_lib)


import env_info

module_data_path = os.path.join(env_info.data_path, 'gae_proxy')
import xlog
logger = xlog.getLogger("gae_proxy")

from xx_six import ConnectionError, ConnectionResetError, BrokenPipeError

from front_base.openssl_wrap import SSLContext
from front_base.connect_creator import ConnectCreator
import front_base.check_ip

from gae_proxy.local.config import config
from gae_proxy.local.host_manager import HostManager


class CheckIp(front_base.check_ip.CheckIp):
    def check_response(self, response):
        server_type = response.headers.get(b'Server', b"")
        if isinstance(server_type, list):
            server_type = server_type[0]
        self.logger.debug("status:%d", response.status)
        self.logger.debug("Server type:%s", server_type)

        if response.status not in self.config.check_ip_accept_status:
            return False

        if response.status in [503, 500]:
            # out of quota
            if b"gws" not in server_type and b"Google Frontend" not in server_type and b"GFE" not in server_type:
                xlog.warn("%d but server type:%s", response.status, server_type)
                return False
            else:
                return True

        try:
            content = response.read()
        except Exception as e:
            if sys.version_info[0] == 3 and (
                    isinstance(e, ConnectionError) or
                    isinstance(e, ConnectionResetError) or
                    isinstance(e, BrokenPipeError)
            ):
                return False

            self.logger.warn("app check except:%r", e)
            return False

        if self.config.check_ip_content not in content:
            self.logger.warn("app check content:%s", content)
            return False

        return True


class CheckAllIp(object):

    def __init__(self):
        ca_certs = os.path.join(current_path, "cacert.pem")
        openssl_context = SSLContext(
            logger, ca_certs=ca_certs,
            cipher_suites=[b'ALL', b"!RC4-SHA", b"!ECDHE-RSA-RC4-SHA", b"!ECDHE-RSA-AES128-GCM-SHA256",
                           b"!AES128-GCM-SHA256", b"!ECDHE-RSA-AES128-SHA", b"!AES128-SHA"]
        )
        host_manager = HostManager()
        connect_creator = ConnectCreator(logger, config, openssl_context, host_manager,
                                         debug=True)
        self.check_ip = CheckIp(logger, config, connect_creator)

        self.lock = threading.Lock()

        self.in_fd = open("ipv6_list.txt", "r")
        self.out_fd = open(
            os.path.join(module_data_path, "ipv6_list.txt"),
            "w"
        )

    def get_ip(self):
        with self.lock:
            while True:
                line = self.in_fd.readline()
                if not line:
                    raise Exception()

                try:
                    ip = line.split()[0]
                    return ip
                except:
                    continue

    def write_ip(self, ip, host, handshake):
        with self.lock:
            self.out_fd.write("%s %s gws %d 0 0\n" % (ip, host, handshake))
            self.out_fd.flush()

    def checker(self):
        while True:
            try:
                ip = self.get_ip()
            except Exception as e:
                xlog.info("no ip left")
                return

            try:
                res = self.check_ip.check_ip(ip)
            except Exception as e:
                xlog.warn("check except:%r", e)
                continue

            if not res or not res.ok:
                xlog.debug("ip:%s fail", ip)
                continue

            if res.h2:
                self.write_ip(ip, res.domain, res.handshake_time)

    def run(self):
        for i in range(0, 100):
            threading.Thread(target=self.checker, name="gae_ip_checker").start()


def check_all():
    check = CheckAllIp()
    check.run()
    exit(0)


if __name__ == "__main__":
    # check_all()

    # case 1: only ip
    # case 2: ip + domain
    #    connect use domain

    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "142.250.66.180"

    xlog.info(("test ip:%s" % ip))

    if len(sys.argv) > 2:
        top_domain = sys.argv[2]
    else:
        top_domain = None

    if len(sys.argv) > 3:
        wait_time = int(sys.argv[3])
    else:
        wait_time = 0

    ca_certs = os.path.join(current_path, "cacert.pem")
    openssl_context = SSLContext(
        logger, ca_certs=ca_certs,
        protocol="TLSv1_2"
        # cipher_suites=[b'ALL', b"!RC4-SHA", b"!ECDHE-RSA-RC4-SHA", b"!ECDHE-RSA-AES128-GCM-SHA256",
        #               b"!AES128-GCM-SHA256", b"!ECDHE-RSA-AES128-SHA", b"!AES128-SHA"]
    )
    host_manager = HostManager(config, logger)
    connect_creator = ConnectCreator(logger, config, openssl_context, host_manager,
                                     debug=True)
    check_ip = CheckIp(logger, config, connect_creator)

    res = check_ip.check_ip(ip, host=top_domain, wait_time=wait_time)
    if not res:
        xlog.info("connect fail")
    elif res.ok:
        xlog.info(("success, domain:%s handshake:%d" % (res.host, res.handshake_time)))
    else:
        xlog.info("not support")
