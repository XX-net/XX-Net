__all__ = ["local", "start"]


from . import apis
from . import web_control
from . import client


def is_ready():
    return client.ready


def start(args):
    client.main(args)


def stop():
    client.terminate()
