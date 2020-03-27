import os
import json

from front_base.host_manager import HostManagerBase

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
module_data_path = os.path.join(data_path, 'x_tunnel')
tls_certs_path = os.path.join(module_data_path, "tls_certs")


class HostManager(HostManagerBase):
    def __init__(self, config_fn):
        self.config_fn = config_fn
        self.info = {}
        self.load()

    def load(self):
        if not os.path.isfile(self.config_fn):
            return

        try:
            with open(self.config_fn, "r") as fd:
                self.info = json.load(fd)
        except:
            pass

    def save(self):
        with open(self.config_fn, "w") as fd:
            json.dump(self.info, fd, indent=2)

    def set_host(self, info):
        self.info = info
        self.save()

    def get_sni_host(self, ip):
        if ip not in self.info:
            return "", ""

        return self.info[ip]["sni"], ""

    def get_info(self, ip_str):
        if ip_str not in self.info:
            raise Exception

        info = self.info[ip_str]
        info["client_key_fn"] = str(os.path.join(tls_certs_path, ip_str + ".key"))
        info["client_ca_fn"] = str(os.path.join(tls_certs_path, ip_str + ".ca"))

        return info

    def reset(self):
        self.info = {}