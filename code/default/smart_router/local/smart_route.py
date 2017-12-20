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
from xlog import getLogger
xlog = getLogger("smart_router")


SO_ORIGINAL_DST = 80


class ConnectFail(Exception):
    pass


class RedirectHttpsFail(Exception):
    pass


class SniNotExist(Exception):
    pass


class SslWrapFail(Exception):
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


def get_sni(sock):
    leadbyte = sock.recv(1, socket.MSG_PEEK)
    if leadbyte in ('\x80', '\x16'):
        if leadbyte == '\x16':
            for _ in xrange(2):
                leaddata = sock.recv(1024, socket.MSG_PEEK)
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
        leaddata = sock.recv(1024, socket.MSG_PEEK)
        if not leaddata:
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
    remote_sock = g.connect_manager.get_conn(host, ips, port)
    if not remote_sock:
        raise ConnectFail()

    xlog.debug("host:%s:%d direct connect %s success", host, port, remote_sock.ip)
    if left_buf:
        remote_sock.send(left_buf)
    g.pipe_socks.add_socks(sock, remote_sock)


def do_redirect_https(sock, host, ips, port, client_address, left_buf=""):
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
        xlog.warn("x_tunnel not run. sock to %s:%d close", host, port)
        sock.close()
        return

    try:
        conn_id = g.x_tunnel.proxy_session.create_conn(sock, host, port)
    except Exception as e:
        xlog.warn("do_sock to %s:%d, x_tunnel fail:%r", host, port, e)
        sock.close()
        return

    if not conn_id:
        xlog.warn("x_tunnel create conn fail")
        sock.close()
        return
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
    req.do_AGENT()


def handle_ip_proxy(sock, ip, port, client_address):
    sock = SocketWrap(sock, client_address[0], client_address[1])
    rule = g.user_rules.check_host(ip, port)
    if not rule:
        if utils.is_private_ip(ip):
            rule = "direct"

    if rule:
        if rule == "direct":
            try:
                do_direct(sock, ip, [ip], port, client_address)
                xlog.info("host:%s:%d user direct", ip, port)
            except ConnectFail:
                xlog.warn("ip:%s:%d user rule:%s connect fail", ip, port, rule)
                sock.close()
            return
        elif rule == "socks":
            do_socks(sock, ip, port, client_address)
            xlog.info("host:%s:%d user socks", ip, port)
            return
        elif rule == "black":
            xlog.info("ip:%s:%d user rule:%s", ip, port, rule)
            sock.close()
            return
        else:
            xlog.error("get rule:%s unknown", rule)
            sock.close()
            return

    try:
        host = get_sni(sock)
        return handle_domain_proxy(sock, host, port, client_address)
    except SniNotExist as e:
        xlog.debug("ip:%s:%d get sni fail", ip, port)

    record = g.ip_cache.get(ip)
    if record:
        rule = record["r"]
    else:
        rule = "direct"

    if rule == "direct":
        try:
            do_direct(sock, ip, [ip], port, client_address)
            xlog.info("host:%s:%d direct", ip, port)
            return
        except ConnectFail:
            xlog.debug("%s:%d try direct fail", ip, port)
            rule = "socks"
            g.ip_cache.update_rule(ip, port, "socks")
    if rule == "socks":
        do_socks(sock, ip, port, client_address)
        xlog.info("host:%s:%d socks", ip, port)
        return

    xlog.error("get rule:%s unknown", rule)
    sock.close()
    return


