import os

from front_base.config import ConfigBase

import utils
import env_info
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

module_data_path = os.path.join(env_info.data_path, 'gae_proxy')


headers = {"connection": "close"}


class Config(ConfigBase):
    def __init__(self, fn):
        super(Config, self).__init__(fn)

        # globa setting level
        # passive < conservative < normal < radical < extreme
        self.set_var("setting_level", "normal")

        # proxy
        self.set_var("listen_ip", "127.0.0.1")
        self.set_var("listen_port", 8087)

        # auto range
        self.set_var("AUTORANGE_THREADS", 10)
        self.set_var("AUTORANGE_MAXSIZE", 512 * 1024)
        # if mobile:
        #     self.set_var("AUTORANGE_MAXBUFFERSIZE", 10 * 1024 * 1024 / 8)
        # else:
        self.set_var("AUTORANGE_MAXBUFFERSIZE", 20 * 1024 * 1024)
        self.set_var("JS_MAXSIZE", 0)

        # gae
        self.set_var("GAE_PASSWORD", "")
        self.set_var("GAE_VALIDATE", 1)

        # host rules
        self.set_var("hosts_direct", [
            #b"docs.google.com",
            #"play.google.com",
            #b"scholar.google.com",
            #"scholar.google.com.hk",
            #b"appengine.google.com"
        ])
        self.set_var("hosts_direct_endswith", [
            #b".gvt1.com",
            b".appspot.com"
        ])

        self.set_var("hosts_gae", [
            b"accounts.google.com",
            b"mail.google.com"
        ])

        self.set_var("hosts_gae_endswith", [
            b".googleapis.com"
        ])

        # sites using br
        self.set_var("BR_SITES", [
            b"webcache.googleusercontent.com",
            b"www.google.com",
            b"www.google.com.hk",
            b"www.google.com.cn",
            b"fonts.googleapis.com"
        ])

        self.set_var("BR_SITES_ENDSWITH", [
            b".youtube.com",
            b".facebook.com",
            b".googlevideo.com"
        ])

        # some unsupport request like url length > 2048, will go Direct
        self.set_var("google_endswith", [
            b".youtube.com",
            b".googleapis.com",
            b".google.com",
            b".googleusercontent.com",
            b".ytimg.com",
            b".doubleclick.net",
            b".google-analytics.com",
            b".googlegroups.com",
            b".googlesource.com",
            b".gstatic.com",
            b".appspot.com",
            b".gvt1.com",
            b".android.com",
            b".ggpht.com",
            b".googleadservices.com",
            b".googlesyndication.com",
            b".2mdn.net"
        ])

        # front
        self.set_var("front_continue_fail_num", 10)
        self.set_var("front_continue_fail_block", 0)

        # http_dispatcher
        self.set_var("dispather_min_idle_workers", 3)
        self.set_var("dispather_work_min_idle_time", 0)
        self.set_var("dispather_work_max_score", 1000)
        self.set_var("dispather_min_workers", 20)
        self.set_var("dispather_max_workers", 50)
        self.set_var("dispather_max_idle_workers", 15)

        self.set_var("max_task_num", 80)

        # http 1 worker
        self.set_var("http1_first_ping_wait", 5)
        self.set_var("http1_idle_time", 200)
        self.set_var("http1_ping_interval", 0)

        # http 2 worker
        self.set_var("http2_max_concurrent", 20)
        self.set_var("http2_target_concurrent", 1)
        self.set_var("http2_max_timeout_tasks", 1)
        self.set_var("http2_timeout_active", 0)
        self.set_var("http2_ping_min_interval", 0)

        # connect_manager
        self.set_var("https_max_connect_thread", 10)
        self.set_var("ssl_first_use_timeout", 5)
        self.set_var("connection_pool_min", 1)
        self.set_var("https_connection_pool_min", 0)
        self.set_var("https_connection_pool_max", 10)
        self.set_var("https_new_connect_num", 3)
        self.set_var("https_keep_alive", 10)

        # check_ip
        self.set_var("check_ip_host", "xxnet-1.appspot.com")
        self.set_var("check_ip_accept_status", [200, 500, 503])
        self.set_var("check_ip_content", b"GoAgent")

        # host_manager
        self.set_var("GAE_APPIDS", [])

        # connect_creator
        self.set_var("check_pkp", [
# Expired CAs
# GIAG2
# GIAG3
# GTSGIAG3
# GIAG3ECC

# GIAG4
# https://pki.goog/repo/certs/giag4.pem
# GIAG4x
# https://pki.goog/repo/certs/giag4x.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvSw7AnhsoyYa5z/crKtt
B52X+R0ld3UdQBU4Yc/4wmF66cpHeEOMSmhdaY5RzYrowZ6kG1xXLrSoVUuudUPR
fg/zjRqv/AAVDJFqc8OnhghzaWZU9zlhtRgY4lx4Z6pDosTuR5imCcKvwqiDztOJ
r4YKHuk23p3cxu1zDnUsuN+cm4TkVtI1SsuSc9t1uErBvFIcW6v3dLcjrPkmwE61
udZQlBDHJzCFwrhXLtXLlmuSA5/9pOuWJ+U3rSgS7ICSfa83vkBe00ymjIZT6ogD
XWuFsu4edue27nG8g9gO1YozIUCV7+zExG0G5kxTovis+FJpy9hIIxSFrRIKM4DX
aQIDAQAB
-----END PUBLIC KEY-----
''',
# GIAG4 ECC
# https://pki.goog/repo/certs/giag4ecc.pem
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEWgDxDsTP7Od9rB8TPUltMacYCHYI
NthcDjlPu3wP0Csmy6Drit3ghqaTqFecqcgks5RwcKQkT9rbY3e8lHuuAw==
-----END PUBLIC KEY-----
''',
# GTS CA 1C3
# https://pki.goog/repo/certs/gts1c3.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA9Yjf52KMHjf4N0KQf2yH
0PtlgiX96MtrpP9t6Voj4pn2HOmSA5kTfAkKivpC1l5WJKp6M4Qf0elpu7l07FdM
ZmiTdzdVU/45EE23NLtfJXc3OxeU6jzlndW8w7RD6y6nR++wRBFj2LRBhd1BMEiT
G7+39uBFAiHglkIXz9krZVY0ByYEDaj9fcou7+pIfDdNPwCfg9/vdYQueVdc/Fdu
Gpb//Iyappm+Jdl/liwG9xEqAoCA62MYPFBJh+WKyl8ZK1mWgQCg+1HbyncLC8mW
T+9wScdcbSD9mbS04soud/0t3Au2axMMjBkrF5aYufCL9qAnu7bjjVGPva7Hm7GJ
nQIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 1D2
# https://pki.goog/repo/certs/gts1d2.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAstl74eHXPxyRcv/5EM2H
FXl0tz5Hi7JhVf0MNsZ+d0I6svpSWwtxgdZN1ekrJE0jXosrcl8hVbUp70TL64JS
qz4npJJJQUreqN0x4DzfbXpNLdZtCbAO42Hysv6QbFp7EGRJtAs8CPLqeQxsphqJ
alYyoCmiMIKPgVEM86K52XW5Ip4nFLpKLyxjWIfxXRDmX5G7uVvMR+IedbaMj8x1
XVcF54LGhA50cirLO1X1bnDrZmnDJLs4kzWbaGEvm9aupndyfHFIWDMQr+mAgh21
B0Ab9j3soq1HnbSUKTSzjC/NJQNYNcAlpFVf4bMHVj3I0GO4IPuMHUMs+Pmp1exv
lwIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 1D4
# https://pki.goog/repo/certs/gts1d4.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq8Cqo8ITbuXTD3MLx1M8
gTz1sD7FOYNobvLtV9Dhz6Y5aGVR5tRCkrTK/avrvxEkTErQdYON6r6csgc3USbm
PqsBFmLGbJFKOEhHQo5A8YExSV2xrO0ggns7SD/zaqP+8YOX//e3i1OrGJGEtCdM
tcl14H7YOGR1TogiDHrA3sTk1xQfdFyx6NyqPynlKPX28GbqLUWGosbKaEwWuhZV
QY7fG0gf3V2yDLh4Upx8pUtYrejbX3RDQub9KIqYttEnkC7jLV64UmbYkz14HzgW
SpreK+tdZR5W3J7QJB0q+xjYWRrO/G3G+6wsnMtZgeTnnNxEBpwMDZJ4S0FtB8PW
qwIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 1O1
# https://pki.goog/repo/certs/gts1o1.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0BjPRdSLzdOc5EDvfrTd
aSEbyc88jkx1uQ8xGYQ9njwp71ANEJNvBYCAnyqgvRJLAuE9n1gWJP4wnwt0d1WT
HUv3TeGSghD2UawMw7IilA80a5gQSecLnYM53SDGHC3v0RhhZecjgyCoIxL/0iR/
1C/nRGpbTddQZrCvnkJjBfvgHMRjYa+fajP/Ype9SNnTfBRn3HXcLmno+G14adC3
EAW48THCOyT9GjN0+CPg7GsZihbG482kzQvbs6RZYDiIO60ducaMp1Mb/LzZpKu8
3Txh15MVmO6BvY/iZEcgQAZO16yX6LnAWRKhSSUj5O1wNCyltGN8+aM9g9HNbSSs
BwIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 1P5
# https://pki.goog/repo/certs/gts1p5.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs4LwJIy/LYevstmnrvrK
ukTWWz7+sveyZRbc3hDoTy0QWFoohoeh7mqzoNl1T3+hUgGLVahKWwZIyDYSJauJ
+fIjX51gZflc2r466FxtfZzQhBiFMM1Om+w82LPhltTzxQtl24+wdMv2HvN48ayV
xd1zwzGIga90qm/9DOMFlfDFEE9lY/qgr8YYPcWh35d51wWJszCwdK49khBrjBV3
3QsEV/uBA93qIjTV5Vay8MSNQbHDAtti7IDQ/3bUhuQEGra2DCticX3Zr9nxXvrA
HsqgGVxV8IDRKgwHhpCfNeMoK1vvI8ijHaSjOu7+g9yCTCWwTcVRrZ6b01uEwhpa
6QIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 2A1
# https://pki.goog/repo/certs/gts2a1.pem
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEAN+bsxmjxoOPZBA3MIh/CdD/J31/
5vRh3MdletXO0zD+TrcD4wZPMrVdMsX4tiPtyzI/rYEiaaJFIBfAXqKIiA==
-----END PUBLIC KEY-----
''',
# GTS Root R1 Cross
# https://pki.goog/repo/certs/gtsr1x.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAthECix7joXebO9y/lD63
ladAPKH9gvl9MgaCcfb2jH/76Nu8ai6Xl6OMS/kr9rH5zoQdsfnFl97vufKj6bwS
iV6nqlKr+CMny6SxnGPb15l+8Ape62im9MZaRw1NEDPjTrETo8gYbEvs/AmQ351k
KSUjB6G00j0uYODP0gmHu81I8E3CwnqIiru6z1kZ1q+PsAewnjHxgsHA3y6mbWwZ
DrXYfiYaRQM9sHmklCitD38m5agI/pboPGiUU+6DOogrFZYJsuB6jC511pzrp1Zk
j5ZPaK49l8KEj8C8QMALXL32h7M1bKwYUH+E4EzNktMg6TO8UpmvMrUpsyUqtEj5
cuHKZPfmghCN6J3Cioj6OGaK/GP5Afl4/Xtcd/p2h/rs37EOeZVXtL0m79YB0esW
CruOC7XFxYpVq9Os6pFLKcwZpDIlTirxZUTQAs6qzkm06p98g7BAe+dDq6dso499
iYH6TKX/1Y7DzkvgtdizjkXPdsDtQCv9Uw+wp9U7DbGKogPeMa3Md+pvez7W35Ei
Eua++tgy/BBjFFFy3l3WFpO9KWgz7zpm7AeKJt8T11dleCfeXkkUAKIAf5qoIbap
sZWwpbkNFhHax2xIPEDgfg1azVY80ZcFuctL7TlLnMQ/0lUTbiSw1nH69MG6zO0b
9f6BQdgAmD06yK56mDcYBZUCAwEAAQ==
-----END PUBLIC KEY-----
''',
# GTS Y1
# https://pki.goog/repo/certs/gtsy1.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv72WKaCDZTTnN6KC5yhi
aDZLawHdgu2zIhpeHogZBdpibue99PU8V26a17//FpbCHzCLBxq8IDnAcIGBtOkG
J+QfHcUow/iFccLDQrhN4YlHl4hhEAaejqXKBy3U+NN2De/rfdDB/QX+38MZnfrx
cLudTgS8ItVbmA9kC/8wnGGrMbLvC7KhJk6aPspN8hXzmjfEHnz3Y9O64eu9QBou
47trCZspr6bXqW/XZV/b/KiOlsprLR4pobkd4gOkrLSNMTsRcrTHh/4SCPYLR6QV
oIZ1K2cmLhJHuxYTOy7ziG0sQmvku/Sh+GeU2Pakm3wSPubxQFDofYs8AQ2dZYfw
YQIDAQAB
-----END PUBLIC KEY-----
''',
# GTS Y2
# https://pki.goog/repo/certs/gtsy2.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqB9XbHMq4soQmRpOVF9C
snIPC2uZ3ITR0QRReBLhOY3sWwjeBctqqMcocN0zg+30c4+UVAcOdAxHjEpVakbr
tcqfF71wrhau8o6sn+y8MrdYAtrGrYzns26KETX8NIzxJy/v31wJOQnW/WZEizes
4JfO/1Mo3qWAiaoctsiHmL5PG8xQkdOhPNdHu6KcgO0IsJ9BCCufd9TpJMb0EnO1
WK3WZLQdgmVny5FkEqp0Fz5TgQKekHyajnbujf1T09AGzTQgO0Btz15WL9pkMADM
WKwYtbEurJaHrAgejMHWC7KjaqH3XlVmFMJs3rDDIQxyTRLBPqRLaiUkzxvBBnmr
lwIDAQAB
-----END PUBLIC KEY-----
''',
# GTS Y3
# https://pki.goog/repo/certs/gtsy3.pem
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE8rfkbjTwx1dixmkxk3b8dhsNCYRC
npKv6jT9gnu5BtJlK3kG/l57HRM9E1/GwErnpBxDBnkLeee+Qb3VxGWHsw==
-----END PUBLIC KEY-----
''',
# GTS Y4
# https://pki.goog/repo/certs/gtsy4.pem
b'''\
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEqPJbOoggUvyliF5Us9hq047KDrKP
9uViYwR13jjZCM4rgkOdciVuN0w8zuxzFnQWaY0r085HwQKAr8rGsbJYdg==
-----END PUBLIC KEY-----
''',
# Google CA1
# https://pki.goog/repo/certs/tp_googleca1.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAupYx7NU9sbeWxSISCARB
GUNj/YKmUpoFxnM+cFwU98Qm3TWk+QkkbgWN7ScBqBHKHqwHt6OZvkhCEbV3D7C2
iDknM8riJdR45f9mDzHUiO12AHyxqao54PrSGvIukBCxU0BO8UV8zg/ZDFUoRPL6
4Pk9xWld9Thzlwts6Bi6CkjZ6HM5EiFiiIcOSvx8tGIHc0/ncBBjsop/ceRK6415
ReXKpyFHEEqH42P64XrGdDYSVli0jZhUDQoHCCjZxIpAagLYM5pryVvdWBGTvH4n
0j0uzPIM8riC+XYyHKnpW/JgargXADBQvIRwRNwEuvfvTVa4JIlPhCYwMo4qLzhx
vQIDAQAB
-----END PUBLIC KEY-----
''',
# GTS CA 1D3
# https://pki.goog/repo/certs/tp_gtsca1d3.pem
b'''\
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsUX4++gDvlpQYGaFi9Jm
omOPfqAsDVJBCLMQa8Ox2vBPsdd7ZqzqiVJquTRnSWNnOJBSuzf+RDZuEZz9eS5k
Z19DcwrRU/aIKEhPBcnui7Z//JZpHBF6ai89CXpChanZXbX6I9ylVomPI9+uuTb6
3RUAy6++1I/FdU/G/YTVNbJHsHXyBSHm7C537EPXowAH5zQZ8t18IoLuPVBrQpDV
KvBVMdT9Wc21fvPvrkEY+Il/6Z8NXL/kUmAMxsSsulpUBwEUKe+1haRtGMsM6DZh
N3Tphr+AwTioLnSvaNDyqo+zfpJeXsoiwFLH+Y6YsP6R5IjVBzUoimFgeWeTSbYP
YQIDAQAB
-----END PUBLIC KEY-----
'''
        ])
        #self.set_var("check_commonname", "Google")
        self.set_var("min_intermediate_CA", 2)
        self.set_var("support_http2", 1)

        # ip_manager
        self.set_var("max_scan_ip_thread_num", 10)
        self.set_var("max_good_ip_num", 100)
        self.set_var("target_handshake_time", 600)

        # ip source
        self.set_var("use_ipv6", "auto") #force_ipv4/force_ipv6/auto
        self.set_var("ipv6_scan_ratio", 90) # 0 - 100

        # Check local network
        self.set_var("check_local_network_rules", "normal")  # normal, force_ok, force_fail

        self.load()

    def load(self):
        super(Config, self).load()

        need_save = 0
        if not os.path.isfile(self.config_path):
            for fn in [
                os.path.join(module_data_path, "config.ini"),
                os.path.join(module_data_path, "manual.ini")
            ]:
                need_save += self.load_old_config(fn)

        self.HOSTS_GAE = tuple(utils.to_bytes(self.hosts_gae))
        self.HOSTS_DIRECT = tuple(utils.to_bytes(self.hosts_direct))
        self.HOSTS_GAE_ENDSWITH = tuple(utils.to_bytes(self.hosts_gae_endswith))
        self.HOSTS_DIRECT_ENDSWITH = tuple(utils.to_bytes(self.hosts_direct_endswith))
        self.GOOGLE_ENDSWITH = tuple(utils.to_bytes(self.google_endswith))

        self.br_sites = tuple(utils.to_bytes(self.BR_SITES))
        self.br_endswith = tuple(utils.to_bytes(self.BR_SITES_ENDSWITH))

        # there are only hundreds of GAE IPs, we don't need a large threads num
        self.max_scan_ip_thread_num = min(self.max_scan_ip_thread_num, 200)

        if need_save:
            self.save()

    def load_old_config(self, fn):
        if not os.path.isfile(fn):
            return 0

        need_save = 0
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
                        need_save += 1
                    except Exception as e:
                        pass
                elif line.startswith("password"):
                    password = line.split("=")[1].strip()
                    self.GAE_PASSWORD = password
                    need_save += 1

        return need_save

    def set_level(self, level=None):
        if level is None:
            level = self.setting_level
        elif level in ["passive", "conservative", "normal", "radical", "extreme"]:
            self.setting_level = level

            if level == "passive":
                self.dispather_min_idle_workers = 0
                self.dispather_work_min_idle_time = 0
                self.dispather_work_max_score = 1000
                self.dispather_min_workers = 5
                self.dispather_max_workers = 30
                self.dispather_max_idle_workers = 5
                self.max_task_num = 50
                self.https_max_connect_thread = 10
                self.https_keep_alive = 5
                self.https_connection_pool_min = 0
                self.https_connection_pool_max = 10
                self.max_scan_ip_thread_num = 10
                self.max_good_ip_num = 60
                self.target_handshake_time = 600
            elif level == "conservative":
                self.dispather_min_idle_workers = 1
                self.dispather_work_min_idle_time = 0
                self.dispather_work_max_score = 1000
                self.dispather_min_workers = 10
                self.dispather_max_workers = 30
                self.dispather_max_idle_workers = 10
                self.max_task_num = 50
                self.https_max_connect_thread = 10
                self.https_keep_alive = 15
                self.https_connection_pool_min = 0
                self.https_connection_pool_max = 10
                self.max_scan_ip_thread_num = 10
                self.max_good_ip_num = 100
                self.target_handshake_time = 600
            elif level == "normal":
                self.dispather_min_idle_workers = 3
                self.dispather_work_min_idle_time = 0
                self.dispather_work_max_score = 1000
                self.dispather_min_workers = 20
                self.dispather_max_workers = 50
                self.dispather_max_idle_workers = 15
                self.max_task_num = 80
                self.https_max_connect_thread = 10
                self.https_keep_alive = 15
                self.https_connection_pool_min = 0
                self.https_connection_pool_max = 10
                self.max_scan_ip_thread_num = 10
                self.max_good_ip_num = 100
                self.target_handshake_time = 600
            elif level == "radical":
                self.dispather_min_idle_workers = 3
                self.dispather_work_min_idle_time = 1
                self.dispather_work_max_score = 1000
                self.dispather_min_workers = 30
                self.dispather_max_workers = 70
                self.dispather_max_idle_workers = 25
                self.max_task_num = 100
                self.https_max_connect_thread = 15
                self.https_keep_alive = 15
                self.https_connection_pool_min = 1
                self.https_connection_pool_max = 15
                self.max_scan_ip_thread_num = 20
                self.max_good_ip_num = 100
                self.target_handshake_time = 1200
            elif level == "extreme":
                self.dispather_min_idle_workers = 5
                self.dispather_work_min_idle_time = 5
                self.dispather_work_max_score = 1000
                self.dispather_min_workers = 45
                self.dispather_max_workers = 100
                self.dispather_max_idle_workers = 40
                self.max_task_num = 130
                self.https_max_connect_thread = 20
                self.https_keep_alive = 15
                self.https_connection_pool_min = 2
                self.https_connection_pool_max = 20
                self.max_scan_ip_thread_num = 30
                self.max_good_ip_num = 200
                self.target_handshake_time = 1500

            self.save()
            self.load()


