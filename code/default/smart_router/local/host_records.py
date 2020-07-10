import os
import threading
import time
import collections
import operator

from . import global_var as g

import utils
from xlog import getLogger
xlog = getLogger("smart_router")


def is_network_ok(ip):
    if not g.gae_proxy:
        return False

    return g.gae_proxy.check_local_network.is_ok(ip)


class DomainRecords(object):
    # File Format:
    # ===============
    # host $rule gae_acceptable [ip|CN,ip|CN ip_update_time]
    # rule: direct, gae, socks, black, other
    # gae_acceptable: 0 or 1, default 1
    # CN: country name

    # Cache struct
    # ==============
    # "r": rule
    # "g": gae_acceptable
    # "dns": { dns_type: [ip], ..}
    # "update": $ip_update_time

    def __init__(self, file_path, capacity=1000, ttl=3600):
        self.file_path = file_path
        self.capacity = capacity
        self.ttl = ttl
        self.cache = collections.OrderedDict()
        self.last_save_time = time.time()
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.need_save = False
        self.load()

        self.running = True

    def _get(self, domain):
        with self.lock:
            try:
                record = self.cache[domain]

                time_now = time.time()
                if time_now - record["update"] > self.ttl:
                   record = None
            except KeyError:
                record = None

            if not record:
                record = {"r": "unknown", "dns": {}, "g": 1, "query_count": 0}
            #self.cache[domain] = record
            return record

    def _set(self, domain, record):
        with self.lock:
            try:
                self.cache.pop(domain)
            except KeyError:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)

            record["update"] = time.time()
            self.cache[domain] = record
            self.need_save = True
            self.last_update_time = time.time()

    def clean(self):
        with self.lock:
            self.cache = collections.OrderedDict()
        self.save(True)

    def get_content(self):
        socks_lines = []
        gae_lines = []
        direct_lines = []
        with open(self.file_path, "r") as fd:
            for line in fd.readlines():
                if not line:
                    continue
                try:
                    lp = line.split()
                    if len(lp) < 2:
                        continue

                    rule = lp[1]
                    if rule == "socks":
                        socks_lines.append(line)
                    elif rule == "gae":
                        gae_lines.append(line)
                    else:
                        direct_lines.append(line)
                except Exception as e:
                    xlog.warn("rule line:%s fail:%r", line, e)
                    continue
        return "".join(socks_lines + gae_lines + direct_lines)

    def load(self):
        if not os.path.isfile(self.file_path):
            return

        with self.lock:
            with open(self.file_path, "r") as fd:
                for line in fd.readlines():
                    if not line:
                        continue

                    try:
                        lp = line.split()
                        if len(lp) == 3:
                            domain = lp[0]
                            rule = lp[1]
                            gae_acceptable = int(lp[2])
                            record = {"r": rule, "ip": {}, "g":gae_acceptable}
                        elif len(lp) == 5:
                            domain = lp[0]
                            rule = lp[1]
                            gae_acceptable = int(lp[2])

                            record = {"r": rule, "ip":{}, "g":gae_acceptable}
                        else:
                            xlog.warn("rule line:%s fail", line)
                            continue
                    except Exception as e:
                        xlog.warn("rule line:%s fail:%r", line, e)
                        continue

                    self.cache[domain] = record

    def save(self, force=False):
        time_now = time.time()
        if not force:
            if not self.need_save:
                return

            if time_now - self.last_save_time < 10:
                return

        with self.lock:
            with open(self.file_path, "w") as fd:
                for host, record in self.cache.items():
                    line = utils.to_str(host) + " " + record["r"] + " " + str(record["g"]) + " "

                    fd.write(line + "\n")

        self.last_save_time = time.time()
        self.need_save = False

    def set_ips(self, domain, ips, dns_type):
        if not ips:
            return ips

        record = self._get(domain)

        if dns_type not in record["dns"]:
            record["dns"][dns_type] = ips
        else:
            for ip in ips:
                if ip in record["dns"][dns_type]:
                    continue
                record["dns"][dns_type].append(ip)

        self._set(domain, record)

    def get_ips(self, domain, dns_type=None):
        if domain not in self.cache:
            return []

        record = self._get(domain)
        if not dns_type:
            dns_types = [1, 28]
        else:
            dns_types = [dns_type]

        ips = []
        for dns_type in dns_types:
            if dns_type not in record["dns"]:
                continue
            ips += record["dns"][dns_type]

        return ips

    def update_rule(self, domain, rule):
        record = self._get(domain)
        record["r"] = rule
        return self._set(domain, record)

    def get_rule(self, domain):
        record = self._get(domain)
        return record["r"]

    def report_gae_deny(self, domain, port=None):
        record = self._get(domain)
        record["g"] = 0
        return self._set(domain, record)

    def accept_gae(self, domain, port=None):
        record = self._get(domain)
        return record["g"]

    def get_query_count(self, domain):
        record = self._get(domain)
        return record["query_count"]

    def add_query_count(self, domain):
        record = self._get(domain)
        record["query_count"] += 1
        self._set(domain, record)


