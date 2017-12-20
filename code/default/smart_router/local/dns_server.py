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

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
data_path = os.path.join(top_path, "data", 'smart_router')

python_path = os.path.join(root_path, 'python27', '1.0')
noarch_lib = os.path.join(python_path, 'lib', 'noarch')
sys.path.append(noarch_lib)

import utils
from dnslib import DNSRecord, DNSHeader, A, AAAA, RR, DNSQuestion, QTYPE

import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")


def remote_query_dns(domain, type):
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


class DnsServer(object):
    def __init__(self, bind_ip="127.0.0.1", port=53, ttl=24*3600):
        self.bind_ip = bind_ip
        self.port = port
        self.ttl = ttl
        self.th = None
        self.local_dns = self.get_dns_server()

        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.serverSock.bind((bind_ip, self.port))
            xlog.info("start DNS server at %s:%d", self.bind_ip, self.port)
            self.running = True
            self.sockets = [self.serverSock]
        except Exception as e:
            self.running = False
            xlog.warn("bind DNS %s:%d fail", bind_ip, port)

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

        if g.config.country_code == "CN":
            iplist += ['114.114.114.114', "180.76.76.76", "198.15.67.245", "202.46.32.19", "64.214.116.84"]
        else:
            iplist += ['8.8.8.8', "208.67.222.222", "209.244.0.3", "8.26.56.26", "37.235.1.174", "91.239.100.100"]

        out_list = []
        for ip in iplist:
            if ip == "127.0.0.1":
                continue
            out_list.append(ip)
            xlog.info("use DNS server:%s", ip)

        return out_list

    def in_country(self, ips):
        for ip_cn in ips:
            ipcn_p = ip_cn.split("|")
            ip = ipcn_p[0]
            cn = ipcn_p[1]
            if cn == g.config.country_code:
                return True
        return False

    def query_local_dns(self, domain, timeout=5):
        start_time = time.time()

        ips = {}
        ipv4_num = 0
        ipv6_num = 0
        return_num = 0
        sock_timeout = 0.1
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except Exception as e:
            xlog.error("query_local_dns e:%r", e)
            return []

        d4 = DNSRecord()
        d4.add_question(DNSQuestion(domain, QTYPE.A))
        req4_pack = d4.pack()

        d6 = DNSRecord()
        d6.add_question(DNSQuestion(domain, QTYPE.AAAA))
        req6_pack = d6.pack()

        try:
            for i in range(0, timeout):
                sock_timeout *= 2
                sock.settimeout(sock_timeout)

                server = self.local_dns[i % len(self.local_dns)]
                sock.sendto(req4_pack, (server, 53))
                sock.sendto(req6_pack, (server, 53))
                # xlog.debug("send req:%s to:%s", domain, server)

                try:
                    response, server_c = sock.recvfrom(8192)
                except Exception as e:
                    if time.time() - start_time > timeout:
                        break
                    else:
                        continue

                p = DNSRecord.parse(response)
                # xlog.debug("recev %s from:%s", len(p.rr), server)

                for r in p.rr:
                    ip = str(r.rdata)
                    if r.rtype == 5:
                        # CNAME
                        d = DNSRecord()
                        d.add_question(DNSQuestion(ip, QTYPE.A))
                        req_pack = d.pack()
                        sock.sendto(req_pack, (server, 53))

                        d = DNSRecord()
                        d.add_question(DNSQuestion(ip, QTYPE.AAAA))
                        req_pack = d.pack()
                        sock.sendto(req_pack, (server, 53))
                        continue

                    if "." in ip:
                        try:
                            socket.inet_aton(ip)
                            # legal
                        except socket.error:
                            # Not legal
                            xlog.warn("query:%s rr:%s", domain, r)
                            continue

                        ipv4_num += 1
                    elif ":" in ip:
                        ipv6_num += 1
                    ips[ip] = 1
                return_num += 1

                if len(ips) > 10 or return_num > 3:
                    break
        except Exception as e:
            xlog.exception("request dns except:%r", e)
        finally:
            sock.close()

        ip_list = []
        for ip in ips:
            ip_list.append(ip + "|XX")

        return ip_list

    def query(self, domain, type=None):
        if utils.check_ip_valid(domain):
            return [domain]

        ips = g.domain_cache.get_ordered_ips(domain, type)
        if not ips:
            if "." in domain:
                ips = remote_query_dns(domain, type)
            if not ips or self.in_country(ips):
                ips = self.query_local_dns(domain)
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
    dns_server = DnsServer(port=8053)
    try:
        dns_server.server_forever()
    except KeyboardInterrupt:  # Ctrl + C on console
        dns_server.stop()
        os._exit(0)