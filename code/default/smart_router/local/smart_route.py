import time
import socket
import struct
import urlparse
import io
import ssl

import utils
import simple_http_server
from socket_wrap import SocketWrap
import global_var as g
from gae_proxy.local import check_local_network

from xlog import getLogger
xlog = getLogger("smart_router")


SO_ORIGINAL_DST = 80



fake_host = ""


class ConnectFail(Exception):
    pass


class RedirectHttpsFail(Exception):
    pass


class SniNotExist(Exception):
    pass


class SslWrapFail(Exception):
    pass


class XTunnelNotRunning(Exception):
    pass


def is_gae_workable():
    if not g.gae_proxy:
        return False

    return g.gae_proxy.apis.is_workable()


def is_x_tunnel_workable():
    if not g.x_tunnel:
        return False

    return g.x_tunnel.apis.is_workable()


def is_clienthello(data):
    if len(data) < 20:
        return False
    if data.startswith('\x16\x03'):
        # TLSv12/TLSv11/TLSv1/SSLv3
        length, = struct.unpack('>h', data[3:5])
        return len(data) == 5 + length
    elif data[0] == '\x80' and data[2:4] == '\x01\x03':
        # SSLv23
        return len(data) == 2 + ord(data[1])
    else:
        return False


def have_ipv6(ips):
    for ip in ips:
        if ":" in ip:
            return True

    return False


def extract_sni_name(packet):
    if not packet.startswith('\x16\x03'):
        return

    stream = io.BytesIO(packet)
    stream.read(0x2b)
    session_id_length = ord(stream.read(1))
    stream.read(session_id_length)
    cipher_suites_length, = struct.unpack('>h', stream.read(2))
    stream.read(cipher_suites_length+2)
    extensions_length, = struct.unpack('>h', stream.read(2))
    # extensions = {}
    while True:
        data = stream.read(2)
        if not data:
            break
        etype, = struct.unpack('>h', data)
        elen, = struct.unpack('>h', stream.read(2))
        edata = stream.read(elen)
        if etype == 0:
            server_name = edata[5:]
            return server_name


def netloc_to_host_port(netloc, default_port=80):
    if ":" in netloc:
        host, _, port = netloc.rpartition(':')
        port = int(port)
    else:
        host = netloc
        port = default_port
    return host, port


def get_sni(sock, left_buf=""):
    if left_buf:
        leadbyte = left_buf[0]
    else:
        leadbyte = sock.recv(1, socket.MSG_PEEK)

    if leadbyte in ('\x80', '\x16'):
        if leadbyte == '\x16':
            for _ in xrange(2):
                leaddata = left_buf + sock.recv(1024, socket.MSG_PEEK)
                if is_clienthello(leaddata):
                    try:
                        server_name = extract_sni_name(leaddata)
                        return server_name
                    except:
                        break

        raise SniNotExist

    elif leadbyte not in ["G", "P", "D", "O", "H", "T"]:
        raise SniNotExist

    leaddata = ""
    for _ in xrange(2):
        leaddata = left_buf + sock.recv(1024, socket.MSG_PEEK)
        if leaddata:
            break
        else:
            time.sleep(0.1)
            continue
    if not leaddata:
        raise SniNotExist

    n1 = leaddata.find("\r\n")
    if n1 <= -1:
        raise SniNotExist

    req_line = leaddata[:n1]
    words = req_line.split()
    if len(words) == 3:
        method, url, http_version = words
    elif len(words) == 2:
        method, url = words
        http_version = "HTTP/1.1"
    else:
        raise SniNotExist

    if method not in ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "PATCH"]:
        raise SniNotExist

    n2 = leaddata.find("\r\n\r\n", n1)
    if n2 <= -1:
        raise SniNotExist
    header_block = leaddata[n1+2:n2]

    lines = header_block.split("\r\n")
    # path = url
    host = None
    for line in lines:
        key, _, value = line.rpartition(":")
        value = value.strip()
        if key.lower() == "host":
            host, port = netloc_to_host_port(value)
            break
    if host is None:
        raise SniNotExist

    return host


def do_direct(sock, host, ips, port, client_address, left_buf=""):
    if not g.config.auto_direct:
        raise ConnectFail()

    remote_sock = g.connect_manager.get_conn(host, ips, port)
    if not remote_sock:
        raise ConnectFail()

    xlog.debug("host:%s:%d direct connect %s success", host, port, remote_sock.ip)
    if left_buf:
        remote_sock.send(left_buf)
    g.pipe_socks.add_socks(sock, remote_sock)


