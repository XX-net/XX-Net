#!/usr/bin/env python
# coding:utf-8

# public DNS servers https://en.wikipedia.org/wiki/Public_recursive_name_server

import json
import os
import sys
import threading
import socket
import time
import re
import ssl
import random
import struct
import subprocess

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

python_path = root_path
noarch_lib = os.path.join(python_path, 'lib', 'noarch')
sys.path.append(noarch_lib)

import env_info
data_path = os.path.join(env_info.data_path, 'smart_router')

from queue import Queue
import lru_cache
import utils
import simple_http_client
from dnslib import DNSRecord, DNSHeader, A, AAAA, RR, DNSQuestion, QTYPE

from . import global_var as g

from xlog import getLogger
xlog = getLogger("smart_router")


def get_local_ips():
    def get_ip_address(NICname):
        import fcntl
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', NICname[:15].encode("UTF-8"))
        )[20:24])

    if sys.platform.startswith("linux"):

        if os.path.isfile("/system/bin/dalvikvm") or os.path.isfile("/system/bin/dalvikvm64") or \
                "android.googlesource.com" in sys.version:
            ips = [b'127.0.0.1']
        else:
            try:
                proc = subprocess.Popen(["ip addr show | egrep inet | awk '{{print $2}}' | awk -F'/' '{{print $1}}'"],
                                        stdout=subprocess.PIPE, shell=True)
                x = proc.communicate()[0]
                ips = x.strip().split(b"\n")
            except Exception as e:
                xlog.warn("get ip address e:%r", e)
                ips = [b'127.0.0.1']
    elif sys.platform == "darwin":
        try:
            proc = subprocess.Popen(["ifconfig | egrep inet | awk '{{print $2}}' | awk -F'/' '{{print $1}}'"],
                                    stdout=subprocess.PIPE, shell=True)
            x = proc.communicate()[0]
            ips = x.strip().split(b"\n")
        except Exception as e:
            xlog.warn("get ip address e:%r", e)
            ips = [b'127.0.0.1']
    elif sys.platform == "ios":
        ips = [b'127.0.0.1']
    elif sys.platform == "win32":
        try:
            ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]]
            ips = utils.to_bytes(ips)
            if b"127.0.0.1" not in ips:
                ips.append(b"127.0.0.1")
        except Exception as e:
            xlog.warn("get local ip fail:%r", e)
            ips = [b"127.0.0.1"]
    else:
        ips = []
        try:
            for ix in socket.if_nameindex():
                name = ix[1]
                ip = get_ip_address(name)
                ips.append(ip)
        except Exception as e:
            xlog.warn("get ip address e:%r", e)
            ips = [b'127.0.0.1']

    xlog.debug("local ips: %s", ips)
    return ips


def query_dns_from_xxnet(domain, dns_type=None):
    if not g.x_tunnel:
        return []

    t0 = time.time()
    content, status, response = g.x_tunnel.front_dispatcher.request(
        "GET", "dns.xx-net.org", path="/query?domain=%s" % (utils.to_str(domain)), timeout=5)
    t1 = time.time()

    if status != 200:
        xlog.warn("query_dns_from_xxnet fail status:%d, cost=%f", status, t1 - t0)
        return []

    if isinstance(content, memoryview):
        content = content.tobytes()

    content = utils.to_str(content)

    try:
        rs = json.loads(content)
        ips = rs["ip"]
        xlog.debug("query_dns_from_xxnet %s cost:%f return:%s", domain, t1 - t0, ips)
        #if dns_type == 1:
        #    ips = [ip for ip in ips if "." in ip]
        ips_out = []
        for ip_cn in ips:
            ip, cn = ip_cn.split("|")
            ips_out.append(ip)
        return ips_out
    except Exception as e:
        xlog.warn("query_dns_from_xxnet %s json:%s parse fail:%s", domain, content, e)
        return []


