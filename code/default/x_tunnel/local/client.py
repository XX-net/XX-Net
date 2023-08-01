import os
import sys
import json
import platform

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

noarch_lib = os.path.abspath(os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
sys.path.append(root_path)

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
xlog = getLogger("x_tunnel", log_path=data_xtunnel_path, save_start_log=1500, save_warning_log=True)

import os_platform
import xconfig
from x_tunnel.local.proxy_handler import Socks5Server
from x_tunnel.local import global_var as g
from x_tunnel.local import proxy_session
import simple_http_server
from x_tunnel.local import front_dispatcher

from x_tunnel.local import web_control
# don't remove, launcher web_control need it.


def xxnet_version():
    version_file = os.path.join(root_path, "version.txt")
    try:
        with open(version_file, "r") as fd:
            version = fd.read()
        return version
    except Exception as e:
        xlog.exception("get version fail")
    return "get_version_fail"


def get_launcher_uuid():
    launcher_config_fn = os.path.join(data_path, "launcher", "config.json")
    try:
        with open(launcher_config_fn, "r") as fd:
            info = json.load(fd)
            return info.get("update_uuid")
    except Exception as e:
        xlog.exception("get_launcher_uuid except:%r", e)
        return ""


def load_config():
    if len(sys.argv) > 2 and sys.argv[1] == "-f":
        config_path = sys.argv[2]
    else:
        config_path = os.path.join(data_xtunnel_path, 'client.json')

    xlog.info("use config_path:%s", config_path)

    config = xconfig.Config(config_path)

    config.set_var("log_level", "DEBUG")
    config.set_var("upload_logs", True)
    config.set_var("write_log_file", 0)
    config.set_var("save_start_log", 1500)
    config.set_var("show_debug", 0)

    config.set_var("encrypt_data", 0)
    config.set_var("encrypt_password", "encrypt_pass")
    config.set_var("encrypt_method", "aes-256-cfb")

    config.set_var("api_server", "center.xx-net.org")
    config.set_var("scan_servers", ["scan1"])
    config.set_var("server_host", "")
    config.set_var("server_port", 443)
    config.set_var("use_https", 1)
    config.set_var("port_range", 1)

    config.set_var("login_account", "")
    config.set_var("login_password", "")

    config.set_var("conn_life", 30)

    config.set_var("socks_host", "127.0.0.1")
    config.set_var("socks_port", 1080)
    config.set_var("update_cloudflare_domains", True)

    # performance parameters
    # range 2 - 100
    config.set_var("concurent_thread_num", 20)

    # min roundtrip on road if connectoin exist
    config.set_var("min_on_road", 3)

    # range 1 - 1000, ms
    config.set_var("send_delay", 10)

    # range 1 - 20000, ms
    config.set_var("resend_timeout", 5000)

    # range 1 - resend_timeout, ms
    config.set_var("ack_delay", 300)

    # max 10M
    config.set_var("max_payload", 256 * 1024)

    # range 1 - 30
    config.set_var("roundtrip_timeout", 25)

    config.set_var("network_timeout", 10)

    config.set_var("windows_size", 10 * 1024 * 1024)  # will recalulate based on: max_payload * concurent_thread_num *2

    # reporter
    config.set_var("timeout_threshold", 2)
    config.set_var("report_interval", 5 * 60)

    config.set_var("enable_gae_proxy", 0)
    config.set_var("enable_cloudflare", 1)
    config.set_var("enable_cloudfront", 0)
    config.set_var("enable_heroku", 0)
    config.set_var("enable_tls_relay", 1)
    config.set_var("enable_direct", 0)

    config.load()

    config.windows_ack = 0.05 * config.windows_size
    config.windows_size = config.max_payload * config.concurent_thread_num * 2
    xlog.info("X-Tunnel window:%d", config.windows_size)

    if config.write_log_file:
        xlog.log_to_file(os.path.join(data_path, "client.log"))

    xlog.setLevel(config.log_level)
    xlog.set_buffer(200)
    xlog.save_start_log = config.save_start_log
    g.config = config


def main(args):
    global ready

    g.xxnet_version = xxnet_version()
    g.client_uuid = get_launcher_uuid()
    g.system = os_platform.platform + "|" + platform.version() + "|" + str(platform.architecture()) + "|" + sys.version

    load_config()
    front_dispatcher.init()
    g.data_path = data_path

    xlog.info("version:%s", g.xxnet_version)

    g.running = True
    if not g.server_host or not g.server_port:
        if g.config.server_host and g.config.server_port == 443:
            xlog.info("Session Server:%s:%d", g.config.server_host, g.config.server_port)
            g.server_host = g.config.server_host
            g.server_port = g.config.server_port
            g.balance = 99999999
        elif g.config.api_server:
            pass
        else:
            xlog.debug("please check x-tunnel server in config")

    g.http_client = front_dispatcher

    g.session = proxy_session.ProxySession()

    allow_remote = args.get("allow_remote", 0)

    listen_ips = g.config.socks_host
    if isinstance(listen_ips, str):
        listen_ips = [listen_ips]
    else:
        listen_ips = list(listen_ips)

    if allow_remote and ("0.0.0.0" not in listen_ips or "::" not in listen_ips):
        listen_ips = [("0.0.0.0"),]

    for port in range(g.config.socks_port, g.config.socks_port + 10):
        addresses = [(listen_ip, port) for listen_ip in listen_ips]
        try:
            g.socks5_server = simple_http_server.HTTPServer(addresses, Socks5Server, logger=xlog)
        except:
            continue
        xlog.info("Socks5 server listen:%s:%d.", g.config.socks_host, g.config.socks_port)
        break

    ready = True
    g.socks5_server.serve_forever()


def terminate():
    global ready
    g.running = False
    g.http_client.stop()
    front_dispatcher.stop()

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


if __name__ == '__main__':
    try:
        main({})
    except KeyboardInterrupt:
        terminate()
        import sys

        sys.exit()
