
from front import front, direct_front
from xlog import getLogger
xlog = getLogger("gae_proxy")


def set_proxy(args):
    front.set_proxy(args)
    direct_front.set_proxy(args)


def is_workable():
    if front.http_dispatcher.is_idle():
        return True

    num = len(front.connect_manager.new_conn_pool.pool) +\
          len(front.connect_manager.gae_conn_pool.pool) + \
          front.http_dispatcher.h1_num + \
          front.http_dispatcher.h2_num

    if num > 0:
        return True
    else:
        return False


def set_bind_ip(args):
    xlog.info("set_bind_ip:%s", args)

    front.config.listen_ip = args["ip"]
    front.config.save()