class LocalDnsQuery():
    def __init__(self, timeout=3):
        self.timeout = timeout
        self.waiters = lru_cache.LruCache(100)
        self.dns_server = self.get_local_dns_server()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        self.sock6.settimeout(1)

        self.running = True
        self.th = threading.Thread(target=self.dns_recv_worker, args=(self.sock,), name="dns_ipv4_receiver")
        self.th.start()

        self.th6 = threading.Thread(target=self.dns_recv_worker, args=(self.sock6,), name="dns_ipv6_receiver")
        self.th6.start()

    def get_local_dns_server(self):
        iplist = []
        if os.name == 'nt':
            import ctypes, ctypes.wintypes, struct, socket
            DNS_CONFIG_DNS_SERVER_LIST = 6
            buf = ctypes.create_string_buffer(2048)
            ctypes.windll.dnsapi.DnsQueryConfig(DNS_CONFIG_DNS_SERVER_LIST, 0, None, None, ctypes.byref(buf),
                                                ctypes.byref(ctypes.wintypes.DWORD(len(buf))))
            ipcount = struct.unpack('I', buf[0:4])[0]

            iplist = []
            for i in range(4, ipcount * 4 + 4, 4):
                ip = socket.inet_ntoa(buf[i:i + 4])
                iplist.append(ip)

        elif os.path.isfile('/etc/resolv.conf'):
            try:
                with open('/etc/resolv.conf', 'rb') as fp:
                    iplist = re.findall(br'(?m)^nameserver\s+(\S+)', fp.read())

                xlog.debug("DNS resolve servers:%s", iplist)

                local_ips = g.local_ips
                for ip in local_ips:
                    if ip in iplist:
                        xlog.warn("remove local DNS server %s from upstream", ip)
                        iplist.remove(ip)
            except Exception as e:
                xlog.warn("load /etc/resolv.conf fail:%r", e)

        if not iplist:
            if g.config.country_code == "CN":
                iplist = [
                    b"114.114.114.114",
                    b"114.114.115.115",
                    b"119.29.29.29",
                    b"182.254.118.118",
                    b"223.5.5.5",
                    b"223.6.6.6",
                    b"180.76.76.76"
                ]
            else:
                iplist = [
                    b"1.1.1.1",
                    b"8.8.8.8",
                    b"9.9.9.9",
                    b"208.67.222.222",
                    b"168.126.63.2"
                ]

        out_list = []
        for ip in iplist:
            if ip == b"127.0.0.1":
                continue
            out_list.append(ip)
            xlog.info("Local DNS server:%s", ip)

        return out_list

    def stop(self):
        self.running = False
        self.sock.close()

    def dns_recv_worker(self, sock):
        while self.running:
            try:
                try:
                    response, server = sock.recvfrom(8192)
                    server, port = server
                except Exception as e:
                    # xlog.exception("sock.recvfrom except:%r", e)
                    continue

                if not response:
                    continue

                try:
                    p = DNSRecord.parse(response)
                except Exception as e:
                    xlog.exception("dns client parse response fail:%r", e)
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
                xlog.debug("DNS local query received %s from:%s domain:%s org:%s", len(p.rr), server, domain, org_domain)
                ips = []
                for r in p.rr:
                    ip = utils.to_bytes(str(r.rdata))
                    ips.append(ip)

                if ips:
                    que.put(ips)
            except Exception as e:
                xlog.exception("dns recv_worker except:%r", e)

        xlog.info("DNS Client recv worker exit.")
        sock.close()

    def send_request(self, id, server_ip, domain, dns_type):
        try:
            d = DNSRecord(DNSHeader(id))
            d.add_question(DNSQuestion(domain, dns_type))
            req4_pack = d.pack()

            if utils.check_ip_valid4(server_ip):
                self.sock.sendto(req4_pack, (server_ip, 53))
            else:
                self.sock6.sendto(req4_pack, (server_ip, 53))
        except Exception as e:
            xlog.warn("send_request except:%r", e)

    def query_by_system(self, domain, dns_type):
        ips = []
        try:
            t0 = time.time()
            ip = socket.gethostbyname(domain)
            t1 = time.time()
            ips.append(ip)

            xlog.debug("query_by_system, %s %d cost:%f, return:%s", domain, dns_type, t1 - t0, ips)
        except Exception as e:
            xlog.warn("query_by_system %s %d e:%r", domain, dns_type, e)

        return ips

    def query(self, domain, dns_type=1, timeout=3):
        if sys.platform == "ios":
            return self.query_by_system(domain, dns_type)

        t0 = time.time()
        end_time = t0 + timeout
        while True:
            id = random.randint(0, 65535)
            if id not in self.waiters:
                break

        que = Queue()
        que.domain = domain

        for server_ip in self.dns_server:
            new_time = time.time()
            if new_time > end_time:
                break

            self.waiters[id] = que
            self.send_request(id, server_ip, domain, dns_type)

        try:
            ips = que.get(timeout=self.timeout)
        except:
            ips = []

        if ips:
            ips = list(set(ips))

        if id in self.waiters:
            del self.waiters[id]

        t1 = time.time()
        xlog.debug("query by udp, %s cost:%f, return:%s", domain, t1-t0, ips)

        return ips


