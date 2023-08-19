__all__ = ["local", "start"]


from . import client
from . import apis
from . import web_control


def is_ready():
    return client.ready


def start(args):
    client.start(args)


def stop():
    client.stop()
