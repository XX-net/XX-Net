
import cloudflare_front.apis as cloudflare_apis
#import heroku_front.apis as heroku_apis

from xlog import getLogger
xlog = getLogger("x_tunnel")

apis = [cloudflare_apis]


def set_proxy(args):
    xlog.info("set_proxy:%s", args)
    for api in apis:
        try:
            api.set_proxy(args)
        except Exception as e:
            xlog.exception("set_proxy except:%r", e)