class DnsOverTcpQuery():
    def __init__(self, server_list=[b"114.114.114.114"], port=53):
        self.protocol = "Tcp"
        self.timeout = 3
        self.connection_timeout = 60
        self.public_list = server_list
        self.port = port
        self.connections = []

    def get_server(self):
        return random.choice(self.public_list)

    def direct_connect(self, host, port):
        connect_timeout = 30

        if b':' in host:
            info = [(socket.AF_INET6, socket.SOCK_STREAM, 0, "", (host, port, 0, 0))]
        elif utils.check_ip_valid4(host):
            info = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (host, port))]
        else:
            try:
                info = socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                          socket.SOCK_STREAM)
            except socket.gaierror:
                info = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (host, port))]

        for res in info:
            af, socktype, proto, canonname, sa = res
            s = None
            try:
                s = socket.socket(af, socktype, proto)

                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32 * 1024)
                s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
                s.settimeout(connect_timeout)
                s.connect((host, port))
                return s
            except socket.error:
                if s:
                    s.close()
            except Exception as e:
                xlog.warn("Connect to DNS server %s:%d fail:%r", host, port)

        return None

    def get_connection(self):
        while len(self.connections):
            try:
                [sock, last_query_time] = self.connections.pop()
                if time.time() - last_query_time < self.connection_timeout:
                    return sock
            except:
                pass

        server_ip = self.get_server()
        if not server_ip:
            return None

        if not g.config.PROXY_ENABLE:
            sock = self.direct_connect(server_ip, self.port)
        else:
            connect_timeout = 5

            import socks

            sock = socks.socksocket(socket.AF_INET)
            sock.set_proxy(proxy_type=g.config.PROXY_TYPE,
                           addr=g.config.PROXY_HOST,
                           port=g.config.PROXY_PORT, rdns=True,
                           username=g.config.PROXY_USER,
                           password=g.config.PROXY_PASSWD)

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32*1024)
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
            sock.settimeout(connect_timeout)

            sock.connect((server_ip, self.port))

        return sock

    def query(self, domain, dns_type=1):
        t0 = time.time()
        try:
            sock = self.get_connection()
            if not sock:
                xlog.warn("query_over_tcp %s type:%s connect fail.", domain, dns_type)
                return []

            d = DNSRecord(DNSHeader())
            d.add_question(DNSQuestion(domain, dns_type))

            data = d.pack()
            data = struct.pack("!H", len(data)) + data
            sock.sendall(data)

            response = sock.recv(8192)
            if not response:
                return []

            length = struct.unpack("!H", bytes(response[:2]))[0]
            while len(response) - 2 < length:
                response += sock.recv(8192)

            t2 = time.time()

            p = DNSRecord.parse(response[2:])
            if len(p.rr) == 0:
                xlog.warn("query_over_tcp for %s type:%d return none, cost:%f", domain, dns_type, t2-t0)

            ips = []
            for r in p.rr:
                ip = utils.to_bytes(str(r.rdata))
                if not utils.check_ip_valid(ip) and dns_type != 2:
                    if ip == domain:
                        continue

                    ip_ips = self.query(ip, dns_type)
                    ips += ip_ips
                else:
                    ips.append(ip)

            xlog.debug("DNS %s %s return %s t:%f", self.protocol, domain, ips, t2-t0)
            self.connections.append([sock, time.time()])
            return ips
        except socket.timeout:
            xlog.warn("query_over_tcp %s type:%s timeout", domain, dns_type)
            return []
        except Exception as e:
            xlog.exception("query_over_tcp %s type:%s except:%r", domain, dns_type, e)
            return []


