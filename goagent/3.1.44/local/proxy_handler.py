#!/usr/bin/env python
# coding:utf-8


import errno
import time
import struct
import zlib
import functools
import re
import io
import logging
import string
import threading
import socket
import ssl
import Queue
import BaseHTTPServer
import httplib
import urlparse


from cert_util import CertUtil
from connect_manager import https_manager,forwork_manager
from appids_manager import appid_manager

import OpenSSL
NetWorkIOError = (socket.error, ssl.SSLError, OpenSSL.SSL.Error, OSError)


from config import config
import gae_handler



class GAEProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    bufsize = 256*1024
    max_retry = 3

    def setup(self):
        self.__class__.setup = BaseHTTPServer.BaseHTTPRequestHandler.setup
        self.__class__.do_GET = self.__class__.do_METHOD
        self.__class__.do_PUT = self.__class__.do_METHOD
        self.__class__.do_POST = self.__class__.do_METHOD
        self.__class__.do_HEAD = self.__class__.do_METHOD
        self.__class__.do_DELETE = self.__class__.do_METHOD
        self.__class__.do_OPTIONS = self.__class__.do_METHOD
        self.setup()

    def finish(self):
        """make python2 BaseHTTPRequestHandler happy"""
        try:
            BaseHTTPServer.BaseHTTPRequestHandler.finish(self)
        except NetWorkIOError as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_METHOD(self):
        host = self.headers.get('Host', '')

        if self.path[0] == '/' and host:
            self.path = 'http://%s%s' % (host, self.path)
        elif not host and '://' in self.path:
            host = urlparse.urlparse(self.path).netloc

        self.parsed_url = urlparse.urlparse(self.path)

        if host in config.HOSTS_MAP or host.endswith(config.HOSTS_POSTFIX_ENDSWITH):
            return self.wfile.write(('HTTP/1.1 301\r\nLocation: %s\r\n\r\n' % self.path.replace('http://', 'https://', 1)).encode())
        else:
            return self.do_AGENT()


    # Called by do_METHOD and do_CONNECT_AGENT
    def do_AGENT(self):

        request_headers = dict((k.title(), v) for k, v in self.headers.items())

        payload = b''
        if 'Content-Length' in request_headers:
            try:
                payload = self.rfile.read(int(request_headers.get('Content-Length', 0)))
            except NetWorkIOError as e:
                logging.error('handle_method_urlfetch read payload failed:%s', e)
                return

        gae_handler.handler(self.command, self.path, request_headers, payload, self.wfile)

    def do_CONNECT(self):
        """handle CONNECT cmmand, socket forward or deploy a fake cert"""
        host, _, port = self.path.rpartition(':')

        if host == "appengine.google.com":
            return self.do_CONNECT_AGENT()

        if host in config.HOSTS_MAP or host.endswith(config.HOSTS_POSTFIX_ENDSWITH):
            return self.do_CONNECT_FWD()
        else:
            return self.do_CONNECT_AGENT()

    def do_CONNECT_FWD(self):
        """socket forward for http CONNECT command"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        logging.info('FWD %s %s:%d ', self.command, host, port)
        if host == "appengine.google.com" or host == "www.google.com":
            connected_in_s = 5 # goagent upload to appengine is slow, it need more 'fresh' connection.
        else:
            connected_in_s = 10  # gws connect can be used after tcp connection created 15 s


        try:
            self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')
            data = self.connection.recv(1024)
        except Exception as e:
            logging.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            return

        remote = forwork_manager.create_connection(host=host, port=port, sock_life=connected_in_s)
        if remote is None:
            self.connection.close()
            logging.warn('FWD %s %s:%d create_connection fail', self.command, host, port)
            return

        try:
            if data:
                remote.send(data)
        except Exception as e:
            logging.exception('do_CONNECT_FWD (%r, %r) Exception:%s', host, port, e)
            self.connection.close()
            remote.close()
            return

        # reset timeout default to avoid long http upload failure, but it will delay timeout retry :(
        remote.settimeout(None)

        forwork_manager.forward_socket(self.connection, remote, bufsize=self.bufsize)
        logging.debug('FWD %s %s:%d with closed', self.command, host, port)

    def do_CONNECT_AGENT(self):
        """deploy fake cert to client"""
        host, _, port = self.path.rpartition(':')
        port = int(port)
        certfile = CertUtil.get_cert(host)
        logging.info('GAE %s %s:%d ', self.command, host, port)
        self.__realconnection = None
        self.wfile.write(b'HTTP/1.1 200 OK\r\n\r\n')

        try:
            ssl_sock = ssl.wrap_socket(self.connection, keyfile=certfile, certfile=certfile, server_side=True)
        except ssl.SSLError as e:
            logging.info('ssl error: %s, create full domain cert for host:%s', e, host)
            certfile = CertUtil.get_cert(host, full_name=True)
            return
        except Exception as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET):
                logging.exception('ssl.wrap_socket(self.connection=%r) failed: %s path:%s, errno:%s', self.connection, e, self.path, e.args[0])
            return

        self.__realconnection = self.connection
        self.__realwfile = self.wfile
        self.__realrfile = self.rfile
        self.connection = ssl_sock
        self.rfile = self.connection.makefile('rb', self.bufsize)
        self.wfile = self.connection.makefile('wb', 0)

        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                return
        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise
        if self.path[0] == '/' and host:
            self.path = 'https://%s%s' % (self.headers['Host'], self.path)
        logging.debug('GAE CONNECT %s %s', self.command, self.path)

        try:
            if self.path[0] == '/' and host:
                self.path = 'http://%s%s' % (host, self.path)
            elif not host and '://' in self.path:
                host = urlparse.urlparse(self.path).netloc

            self.parsed_url = urlparse.urlparse(self.path)

            return self.do_AGENT()


        except NetWorkIOError as e:
            if e.args[0] not in (errno.ECONNABORTED, errno.ETIMEDOUT, errno.EPIPE):
                raise
        finally:
            if self.__realconnection:
                try:
                    self.__realconnection.shutdown(socket.SHUT_WR)
                    self.__realconnection.close()
                except NetWorkIOError:
                    pass
                finally:
                    self.__realconnection = None