class IpRecord(object):
    # File Format:
    # =============
    # ip $rule $connect_time $update_time
    # rule: direct, gae, socks, black, other
    # connect_time: -1(fail times), n>=0 connect time cost in ms.
    # default: IPv4 6000, IPv6 4000
    # fail: 7000 + (fail time * 1000)

    # IPv6 will try first if IPv6 exist.

    # Cache struct
    # ==============
    # "r": rule
    # "c": $connect_time
    # "update": $update_time

    def __init__(self, file_path, capacity=1000, ttl=3600):
        self.file_path = file_path
        self.capacity = capacity
        self.ttl = ttl
        self.cache = collections.OrderedDict()
        self.last_save_time = time.time()
        self.lock = threading.Lock()
        self.last_update_time = 0
        self.need_save = False
        self.load()

        self.running = True

    def get(self, ip):
        with self.lock:
            record = None
            try:
                record = self.cache.pop(ip)
                self.cache[ip] = record
            except KeyError:
                pass
            return record

    def set(self, ip, record):
        with self.lock:
            try:
                self.cache.pop(ip)
            except KeyError:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)

            self.cache[ip] = record
            self.need_save = True
            self.last_update_time = time.time()

    def clean(self):
        with self.lock:
            self.cache = collections.OrderedDict()
        self.save(True)

    def get_content(self):
        with open(self.file_path, "r") as fd:
            content = fd.read()
            return content

    def load(self):
        if not os.path.isfile(self.file_path):
            return

        with self.lock:
            with open(self.file_path, "r") as fd:
                for line in fd.readlines():
                    if not line:
                        continue

                    lp = line.split()
                    if len(lp) != 4:
                        xlog.warn("rule line:%s fail", line)
                        continue

                    ip = lp[0]
                    rule = lp[1]
                    connect_time = int(lp[2])
                    update_time = int(lp[3])
                    self.cache[ip] = {"r": rule, "c": connect_time, "update": update_time}

    def save(self, force=False):
        if not force:
            if not self.need_save:
                return

            if time.time() - self.last_save_time < 10:
                return

        with self.lock:
            with open(self.file_path, "w") as fd:
                for ip in self.cache:
                    record = self.cache[ip]
                    rule = record["r"]
                    connect_time = record["c"]
                    update_time = record["update"]

                    fd.write("%s %s %d %d\n" % (ip, rule, connect_time, update_time))

        self.last_save_time = time.time()
        self.need_save = False

    def get_connect_time(self, ip, port=None):
        record = self.get(ip)
        if not record or time.time() - record["update"] > self.ttl:
            if b"." in ip:
                return 6000
            else:
                return 4000
        else:
            return record["c"]

    def update_rule(self, ip, port, rule):
        record = self.get(ip)
        if b"." in ip:
            connect_time = 6000
        else:
            connect_time = 4000

        if not record:
            record = {"r": rule, "c": connect_time}
        else:
            record["r"] = rule

        record["update"] = time.time()
        return self.set(ip, record)

    def update_connect_time(self, ip, port, connect_time):
        record = self.get(ip)
        if not record:
            record = {"r": "direct", "c": connect_time}
        else:
            record["c"] = connect_time
        record["update"] = time.time()
        return self.set(ip, record)

    def report_connect_fail(self, ip, port):
        if not is_network_ok(ip):
            return

        record = self.get(ip)
        if not record:
            record = {"r": "direct", "c": 7000}
        else:
            if record["c"] <= 7000:
                record["c"] = 7000
            else:
                record["c"] += 1000
        record["update"] = time.time()
        return self.set(ip, record)