class DnsOverTlsQuery(DnsOverTcpQuery):
    def __init__(self, server_list=[b"1.1.1.1", b"9.9.9.9"]):
        DnsOverTcpQuery.__init__(self, server_list=server_list, port=853)
        self.protocol = "DoT"

    def get_connection(self):
        try:
            s = DnsOverTcpQuery.get_connection(self)
            if isinstance(s, ssl.SSLSocket) or s is None:
                return s

            sock = ssl.wrap_socket(s, ca_certs=os.path.join(current_path, "cloudflare_cert.pem"))
        except Exception as e:
            xlog.warn("DNSOverTlsQuery wrap_socket fail %r", e)
            return None

        sock.settimeout(self.timeout)

        return sock


class DnsOverHttpsQuery(object):
    def __init__(self, timeout=6):
        self.protocol = "DoH"
        self.timeout = timeout
        self.cn_servers = ["https://1.12.12.12/dns-query", "https://223.5.5.5/dns-query"]
        self.other_servers = [
            "https://1.1.1.1/dns-query",
            "https://dns10.quad9.net/dns-query",
            "https://dns.aa.net.uk/dns-query",
        ]
        self.connection_timeout = 60
        self.connections = []

    def get_connection(self):
        while len(self.connections):
            try:
                [client, last_query_time] = self.connections.pop()
                if time.time() - last_query_time < self.connection_timeout:
                    return client
            except:
                pass

        if g.config.PROXY_ENABLE == 1:
            return simple_http_client.Client(proxy={
                "type": g.config.PROXY_TYPE,
                "host": g.config.PROXY_HOST,
                "port": g.config.PROXY_PORT,
                "user": g.config.PROXY_USER,
                "pass": g.config.PROXY_PASSWD,
            }, timeout=self.timeout)
        else:
            return simple_http_client.Client(timeout=self.timeout)

    @property
    def server(self):
        return random.choice(self.other_servers)

    def query_json(self, domain, dns_type=1):
        try:
            t0 = time.time()
            client = self.get_connection()

            url = self.server + "?name=" + domain + "&type=A" # type need to map to Text.
            r = client.request("GET", url, headers={"accept": "application/dns-json"})
            t2 = time.time()
            ips = []
            if not r:
                xlog.warn("DNS server:%s domain:%s fail t:%f", self.server, domain,  t2 - t0)
                return ips

            t = utils.to_str(r.text)

            data = json.loads(t)
            for answer in data["Answer"]:
                ips.append(answer["data"])

            self.connections.append([client, time.time()])

            xlog.debug("DNS server:%s query:%s return %s t:%f", self.server, domain, ips, t2 - t0)
            return ips
        except Exception as e:
            xlog.warn("DNSOverHttpsQuery query fail:%r", e)
            return []

    def query(self, domain, dns_type=1, url=None):
        t0 = time.time()
        try:
            client = self.get_connection()

            if not url:
                url = self.server
            # xlog.debug("DoH use %s", url)

            d = DNSRecord(DNSHeader())
            d.add_question(DNSQuestion(domain, dns_type))
            data = d.pack()

            r = client.request("POST", url, headers={"accept": "application/dns-message",
                                                     "content-type": "application/dns-message"}, body=data)

            t2 = time.time()
            ips = []
            if not r:
                xlog.warn("DNS s:%s query:%s fail t:%f", self.server, domain,  t2 - t0)
                return ips

            p = DNSRecord.parse(r.text)

            self.connections.append([client, time.time()])

            for r in p.rr:
                ip = utils.to_bytes(str(r.rdata))
                if not utils.check_ip_valid(ip):
                    if ip == domain:
                        continue

                    ip_ips = self.query(ip, dns_type)
                    ips += ip_ips
                else:
                    ips.append(ip)

            xlog.debug("DNS %s %s return %s t:%f", self.protocol, domain, ips, t2 - t0)
            return ips
        except Exception as e:
            t1 = time.time()
            t = t1 - t0
            xlog.warn("DnsOverHttpsQuery query %s cost:%f fail:%r", domain, t, e)
            return []


