import os

from front_base.config import ConfigBase

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
module_data_path = os.path.join(data_path, 'gae_proxy')


class Config(ConfigBase):
    def __init__(self, fn):
        super(Config, self).__init__(fn)

        # proxy
        self.set_var("listen_ip", "127.0.0.1")
        self.set_var("listen_port", 8087)

        # auto range
        self.set_var("AUTORANGE_THREADS", 20)
        self.set_var("AUTORANGE_MAXSIZE", 548576)
        self.set_var("JS_MAXSIZE", 2097152)

        # gae
        self.set_var("GAE_PASSWORD", "")
        self.set_var("GAE_VALIDATE", 0)

        # host rules
        self.set_var("hosts_direct", [
            "scholar.google.com",
            "scholar.google.com.hk",

        ])
        self.set_var("hosts_gae", [
            "appengine.google.com",
            "accounts.google.com"
        ])

        self.set_var("hosts_direct_endswith", [
            ".appspot.com"
        ])
        self.set_var("hosts_gae_endswith", [])

        # sites using br
        self.set_var("BR_SITES", [
            "webcache.googleusercontent.com",
            "www.google.com",
            "www.google.com.hk",
            "www.google.com.cn",
            "fonts.googleapis.com"
        ])

        self.set_var("BR_SITES_ENDSWITH", [
            ".youtube.com",
            ".facebook.com",
            ".googlevideo.com"
        ])

        # front
        self.set_var("front_continue_fail_num", 10)
        self.set_var("front_continue_fail_block", 0)

        # http_dispatcher
        self.set_var("dispather_min_idle_workers", 10)
        self.set_var("dispather_work_min_idle_time", 0)
        self.set_var("dispather_work_max_score", 200000)
        self.set_var("dispather_max_workers", 90)

        # http 1 worker
        self.set_var("http1_first_ping_wait", 5)
        self.set_var("http1_idle_time", 200)
        self.set_var("http1_ping_interval", 0)

        # http 2 worker
        self.set_var("http2_max_concurrent", 20)
        self.set_var("http2_max_timeout_tasks", 1)
        self.set_var("http2_timeout_active", 0)

        # connect_manager
        self.set_var("https_max_connect_thread", 10)
        self.set_var("ssl_first_use_timeout", 5)
        self.set_var("connection_pool_min", 0)
        self.set_var("https_new_connect_num", 0)
        self.set_var("https_keep_alive", 5)

        # check_ip
        self.set_var("check_ip_host", "xxnet-1.appspot.com")
        self.set_var("check_ip_accept_status", [200, 503])
        self.set_var("check_ip_content", "GoAgent")

        # host_manager
        self.set_var("GAE_APPIDS", [])

        # connect_creator
        self.set_var("check_pkp", [
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnCoEd1zYUJE6BqOC4NhQ
SLyJP/EZcBqIRn7gj8Xxic4h7lr+YQ23MkSJoHQLU09VpM6CYpXu61lfxuEFgBLE
XpQ/vFtIOPRT9yTm+5HpFcTP9FMN9Er8n1Tefb6ga2+HwNBQHygwA0DaCHNRbH//
OjynNwaOvUsRBOt9JN7m+fwxcfuU1WDzLkqvQtLL6sRqGrLMU90VS4sfyBlhH82d
qD5jK4Q1aWWEyBnFRiL4U5W+44BKEMYq7LqXIBHHOZkQBKDwYXqVJYxOUnXitu0I
yhT8ziJqs07PRgOXlwN+wLHee69FM8+6PnG33vQlJcINNYmdnfsOEXmJHjfFr45y
aQIDAQAB
-----END PUBLIC KEY-----
''',
# https://pki.goog/gsr2/GIAG3.crt
# https://pki.goog/gsr2/GTSGIAG3.crt
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAylJL6h7/ziRrqNpyGGjV
Vl0OSFotNQl2Ws+kyByxqf5TifutNP+IW5+75+gAAdw1c3UDrbOxuaR9KyZ5zhVA
Cu9RuJ8yjHxwhlJLFv5qJ2vmNnpiUNjfmonMCSnrTykUiIALjzgegGoYfB29lzt4
fUVJNk9BzaLgdlc8aDF5ZMlu11EeZsOiZCx5wOdlw1aEU1pDbcuaAiDS7xpp0bCd
c6LgKmBlUDHP+7MvvxGIQC61SRAPCm7cl/q/LJ8FOQtYVK8GlujFjgEWvKgaTUHF
k5GiHqGL8v7BiCRJo0dLxRMB3adXEmliK+v+IO9p+zql8H4p7u2WFvexH6DkkCXg
MwIDAQAB
-----END PUBLIC KEY-----
''',
# https://pki.goog/gsr4/GIAG3ECC.crt
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEG4ANKJrwlpAPXThRcA3Z4XbkwQvW
hj5J/kicXpbBQclS4uyuQ5iSOGKcuCRt8ralqREJXuRsnLZo0sIT680+VQ==
-----END PUBLIC KEY-----
'''
        ])
        self.set_var("check_commonname", "Google")
        self.set_var("min_intermediate_CA", 3)

        # ip_manager
        self.set_var("max_scan_ip_thread_num", 1)
        self.set_var("max_good_ip_num", 100)
        self.set_var("target_handshake_time", 600)

        # ip source
        self.set_var("use_ipv6", "auto") #force_ipv4/force_ipv6/auto
        self.set_var("ipv6_scan_ratio", 90) # 0 - 100

        self.load()

    def load(self):
        super(Config, self).load()

        if not os.path.isfile(self.config_path):
            for fn in [
                os.path.join(module_data_path, "config.ini"),
                os.path.join(module_data_path, "manual.ini")
            ]:
                self.load_old_config(fn)

        self.HOSTS_GAE = tuple(self.hosts_gae)
        self.HOSTS_DIRECT = tuple(self.hosts_direct)
        self.HOSTS_GAE_ENDSWITH = tuple(self.hosts_gae_endswith)
        self.HOSTS_DIRECT_ENDSWITH = tuple(self.hosts_direct_endswith)

        self.br_sites = tuple(self.BR_SITES)
        self.br_endswith = tuple(self.BR_SITES_ENDSWITH)

    def load_old_config(self, fn):
        if not os.path.isfile(fn):
            return

        with open(fn, "r") as fd:
            for line in fd.readlines():
                if line.startswith("appid"):
                    try:
                        appid_str = line.split("=")[1]
                        appids = []
                        for appid in appid_str.split("|"):
                            appid = appid.strip()
                            appids.append(appid)
                        self.GAE_APPIDS = appids
                    except Exception as e:
                        pass
                elif line.startswith("password"):
                    password = line.split("=")[1].strip()
                    self.GAE_PASSWORD = password


config_path = os.path.join(module_data_path, "config.json")
config = Config(config_path)