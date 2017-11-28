#!/usr/bin/env python
# coding:utf-8


import os
import sys
import threading
import socket
import collections
import time


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.join(top_path, "data", 'smart_router')

python_path = os.path.join(root_path, 'python27', '1.0')
noarch_lib = os.path.join(python_path, 'lib', 'noarch')
sys.path.append(noarch_lib)


from dnslib import DNSRecord, DNSHeader, A, AAAA, RR
from xlog import getLogger
xlog = getLogger("smart_router")


class DnsCache(object):
    def __init__(self, capacity, ttl):
        self.capacity = capacity
        self.ttl = ttl
        self.cache = collections.OrderedDict()
        # domain => { ipv4: [], ipv6: []}

    def set(self, domain, ips):
        try:
            record = self.cache.pop(domain)
        except KeyError:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            record = {"ipv4": [], "ipv6": []}

        record["update_time"] = time.time()
        for ip in ips:
            if "." in ip:
                if ip not in record["ipv4"]:
                    record["ipv4"].append(ip)

            elif ":" in ip:
                if ip not in record["ipv6"]:
                    record["ipv6"].append(ip)
        self.cache[domain] = record

    def get(self, domain, target_num=100):
        ips4 = []
        ips6 = []

        try:
            record = self.cache.pop(domain)
            if time.time() - record["update_time"] > self.ttl:
                return []

            self.cache[domain] = record

            for ip in record["ipv4"]:
                ips4.append(ip)
                if len(ips4) > target_num:
                    break

            for ip in record["ipv6"]:
                ips6.append(ip)
                if len(ips6) > target_num:
                    break
        except KeyError:
            pass

        return ips4 + ips6

    def remove(self, domain):
        try:
            self.cache.pop(domain)
        except KeyError:
            return


class DnsServer(object):
    def __init__(self, bind_ip="127.0.0.1", port=53, query_cb=None, cache_size=200, ttl=24*3600):
        self.bind_ip = bind_ip
        self.port = port
        self.query_cb = query_cb
        self.cache = DnsCache(cache_size, ttl)
        self.th = None

        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.serverSock.bind((bind_ip, self.port))
            xlog.info("start DNS server at %s:%d", self.bind_ip, self.port)
            self.running = True
        except Exception as e:
            self.running = False
            xlog.warn("bind DNS %s:%d fail", bind_ip, port)

    def stop(self):
        self.running = False

    def query(self, domain, type):
        if not self.query_cb:
            xlog.warn("no query_cb")
            return []

        ips = self.cache.get(domain)
        if not ips:
            ips = self.query_cb(domain, type)
            self.cache.set(domain, ips)

        return ips

    def on_udp_query(self, req_data, addr):
        start_time = time.time()
        try:
            request = DNSRecord.parse(req_data)
            if len(request.questions) != 1:
                xlog.warn("query num:%d %s", len(request.questions), request)
                return

            domain = str(request.questions[0].qname)

            type = request.questions[0].qtype
            if type not in [1, 28]:
                xlog.warn("query:%s type:%d", domain, type)

            # xlog.debug("DNS query:%s type:%d from %s", domain, type, addr)

            ips = self.query(domain, type)

            reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1, auth=1), q=request.q)
            for ip_cn in ips:
                ipcn_p = ip_cn.split("|")
                ip = ipcn_p[0]
                if "." in ip and type == 1:
                    reply.add_answer(RR(domain, ttl=60, rdata=A(ip)))
                elif ":" in ip and type == 28:
                    reply.add_answer(RR(domain, ttl=60, rdata=AAAA(ip)))
            res_data = reply.pack()

            self.serverSock.sendto(res_data, addr)
            xlog.debug("query:%s type:%d from:%s, return ip num:%d cost:%d", domain, type, addr,
                       len(reply.rr), (time.time()-start_time)*1000)
        except Exception as e:
            xlog.exception("on_query except:%r", e)

    def server_forever(self):
        while self.running:
            data, addr = self.serverSock.recvfrom(1024)
            threading.Thread(target=self.on_udp_query, args=(data, addr)).start()

        self.serverSock.close()
        self.th = None
        xlog.info("dns_server stop")

    def start(self):
        self.th = threading.Thread(target=self.server_forever)
        self.th.start()


if __name__ == '__main__':
    dns_server = DnsServer(port=8053)
    try:
        dns_server.server_forever()
    except KeyboardInterrupt:  # Ctrl + C on console
        dns_server.stop()
        os._exit(0)