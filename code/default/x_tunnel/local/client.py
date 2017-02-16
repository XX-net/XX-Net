import os
import sys
import threading

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

noarch_lib = os.path.abspath(os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
data_xtunnel_path = os.path.join(data_path, 'x_tunnel')

lib_path = os.path.abspath(os.path.join(current_path, os.pardir, 'common'))
sys.path.append(lib_path)

ready = False
# don't remove, launcher web_control need it.


def create_data_path():
    if not os.path.isdir(data_path):
        os.mkdir(data_path)

    if not os.path.isdir(data_xtunnel_path):
        os.mkdir(data_xtunnel_path)


create_data_path()

from xlog import getLogger

log_file = os.path.join(data_xtunnel_path, "client.log")
xlog = getLogger("x_tunnel", buffer_size=500, file_name=log_file)

import xconfig
from proxy_handler import Socks5Server
import global_var as g
import proxy_session
import simple_http_server

import web_control
# don't remove, launcher web_control need it.


def load_config():
    if len(sys.argv) > 2 and sys.argv[1] == "-f":
        config_path = sys.argv[2]
    else:
        config_path = os.path.join(data_xtunnel_path, 'client.json')

    xlog.info("use config_path:%s", config_path)

    config = xconfig.Config(config_path)

    config.set_var("log_level", "DEBUG")
    config.set_var("write_log_file", 0)

    config.set_var("encrypt_data", 0)
    config.set_var("encrypt_password", "encrypt_pass")
    config.set_var("encrypt_method", "aes-256-cfb")

    config.set_var("api_server", "http://center.xx-net.net:8888/")
    config.set_var("server_host", "")
    config.set_var("server_port", 0)
    config.set_var("use_https", 0)
    config.set_var("port_range", 1)

    config.set_var("login_account", "")
    config.set_var("login_password", "")

    # can use gae_proxy "127.0.0.1", 8087
    config.set_var("http_proxy_host", "127.0.0.1")
    config.set_var("http_proxy_port", 8087)

    config.set_var("conn_life", 30)

    config.set_var("socks_host", "127.0.0.1")
    config.set_var("socks_port", 1080)

    # performance parameters
    # range 2 - 100
    config.set_var("concurent_thread_num", 20)

    # range 1 - 1000
    config.set_var("send_delay", 100)
    # max 10M
    config.set_var("block_max_size", 256 * 1024)
    # range 1 - 60
    config.set_var("roundtrip_timeout", 120)

    config.load()

    config.windows_size = config.block_max_size * config.concurent_thread_num
    config.windows_ack = 0.2 * config.windows_size

    if config.write_log_file:
        xlog.log_to_file(os.path.join(data_path, "client.log"))

    xlog.setLevel(config.log_level)
    g.config = config

    if g.config.http_proxy_host and g.config.http_proxy_port:
        xlog.info("Use proxy:%s:%d", g.config.http_proxy_host, g.config.http_proxy_port)
        g.proxy = (g.config.http_proxy_host, g.config.http_proxy_port)
    else:
        g.proxy = None


def start():
    if not g.server_host or not g.server_port:
        if g.config.server_host and g.config.server_port:
            xlog.info("Session Server:%s:%d", g.config.server_host, g.config.server_port)
            g.server_host = g.config.server_host
            g.server_port = g.config.server_port
            g.balance = 99999999
        elif g.config.api_server:
            if not (g.config.login_account and g.config.login_password):
                xlog.debug("x-tunnel no account")
            else:
                res, reason = proxy_session.request_balance(g.config.login_account, g.config.login_password)
                if not res:
                    xlog.warn("request_balance fail when start:%s", reason)
        else:
            xlog.debug("please check x-tunnel server in config")

    g.session = proxy_session.ProxySession()


def terminate():
    global ready
    if g.socks5_server:
        xlog.info("Close Socks5 server ")
        g.socks5_server.server_close()
        g.socks5_server.shutdown()
        g.socks5_server = None

    if g.session:
        xlog.info("Stopping session")
        g.session.stop()
        g.session = None
    ready = False


def main():
    global ready
    load_config()
    g.cert = os.path.abspath(os.path.join(data_path, "CA.crt"))
    g.data_path = data_path

    start()

    g.socks5_server = simple_http_server.HTTPServer((g.config.socks_host, g.config.socks_port), Socks5Server)
    socks_thread = threading.Thread(target=g.socks5_server.serve_forever)
    socks_thread.setDaemon(True)
    socks_thread.start()

    xlog.info("Socks5 server listen:%s:%d.", g.config.socks_host, g.config.socks_port)

    ready = True
    g.socks5_server.serve_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        #terminate()
        import sys

        sys.exit()