def do_redirect_https(sock, host, ips, port, client_address, left_buf=""):
    if not g.config.auto_direct:
        raise ConnectFail()

    remote_sock = g.connect_manager.get_conn(host, ips, 443)
    if not remote_sock:
        raise RedirectHttpsFail()

    try:
        ssl_sock = ssl.wrap_socket(remote_sock._sock)
    except Exception as e:
        raise RedirectHttpsFail()

    xlog.debug("host:%s:%d redirect_https connect %s success", host, port, remote_sock.ip)

    if left_buf:
        ssl_sock.send(left_buf)
    sw = SocketWrap(ssl_sock, remote_sock.ip, port, host)
    sock.recved_times = 3
    g.pipe_socks.add_socks(sock, sw)


def do_socks(sock, host, port, client_address, left_buf=""):
    if not g.x_tunnel:
        raise XTunnelNotRunning()

    try:
        conn_id = g.x_tunnel.proxy_session.create_conn(sock, host, port)
    except Exception as e:
        xlog.warn("do_sock to %s:%d, x_tunnel fail:%r", host, port, e)
        raise XTunnelNotRunning()

    if not conn_id:
        xlog.warn("x_tunnel create conn fail")
        raise XTunnelNotRunning()

    # xlog.debug("do_socks %r connect to %s:%d conn_id:%d", client_address, host, port, conn_id)
    if left_buf:
        g.x_tunnel.global_var.session.conn_list[conn_id].transfer_received_data(left_buf)
    g.x_tunnel.global_var.session.conn_list[conn_id].start(block=True)


def do_gae(sock, host, port, client_address, left_buf=""):
    sock.setblocking(1)
    if left_buf:
        ssl_sock = sock
        schema = "http"
    else:
        leadbyte = sock.recv(1, socket.MSG_PEEK)
        if leadbyte in ('\x80', '\x16'):
            try:
                ssl_sock = g.gae_proxy.proxy_handler.wrap_ssl(sock._sock, host, port, client_address)
            except Exception as e:
                raise SslWrapFail()

            schema = "https"
        else:
            ssl_sock = sock
            schema = "http"

    ssl_sock.setblocking(1)
    xlog.debug("host:%s:%d do gae", host, port)
    req = g.gae_proxy.proxy_handler.GAEProxyHandler(ssl_sock, client_address, None, xlog)
    req.parse_request()

    if req.path[0] == '/':
        req.path = '%s://%s%s' % (schema, req.headers['Host'], req.path)

    if req.path in ["http://www.twitter.com/xxnet", "https://www.twitter.com/xxnet"]:
        # for web_ui status page
        # auto detect browser proxy setting is work
        xlog.debug("CONNECT %s %s", req.command, req.path)
        req.wfile.write(req.self_check_response_data)
        ssl_sock.close()
        return

    req.parsed_url = urlparse.urlparse(req.path)
    req.do_METHOD()


def try_loop(scense, rule_list, sock, host, port, client_address, left_buf=""):
    start_time = time.time()

    for rule in rule_list:
        try:
            if rule == "redirect_https":
                if port != 80:
                    continue

                ips = g.dns_srv.query(host)
                do_redirect_https(sock, host, ips, port, client_address, left_buf)
                xlog.info("%s %s:%d redirect_https", scense, host, port)
                return

            elif rule == "direct":
                ips = g.dns_srv.query(host)
                do_direct(sock, host, ips, port, client_address, left_buf)
                xlog.info("%s %s:%d direct", scense, host, port)
                return

            elif rule == "gae":
                if not is_gae_workable() and host != fake_host:
                    xlog.debug("%s gae host:%s:%d, but gae not work", scense, host, port)
                    continue

                try:
                    sni_host = get_sni(sock, left_buf)
                    xlog.info("%s %s:%d gae", scense, host, port)
                    do_gae(sock, host, port, client_address, left_buf)
                    return
                except SniNotExist:
                    xlog.debug("%s domain:%s get sni fail", scense, host)
                    continue
                except (SslWrapFail, simple_http_server.ParseReqFail) as e:
                    xlog.warn("%s domain:%s sni:%s fail:%r", scense, host, sni_host, e)
                    g.domain_cache.report_gae_deny(host, port)
                    sock.close()
                    return
                except simple_http_server.GetReqTimeout:
                    # Happen sometimes, don't known why.
                    xlog.debug("%s host:%s:%d try gae, GetReqTimeout:%d", scense, host, port,
                             (time.time() - start_time) * 1000)
                    sock.close()
                    return
                except Exception as e:
                    xlog.exception("%s host:%s:%d rule:%s except:%r", scense, host, port, rule, e)
                    g.domain_cache.report_gae_deny(host, port)
                    sock.close()
                    return

            elif rule == "socks":
                xlog.info("%s %s:%d socks", scense, host, port)
                do_socks(sock, host, port, client_address, left_buf)
                return
            elif rule == "black":
                xlog.info("%s to:%s:%d black", scense, host, port)
                sock.close()
                return
            else:
                xlog.error("%s %s:%d rule:%s unknown", scense, host, port, host, rule)
                sock.close()
                return
        except Exception as e:
            xlog.debug("%s %s to %s:%d except:%r", scense, rule, host, port, e)

    xlog.info("%s %s to %s:%d fail", scense, rule_list, host, port)
    sock.close()
    return


