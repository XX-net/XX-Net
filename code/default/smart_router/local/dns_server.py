#!/usr/bin/env python
# coding:utf-8

import json
import os
import sys
import threading
import socket
import time
import re
import select
import collections
import random

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.join(top_path, "data", 'smart_router')

python_path = os.path.join(root_path, 'python27', '1.0')
noarch_lib = os.path.join(python_path, 'lib', 'noarch')
sys.path.append(noarch_lib)

import simple_queue
import utils
from dnslib import DNSRecord, DNSHeader, A, AAAA, RR, DNSQuestion, QTYPE

import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")


def remote_query_dns(domain, type=None):
    if not g.x_tunnel:
        return []

    content, status, response = g.x_tunnel.front_dispatcher.request(
        "GET", "dns.xx-net.net", path="/query?domain=%s" % (domain), timeout=5)

    if status != 200:
        xlog.warn("remote_query_dns fail status:%d", status)
        return []

    try:
        rs = json.loads(content)
        return rs["ip"]
    except Exception as e:
        xlog.warn("remote_query_dns json:%s parse fail:%s", content, e)
        return []


class DnsServerList(object):
    def __init__(self):
        self.local_list = self.get_dns_server()

        if g.config.country_code == "CN":
            self.public_list = ['114.114.114.114', "180.76.76.76", "198.15.67.245", "202.46.32.19", "64.214.116.84"]
        else:
            self.public_list = ['8.8.8.8', "208.67.222.222", "209.244.0.3", "8.26.56.26", "37.235.1.174", "91.239.100.100"]

        self.i = 0

    def get_dns_server(self):
        iplist = []
        if os.name == 'nt':
            import ctypes, ctypes.wintypes, struct, socket
            DNS_CONFIG_DNS_SERVER_LIST = 6
            buf = ctypes.create_string_buffer(2048)
            ctypes.windll.dnsapi.DnsQueryConfig(DNS_CONFIG_DNS_SERVER_LIST, 0, None, None, ctypes.byref(buf),
                                                ctypes.byref(ctypes.wintypes.DWORD(len(buf))))
            ipcount = struct.unpack('I', buf[0:4])[0]
            iplist = [socket.inet_ntoa(buf[i:i + 4]) for i in xrange(4, ipcount * 4 + 4, 4)]
        elif os.path.isfile('/etc/resolv.conf'):
            with open('/etc/resolv.conf', 'rb') as fp:
                iplist = re.findall(r'(?m)^nameserver\s+(\S+)', fp.read())

        out_list = []
        for ip in iplist:
            if ip == "127.0.0.1":
                continue
            out_list.append(ip)
            xlog.debug("use local DNS server:%s", ip)

        return out_list

    def get_local(self):
        return self.local_list[self.i]

    def reset_server(self):
        self.i = 0

    def next_server(self):
        self.i += 1
        if self.i >= len(self.local_list):
            self.i = self.i % len(self.local_list)

        xlog.debug("next dns server:%s", self.get_local())

    def get_public(self):
        return random.choice(self.public_list)


class DnsClient(object):
    def __init__(self):
        self.start()

    def start(self):
        self.waiters = {}

        self.dns_server = DnsServerList()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)

        self.running = True
        self.th = threading.Thread(target=self.recv_worker)
        self.th.start()

    def stop(self):
        self.running = False

    def recv_worker(self):
        while self.running:
            try:
                response, server = self.sock.recvfrom(8192)
                server, port = server
            except Exception as e:
                # xlog.exception("sock.recvfrom except:%r", e)
                continue

            if not response:
                continue

            try:
                p = DNSRecord.parse(response)
            except Exception as e:
                xlog.exception("parse response fail:%r", e)
                continue

            if len(p.questions) == 0:
                xlog.warn("received response without question")
                continue

            id = p.header.id

            if id not in self.waiters:
                continue

            que = self.waiters[id]
            org_domain = que.domain
            domain = str(p.questions[0].qname)
            xlog.debug("recev %s from:%s domain:%s org:%s", len(p.rr), server, domain, org_domain)
            ips = []
            for r in p.rr:
                ip = str(r.rdata)
                if r.rtype == 5:
                    # CNAME
                    xlog.debug("local dns %s recv %s cname:%s from:%s", org_domain, domain, ip, server)
                    d = DNSRecord(DNSHeader(id))
                    d.add_question(DNSQuestion(ip, QTYPE.A))
                    req_pack = d.pack()

                    self.sock.sendto(req_pack, (server, 53))

                    d = DNSRecord()
                    d.add_question(DNSQuestion(ip, QTYPE.AAAA))
                    req_pack = d.pack()

                    self.sock.sendto(req_pack, (server, 53))
                    continue

                if "." in ip and g.ip_region.check_ip(ip):
                    cn = g.ip_region.cn
                else:
                    cn = "XX"
                ips.append(ip+"|"+cn)

            if len(ips):
                g.domain_cache.set_ips(org_domain, ips)
            que.notify_all()

        xlog.info("DNS Client recv worker exit.")
        self.sock.close()

    def send_request(self, id, domain, server):
        try:
            d = DNSRecord(DNSHeader(id))
            d.add_question(DNSQuestion(domain, QTYPE.A))
            req4_pack = d.pack()

            d = DNSRecord()
            d.add_question(DNSQuestion(domain, QTYPE.AAAA))
            req6_pack = d.pack()

            self.sock.sendto(req4_pack, (server, 53))
            # xlog.debug("send req:%s to:%s", domain, server)

            self.sock.sendto(req6_pack, (server, 53))
            # xlog.debug("send req:%s to:%s", domain, server)
        except Exception as e:
            xlog.warn("request dns except:%r", e)

    def query(self, domain, timeout=3):
        end_time = time.time() + timeout
        id = random.randint(0, 65535)
        que = simple_queue.Queue()
        que.domain = domain

        ips = []
        if "." not in domain:
            server_list = self.dns_server.local_list
        else:
            server_list = self.dns_server.public_list

        for ip in server_list:
            if time.time() > end_time:
                break

            self.send_request(id, domain, ip)

            self.waiters[id] = que
            que.wait(time.time() + 1)
            ips = g.domain_cache.get_ips(domain)
            if len(ips):
                break
            if "." in domain:
                continue
            else:
                break

        if id in self.waiters:
            del self.waiters[id]

        return ips