def handle_domain_proxy(sock, host, port, client_address, left_buf=""):
    if not isinstance(sock, SocketWrap):
        sock = SocketWrap(sock, client_address[0], client_address[1])

    sock.target = "%s:%d" % (host, port)
    start_time = time.time()
    rule = g.user_rules.check_host(host, port)
    if not rule:
        if host == "www.twitter.com":
            rule = "gae"
        elif utils.check_ip_valid(host) and utils.is_private_ip(host):
            rule = "direct"

    if rule:
        if rule == "direct":
            ips = g.dns_srv.query(host)

            try:
                do_direct(sock, host, ips, port, client_address, left_buf)
                xlog.info("host:%s:%d user direct", host, port)
            except ConnectFail:
                xlog.warn("host:%s:%d user rule:%s connect fail", host, port, rule)
                sock.close()
            return
        elif rule == "redirect_https":
            ips = g.dns_srv.query(host)

            try:
                do_redirect_https(sock, host, ips, port, client_address, left_buf)
                xlog.info("host:%s:%d user redirect_https", host, port)
            except RedirectHttpsFail :
                xlog.warn("host:%s:%d user rule:%s connect fail", host, port, rule)
                sock.close()
            return
        elif rule == "gae":
            if not is_gae_workable():
                xlog.debug("host:%s:%d user rule:%s, but gae not work", host, port, rule)
                sock.close()
                return

            try:
                host = get_sni(sock)
                do_gae(sock, host, port, client_address, left_buf)
                xlog.info("host:%s:%d user gae", host, port)
            except ssl.SSLError as e:
                xlog.warn("host:%s:%d user rule gae, GetReqTimeout:%d e:%r", host, port, (time.time()-start_time)*1000, e)
                sock.close()
            except simple_http_server.GetReqTimeout as e:
                # xlog.warn("host:%s:%d user rule gae, GetReqTimeout:%d e:%r", host, port, (time.time()-start_time)*1000, e)
                sock.close()
            except Exception as e:
                xlog.warn("host:%s:%d user rule:%s except:%r", host, port, rule, e)
                sock.close()
            return
        elif rule == "socks":
            do_socks(sock, host, port, client_address, left_buf)
            xlog.info("host:%s:%d user rule:socks", host, port)
            return
        elif rule == "black":
            xlog.info("host:%s:%d user rule black", host, port)
            sock.close()
            return
        else:
            xlog.error("get rule:%s unknown", rule)
            sock.close()
            return

    record = g.domain_cache.get(host)
    if not record:
        rule = "direct"
    else:
        rule = record["r"]

    if not rule or rule == "direct":
        if g.config.auto_direct:
            ips = g.dns_srv.query(host)

            try:
                if port == 80 and g.gfwlist.check(host):
                    do_redirect_https(sock, host, ips, port, client_address, left_buf)
                    xlog.info("%s:%d redirect_https", host, port)
                    return
                else:
                    do_direct(sock, host, ips, port, client_address, left_buf)
                    xlog.info("%s:%d direct", host, port)
                    return
            except (ConnectFail, RedirectHttpsFail) as e:
                xlog.debug("%s:%d try direct/redirect fail:%r", host, port, e)
                rule = "gae"
        else:
            rule = "gae"

    if rule == "gae":
        if g.config.auto_gae and is_gae_workable() and g.domain_cache.accept_gae(host, port):
            try:
                sni_host = get_sni(sock)
                do_gae(sock, host, port, client_address, left_buf)
                xlog.info("%s:%d gae", host, port)
                return
            except SniNotExist:
                xlog.debug("domain:%s get sni fail", host)
                rule = "socks"
            except (SslWrapFail, simple_http_server.ParseReqFail) as e:
                xlog.warn("domain:%s sni:%s fail:%r", host, sni_host, e)
                g.domain_cache.report_gae_deny(host, port)
                sock.close()
                return
            except simple_http_server.GetReqTimeout:
                # Happen sometimes, don't known why.
                # xlog.warn("host:%s:%d try gae, GetReqTimeout:%d", host, port,
                #          (time.time() - start_time) * 1000)
                sock.close()
                return
            except Exception as e:
                xlog.warn("host:%s:%d cache rule:%s except:%r", host, port, rule, e)
                g.domain_cache.report_gae_deny(host, port)
                sock.close()
                return

        else:
            rule = "socks"

    if rule == "socks":
        do_socks(sock, host, port, client_address, left_buf)
        xlog.info("%s:%d socks", host, port)
        return
    else:
        xlog.error("domain:%s get rule:%s unknown", host, rule)
        sock.close()
        return