def handle_ip_proxy(sock, ip, port, client_address):
    if not isinstance(sock, SocketWrap):
        sock = SocketWrap(sock, client_address[0], client_address[1])

    rule = g.user_rules.check_host(ip, port)
    if not rule:
        if utils.is_private_ip(ip):
            rule = "direct"

    if rule:
        return try_loop("ip user", [rule], sock, ip, port, client_address)

    if g.config.auto_direct and g.ip_region.check_ip(ip):
        rule_list = ["direct", "gae", "socks", "redirect_https"]
    else:
        if g.config.auto_direct or g.config.auto_gae:
            try:
                host = get_sni(sock)
                if host:
                    return handle_domain_proxy(sock, host, port, client_address)
            except SniNotExist as e:
                xlog.debug("ip:%s:%d get sni fail", ip, port)

        if not g.config.auto_direct:
            rule_list = ["socks"]
        else:
            record = g.ip_cache.get(ip)
            if record and record["r"] == "socks":
                rule_list = ["socks"]
            else:
                rule_list = ["direct", "socks"]

    if not g.config.auto_direct and "direct" in rule_list:
        try:
            rule_list.remove("direct")
            rule_list.remove("redirect_https")
        except:
            pass

    if not g.config.auto_gae and "gae" in rule_list:
        try:
            rule_list.remove("gae")
        except:
            pass

    try_loop("ip", rule_list, sock, ip, port, client_address)


def handle_domain_proxy(sock, host, port, client_address, left_buf=""):
    global fake_host
    if not fake_host and g.gae_proxy:
        fake_host = g.gae_proxy.web_control.get_fake_host()

    if not isinstance(sock, SocketWrap):
        sock = SocketWrap(sock, client_address[0], client_address[1])

    sock.target = "%s:%d" % (host, port)
    rule = g.user_rules.check_host(host, port)
    if not rule:
        if host == fake_host:
            rule = "gae"
        elif utils.check_ip_valid(host) and utils.is_private_ip(host):
            rule = "direct"

    if rule:
        return try_loop("domain user", [rule], sock, host, port, client_address, left_buf)

    if g.config.block_advertisement and g.gfwlist.is_advertisement(host):
        xlog.info("block advertisement %s:%d", host, port)
        sock.close()
        return

    #ips = g.dns_srv.query(host)
    #if check_local_network.IPv6.is_ok() and have_ipv6(ips) and port == 443:
    #    rule_list = ["direct", "gae", "socks", "redirect_https"]
    # gae is more faster then direct.

    record = g.domain_cache.get(host)
    if record and record["r"] != "unknown":
        rule = record["r"]
        if rule == "gae":
            rule_list = ["gae", "socks", "redirect_https", "direct"]
        else:
            rule_list = ["direct", "gae", "socks", "redirect_https"]

        if not g.domain_cache.accept_gae(host):
            rule_list.remove("gae")
    elif g.gfwlist.is_white(host):
        rule_list = ["direct", "gae", "socks", "redirect_https"]
    elif g.gfwlist.check(host):
        rule_list = ["gae", "socks", "redirect_https", "direct"]
    else:
        ips = g.dns_srv.query(host)
        if g.ip_region.check_ips(ips):
            rule_list = ["direct", "gae", "socks", "redirect_https"]
        else:
            rule_list = ["gae", "socks", "redirect_https", "direct"]

    if not g.config.auto_direct and "direct" in rule_list:
        try:
            rule_list.remove("direct")
            rule_list.remove("redirect_https")
        except:
            pass

    if not g.config.auto_gae and "gae" in rule_list:
        try:
            rule_list.remove("gae")
        except:
            pass

    try_loop("domain", rule_list, sock, host, port, client_address, left_buf)