class DnsServer(object):
    def __init__(self, bind_ip="127.0.0.1", port=53, ttl=24*3600):
        self.bind_ip = bind_ip
        self.port = port
        self.ttl = ttl
        self.th = None

        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.serverSock.bind((bind_ip, self.port))
            xlog.info("start DNS server at %s:%d", self.bind_ip, self.port)
            self.running = True
            self.sockets = [self.serverSock]
        except Exception as e:
            self.running = False
            xlog.warn("bind DNS %s:%d fail", bind_ip, port)

            import platform
            value = platform.platform()
            if "x86" in value or "i686" in value or "amd64" in value:
                xlog.warn("You can try: install libcap2-bin")
                xlog.warn("Then: sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python2.7")
                xlog.warn("Or run XX-Net as root")
            elif "mips" in value:
                xlog.warn("Router platform")

    def in_country(self, ips):
        for ip_cn in ips:
            ipcn_p = ip_cn.split("|")
            ip = ipcn_p[0]
            cn = ipcn_p[1]
            if cn == g.config.country_code:
                return True
        return False

    def query(self, domain, type=None):
        if utils.check_ip_valid(domain):
            return [domain]

        ips = g.domain_cache.get_ordered_ips(domain, type)
        if ips:
            return ips

        rule = g.user_rules.check_host(domain, 0)
        if rule == "black":
            ips = ["127.0.0.1|XX"]
            xlog.debug("DNS query:%s in black", domain)
            return ips

        if rule == "direct" or \
                (g.config.auto_direct and not g.gfwlist.check(domain)):
            ips = g.dns_client.query(domain, timeout=1)

        if not ips or not self.in_country(ips):
            if "." in domain:
                ips = remote_query_dns(domain, type)
                g.domain_cache.set_ips(domain, ips, type)

                if not ips or self.in_country(ips):
                    if g.config.auto_direct or g.user_rules.check_host(domain, 0) == "direct":
                         ips = g.dns_client.query(domain)
            else:
                ips = ["127.0.0.1|XX"]
                g.domain_cache.set_ips(domain, ips, type)

        return ips

    def on_udp_query(self, req_data, addr):
        start_time = time.time()
        try:
            request = DNSRecord.parse(req_data)
            if len(request.questions) != 1:
                xlog.warn("query num:%d %s", len(request.questions), request)
                return

            domain = str(request.questions[0].qname)
            if domain.endswith("."):
                domain = domain[:-1]

            type = request.questions[0].qtype
            if type not in [1, 28]:
                xlog.warn("query:%s type:%d", domain, type)

            xlog.debug("DNS query:%s type:%d from %s", domain, type, addr)

            ips = self.query(domain, type)
            if not ips:
                xlog.debug("query:%s type:%d from:%s, get fail, cost:%d", domain, type, addr,
                           (time.time() - start_time) * 1000)
                return

            reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=1, auth=1), q=request.q)
            for ip_cn in ips:
                ipcn_p = ip_cn.split("|")
                ip = ipcn_p[0]
                if "." in ip and type == 1:
                    reply.add_answer(RR(domain, ttl=60, rdata=A(ip)))
                elif ":" in ip and type == 28:
                    reply.add_answer(RR(domain, rtype=type, ttl=60, rdata=AAAA(ip)))
            res_data = reply.pack()

            self.serverSock.sendto(res_data, addr)
            xlog.debug("query:%s type:%d from:%s, return ip num:%d cost:%d", domain, type, addr,
                       len(reply.rr), (time.time()-start_time)*1000)
        except Exception as e:
            xlog.exception("on_query except:%r", e)

    def server_forever(self):
        while self.running:
            r, w, e = select.select(self.sockets, [], [], 1)
            for rsock in r:
                data, addr = rsock.recvfrom(1024)
                threading.Thread(target=self.on_udp_query, args=(data, addr)).start()

        self.serverSock.close()
        self.sockets = []
        self.th = None
        xlog.info("dns_server stop")

    def start(self):
        self.th = threading.Thread(target=self.server_forever)
        self.th.start()

    def stop(self):
        self.running = False
        while self.th:
            time.sleep(1)


if __name__ == '__main__':
    r = remote_query_dns("apple.com")
    print(r)