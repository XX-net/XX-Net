import socket

from front_base.ip_manager import IpManagerBase


class IpManager(IpManagerBase):
    def get_ip(self):
        data = socket.gethostbyname_ex("xxx.heroku.com")
        return data