class DirectConfig(object):
    def __init__(self, config):
        self._config = config
        self.set_default()

    def __getattr__(self, attr):
        return getattr(self._config, attr)

    def dummy(*args, **kwargs):
        pass

    set_var = save = load = dummy

    def set_level(self, level=None):
        if level is None:
            level = self.setting_level

        if level == "passive":
            self.dispather_min_idle_workers = 0
            self.dispather_work_min_idle_time = 0
            self.dispather_work_max_score = 1000
            self.dispather_min_workers = 0
            self.dispather_max_workers = 8
            self.dispather_max_idle_workers = 0
            self.max_task_num = 16
            self.https_max_connect_thread = 4
            self.https_connection_pool_min = 0
            self.https_connection_pool_max = 6
        elif level == "conservative":
            self.dispather_min_idle_workers = 1
            self.dispather_work_min_idle_time = 0
            self.dispather_work_max_score = 1000
            self.dispather_min_workers = 1
            self.dispather_max_workers = 8
            self.dispather_max_idle_workers = 2
            self.max_task_num = 16
            self.https_max_connect_thread = 5
            self.https_connection_pool_min = 0
            self.https_connection_pool_max = 8
        elif level == "normal":
            self.dispather_min_idle_workers = 2
            self.dispather_work_min_idle_time = 0
            self.dispather_work_max_score = 1000
            self.dispather_min_workers = 3
            self.dispather_max_workers = 8
            self.dispather_max_idle_workers = 3
            self.max_task_num = 16
            self.https_max_connect_thread = 6
            self.https_connection_pool_min = 0
            self.https_connection_pool_max = 10
        elif level == "radical":
            self.dispather_min_idle_workers = 3
            self.dispather_work_min_idle_time = 1
            self.dispather_work_max_score = 1000
            self.dispather_min_workers = 5
            self.dispather_max_workers = 10
            self.dispather_max_idle_workers = 5
            self.max_task_num = 20
            self.https_max_connect_thread = 6
            self.https_connection_pool_min = 1
            self.https_connection_pool_max = 10
        elif level == "extreme":
            self.dispather_min_idle_workers = 5
            self.dispather_work_min_idle_time = 5
            self.dispather_work_max_score = 1000
            self.dispather_min_workers = 5
            self.dispather_max_workers = 15
            self.dispather_max_idle_workers = 5
            self.max_task_num = 30
            self.https_max_connect_thread = 10
            self.https_connection_pool_min = 1
            self.https_connection_pool_max = 10

    set_default = set_level


config_path = os.path.join(module_data_path, "config.json")
config = Config(config_path)
direct_config = DirectConfig(config)

