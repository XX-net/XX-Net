import socket
import time

import hyper
import simple_http_client


class CheckIp(object):
    def __init__(self, logger, config, connect_creator):
        self.logger = logger
        self.config = config
        self.connect_creator = connect_creator

    def check_http1(self, ssl_sock, host):
        self.logger.info("ip:%s use http/1.1", ssl_sock.ip)
        start_time = time.time()

        try:
            request_data = 'GET / HTTP/1.1\r\nHost: %s\r\n\r\n' % host
            ssl_sock.send(request_data.encode())

            response = simple_http_client.Response(ssl_sock)
            response.begin(timeout=5)

            server_type = response.getheader('Server', "")
            self.logger.debug("status:%d", response.status)
            self.logger.debug("Server type:%s", server_type)
            if response.status == 403:
                self.logger.warn("check status:%d", response.status)
                return ssl_sock

            if response.status != 200:
                self.logger.warn("ip:%s status:%d", ssl_sock.ip, response.status)
                return False

            content = response.read(timeout=1)
            if self.config.check_ip_content not in content:
                self.logger.warn("app check content:%s", content)
                return ssl_sock
        except Exception as e:
            self.logger.debug("check ip %s http1 e:%r", ssl_sock.ip, e)
            return ssl_sock

        time_cost = (time.time() - start_time) * 1000
        ssl_sock.request_time = time_cost
        self.logger.info("check ok, time:%d", time_cost)
        ssl_sock.ok = True
        return ssl_sock

    def check_http2(self, ssl_sock, host):
        self.logger.warn("ip:%s use http/2", ssl_sock.ip)
        start_time = time.time()
        try:
            conn = hyper.HTTP20Connection(ssl_sock, host=host, ip=ssl_sock.ip, port=443)
            conn.request('GET', '/')
        except Exception as e:
            # self.logger.exception("xtunnel %r", e)
            self.logger.debug("ip:%s http/1.1:%r", ssl_sock.ip, e)
            return ssl_sock

        try:
            response = conn.get_response()
        except Exception as e:
            self.logger.exception("http2 get response fail:%r", e)
            return ssl_sock

        self.logger.debug("ip:%s http/2", ssl_sock.ip)

        if response.status != 200:
            self.logger.warn("app check ip:%s status:%d", ssl_sock.ip, response.status)
            return ssl_sock

        content = response.read()
        if self.config.check_ip_content not in content:
            self.logger.warn("app check content:%s", content)
            return ssl_sock

        ssl_sock.ok = True
        time_cost = (time.time() - start_time) * 1000
        ssl_sock.request_time = time_cost
        self.logger.info("check ok, time:%d", time_cost)
        return ssl_sock

    def check_ip(self, ip, host=None, wait_time=0):
        try:
            ssl_sock = self.connect_creator.connect_ssl(ip, host=host)
        except socket.timeout:
            self.logger.warn("connect timeout")
            return False
        except Exception as e:
            self.logger.exception("test_xtunnel_ip %s e:%r", ip, e)
            return False

        ssl_sock.ok = False

        if self.config.check_ip_host:
            host = self.config.check_ip_host
        else:
            host = ssl_sock.host
        self.logger.info("host:%s", host)

        time.sleep(wait_time)

        if not ssl_sock.h2:
            return self.check_http1(ssl_sock, host)
        else:
            return self.check_http2(ssl_sock, host)

