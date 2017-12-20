from web_control import user_config
import check_ip
from connect_manager import https_manager
from http_dispatcher import http_dispatch
from config import config
from xlog import getLogger
xlog = getLogger("gae_proxy")


def set_proxy(args):
    xlog.info("set_proxy:%s", args)

    user_config.user_special.proxy_enable = args["enable"]
    user_config.user_special.proxy_type = args["type"]
    user_config.user_special.proxy_host = args["host"]
    try:
        user_config.user_special.proxy_port = int(args["port"])
    except:
        user_config.user_special.proxy_port = 0

    user_config.user_special.proxy_user = args["user"]
    user_config.user_special.proxy_passwd = args["passwd"]

    user_config.save()
    config.load()

    check_ip.load_proxy_config()


def is_workable():
    if http_dispatch.is_idle():
        return True

    num = len(https_manager.new_conn_pool.pool) +\
          len(https_manager.gae_conn_pool.pool) + \
          http_dispatch.h1_num + \
          http_dispatch.h2_num

    if num > 0:
        return True
    else:
        return False


def set_bind_ip(args):
    xlog.info("set_bind_ip:%s", args)

    user_config.LISTEN_IP = args["ip"]
    user_config.save()
