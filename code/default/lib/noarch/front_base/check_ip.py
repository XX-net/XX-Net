import socket
import time

import hyper
import simple_http_client
import utils


class CheckIp(object):
    def __init__(self, logger, config, connect_creator):
        self.logger = logger
        self.config = config
        self.connect_creator = connect_creator
        self.check_content = utils.to_bytes(self.config.check_ip_content)

    def check_http1(self, ssl_sock, host):
        self.logger.info("ip:%s use http/1.1", ssl_sock.ip_str)

        try:
            request_data = 'GET %s HTTP/1.1\r\nHost: %s\r\nAccept: */*\r\n\r\n' % (self.config.check_ip_path, host)
            ssl_sock.send(request_data.encode())

            response = simple_http_client.Response(ssl_sock)
            response.begin(timeout=5)
            return response
        except Exception as e:
            self.logger.exception("check ip %s http1 e:%r", ssl_sock.ip_str, e)
            return False

    def check_http2(self, ssl_sock, host, path=None, headers={}):
        self.logger.debug("ip:%s use http/2", ssl_sock.ip_str)
        try:
            conn = hyper.HTTP20Connection(ssl_sock, host=host, ip=ssl_sock.ip_str, port=443)
            if not path:
                path = self.config.check_ip_path
            conn.request('GET', path, headers=headers)
            response = conn.get_response()
            return response
        except Exception as e:
            self.logger.debug("check ip %s http2 get response fail:%r", ssl_sock.ip_str, e)
            return False

    def check_ip(self, ip, sni=None, host=None, wait_time=0, path=None, headers={}):
        try:
            ssl_sock = self.connect_creator.connect_ssl(ip, sni=sni, host=host)
        except socket.timeout:
            self.logger.warn("connect timeout")
            return False
        except Exception as e:
            self.logger.exception("check_ip:%s create_ssl except:%r", ip, e)
            return False

        ssl_sock.ok = False

        if host:
            pass
        elif self.config.check_ip_subdomain:
            host = self.config.check_ip_subdomain + "." + ssl_sock.host
        elif self.config.check_ip_host:
            host = self.config.check_ip_host
        else:
            host = ssl_sock.host
        self.logger.info("host:%s", host)

        if wait_time:
            time.sleep(wait_time)
        start_time = time.time()

        if not ssl_sock.h2:
            response = self.check_http1(ssl_sock, host)
        else:
            response = self.check_http2(ssl_sock, host, path, headers)

        if not response:
            return False

        if not self.check_response(response):
            return False

        time_cost = (time.time() - start_time) * 1000
        ssl_sock.request_time = time_cost
        self.logger.info("check ok, time:%d", time_cost)
        ssl_sock.ok = True
        ssl_sock.response = response
        return ssl_sock

    def check_response(self, response):
        server_type = response.headers.get(b'Server', b"")
        self.logger.debug("status:%d", response.status)
        self.logger.debug("Server type:%s", server_type)

        if response.status not in self.config.check_ip_accept_status:
            return False

        content = response.read()
        response.content = content

        if self.check_content and self.check_content not in content:
            self.logger.warn("app check content:%s", content)
            return False

        return True
