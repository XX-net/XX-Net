from web_control import user_config
import check_ip
from config import config
from xlog import getLogger
xlog = getLogger("heroku_front")


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