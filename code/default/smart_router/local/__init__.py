import os
import sys
import json
import apis

from xlog import getLogger
xlog = getLogger("smart_router")

current_path = os.path.dirname(os.path.abspath(__file__))
launcher_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, "launcher"))

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data', "smart_router"))
if launcher_path not in sys.path:
    sys.path.append(launcher_path)

try:
    from module_init import proc_handler
except:
    xlog.info("launcher not running")
    proc_handler = None


from . import global_var as g
import dns_server
import redirect_server
import xconfig


dns_srv = None
redirect_srv = None
ready = False


def remote_query_dns(domain, type):
    content, status, response = g.x_tunnel.front_dispatcher.request(
        "GET", "dns.xx-net.net", path="/query?domain=%s" % (domain), timeout=5)

    if status != 200:
        xlog.warn("remote_query_dns fail status:%d", status)
        return []

    try:
        rs = json.loads(content)
        return rs["ip"]
    except Exception as e:
        xlog.warn("remote_query_dns json:%s parse fail:%s", content, e)
        return []


def load_config():
    global g
    if not os.path.isdir(data_path):
        os.mkdir(data_path)

    config_path = os.path.join(data_path, 'config.json')
    config = xconfig.Config(config_path)
    config.set_var("dns_port", 53)
    config.set_var("redirect_port", 8083)
    config.set_var("bind_ip", "127.0.0.1")
    config.set_var("cache_size", 200)
    config.set_var("ttl", 24*3600)
    config.set_var("redirect_to", "x_tunnel")
    config.load()

    g.config = config


def redirect_handler(sock, host, port, client_address):
    if g.config.redirect_to == "x_tunnel":
        return g.x_tunnel.proxy_handler.redirect_handler(sock, host, port, client_address)
    elif g.config.redirect_to == "gae_proxy":
        return g.gae_proxy.proxy_handler.redirect_handler(sock, host, port, client_address)
    else:
        xlog.error("redirect_to:%s not exist", g.config.redirect_to)
        return


def run():
    global proc_handler, ready, dns_srv, g, redirect_srv

    if not proc_handler:
        return False

    load_config()

    if "gae_proxy" in proc_handler:
        g.gae_proxy = proc_handler["gae_proxy"]["imp"].local
    else:
        xlog.debug("gae_proxy not running")

    if "x_tunnel" in proc_handler:
        g.x_tunnel = proc_handler["x_tunnel"]["imp"].local
    else:
        xlog.debug("x_tunnel not running")

    redirect_srv = redirect_server.RedirectHandler(bind_ip=g.config.bind_ip, port=g.config.redirect_port,
                                                   handler=redirect_handler)
    redirect_srv.start()

    dns_srv = dns_server.DnsServer(bind_ip=g.config.bind_ip, port=g.config.dns_port, query_cb=remote_query_dns,
                                   cache_size=g.config.cache_size, ttl=g.config.ttl)
    ready = True
    dns_srv.server_forever()


def terminate():
    global ready
    dns_srv.stop()
    redirect_srv.stop()
    ready = False