class ParallelQuery():
    def query_worker(self, task, function):
        ips = function(task.domain, task.dns_type)
        if len(ips):
            g.domain_cache.set_ips(task.domain, ips, task.dns_type)
            task.put(ips)

    def query(self, domain, dns_type, funcs):
        task = Queue()
        task.domain = domain
        task.dns_type = dns_type

        for func in funcs:
            threading.Thread(target=self.query_worker, args=(task, func), name="ParalleQuery_%s" % domain).start()

        try:
            ips = task.get(timeout=5)
        except:
            ips = []

        return ips


class CombineDnsQuery():
    def __init__(self):
        self.domain_allowed_pattern = re.compile(br"(?!-)[A-Z\d-]{1,63}(?<!-)$")
        self.local_dns_resolve = LocalDnsQuery()

        self.tcp_query = DnsOverTcpQuery()
        self.tls_query = DnsOverTlsQuery()
        self.https_query = DnsOverHttpsQuery()

        self.parallel_query = ParallelQuery()

    def is_valid_hostname(self, hostname):
        hostname = hostname.upper()
        if len(hostname) > 255:
            return False
        if hostname.endswith(b"."):
            hostname = hostname[:-1]

        return all(self.domain_allowed_pattern.match(x) for x in hostname.split(b"."))

    def query_blocked_domain(self, domain, dns_type):
        return self.parallel_query.query(domain, dns_type, [
            self.https_query.query,
            self.tls_query.query,
            query_dns_from_xxnet,
        ])

    def query_unknown_domain(self, domain, dns_type):
        res = self.local_dns_resolve.query(domain, dns_type)
        if res:
            return res

        return self.parallel_query.query(domain, dns_type, [
            self.https_query.query,
            self.tls_query.query,
            self.tcp_query.query,
            query_dns_from_xxnet
        ])

    def query(self, domain, dns_type=1, history=[]):
        domain = utils.to_bytes(domain)
        if utils.check_ip_valid(domain):
            return [domain]

        if not self.is_valid_hostname(domain):
            xlog.warn("DNS query:%s not valid, type:%d", domain, dns_type)
            return []

        ips = g.domain_cache.get_ips(domain, dns_type)
        if ips:
            return ips

        rule = g.user_rules.check_host(domain, 0)
        if rule == "black":
            # user define black list like advertisement or malware server.
            ips = ["127.0.0.1"]
            xlog.debug("DNS query:%s in black", domain)
            return ips

        elif b"." not in domain or g.gfwlist.in_white_list(domain) or rule in ["direct"] or g.config.pac_policy == "all_Direct":
            ips = self.local_dns_resolve.query(domain, timeout=1)
            g.domain_cache.set_ips(domain, ips, dns_type)
            return ips

        elif g.gfwlist.in_block_list(domain) or rule in ["gae", "socks"] or g.config.pac_policy == "all_X-Tunnel":
            ips = self.query_blocked_domain(domain, dns_type)
        elif g.gfwlist.in_white_list(domain):
            ips = self.local_dns_resolve.query(domain, dns_type, timeout=1)
        else:
            ips = self.query_unknown_domain(domain, dns_type)

        if not ips:
            ips = self.local_dns_resolve.query(domain, timeout=1)

        out_ips = []
        for ip in ips:
            if not utils.check_ip_valid(ip):
                if ip == domain:
                    continue

                if ip in history:
                    continue

                history.append(ip)
                ip_ips = self.query(ip, dns_type, history)
                for ip in ip_ips:
                    out_ips.append(ip)

            elif ip not in out_ips:
                out_ips.append(ip)

        return out_ips

    def query_recursively(self, domain, dns_type=None):
        if not dns_type:
            dns_types = [1, 28]
        else:
            dns_types = [dns_type]

        ips_out = []
        for dns_type in dns_types:
            ips = self.query(domain, dns_type)
            for ip in ips:
                if dns_type == 2 or utils.check_ip_valid(ip):
                    ips_out.append(ip)
                else:
                    ips_s = self.query_recursively(ip, dns_type)
                    ips_out += ips_s

        return ips_out

    def stop(self):
        self.local_dns_resolve.stop()