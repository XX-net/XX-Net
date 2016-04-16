#!/usr/bin/env python
# coding:utf-8

import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform == "linux" or sys.platform == "linux2":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(win32_lib)

import platform
import BaseHTTPServer
import urlparse
import json
import os
import re
import subprocess
import cgi
import urllib2
import sys

import logging
import ConfigParser

os.environ['HTTPS_PROXY'] = ''
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))


class User_config(object):
    php_enable = '1'
    php_password = '123456'
    php_server = ''

    proxy_enable = "0"
    proxy_host = ""
    proxy_port = ""
    proxy_user = ""
    proxy_passwd = ""

    CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, os.pardir, os.pardir, 'data', 'php_proxy', 'config.ini'))

    def __init__(self):
        self.load()


    def load(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        CONFIG = ConfigParser.ConfigParser()


        try:
            if os.path.isfile(self.CONFIG_USER_FILENAME):
                CONFIG.read(self.CONFIG_USER_FILENAME)
            else:
                return

            try:
                self.php_enable = CONFIG.get('php', 'enable')
                self.php_password = CONFIG.get('php', 'password')
                self.php_server = CONFIG.get('php', 'fetchserver')
            except:
                pass

            self.proxy_enable = CONFIG.get('proxy', 'enable')
            self.proxy_host = CONFIG.get('proxy', 'host')
            self.proxy_port = CONFIG.get('proxy', 'port')
            self.proxy_user = CONFIG.get('proxy', 'username')
            self.proxy_passwd = CONFIG.get('proxy', 'password')
        except Exception as e:
            logging.warn("User_config.load except:%s", e)

    def save(self):
        try:
            f = open(self.CONFIG_USER_FILENAME, 'w')
            f.write("[php]\n")
            f.write("enable = %s\n" % self.php_enable)
            f.write("password = %s\n" % self.php_password)
            f.write("fetchserver = %s\n\n" % self.php_server)

            f.write("[proxy]\n")
            f.write("enable = %s\n" % self.proxy_enable)
            f.write("host = %s\n" % self.proxy_host)
            f.write("port = %s\n" % self.proxy_port)
            f.write("username = %s\n" % self.proxy_user)
            f.write("password = %s\n" % self.proxy_passwd)
            f.close()
        except:
            logging.exception("PHP config save user config fail:%s", self.CONFIG_USER_FILENAME)


user_config = User_config()


def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url)
    except Exception as e:
        logging.exception("web_control http_request:%s fail:%s", url, e)
    return

class RemoteContralServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    deploy_proc = None

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_GET(self):

        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                logging.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

        path = urlparse.urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/config":
            return self.req_config_handler()
        elif path == "/is_ready":
            return self.req_is_ready_handler()
        elif path == "/quit":
            common.keep_run = False
            data = "Quit"
            self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % ('text/plain', len(data))).encode())
            self.wfile.write(data)
            sys.exit()
            return
        else:
            logging.debug('PHP Web_control %s %s %s ', self.address_string(), self.command, self.path)
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def do_POST(self):
        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                logging.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass
        logging.debug ('PHP web_control %s %s %s ', self.address_string(), self.command, self.path)
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                self.postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.getheader('content-length'))
                self.postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                self.postvars = {}
        except:
            self.postvars = {}

        path = urlparse.urlparse(self.path).path
        if path == "/config":
            return self.req_config_handler()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_response(self, mimetype, data):
        self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def send_file(self, filename, mimetype):
        # logging.info('%s "%s %s HTTP/1.1" 200 -', self.address_string(), self.command, self.path)
        data = ''
        with open(filename, 'rb') as fp:
            data = fp.read()
        if data:
            self.send_response(mimetype, data)

    def req_log_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        cmd = "get_last"
        if reqs["cmd"]:
            cmd = reqs["cmd"][0]
        if cmd == "set_buffer_size" :
            if not reqs["buffer_size"]:
                data = '{"res":"fail", "reason":"size not set"}'
                mimetype = 'text/plain'
                self.send_response(mimetype, data)
                return

            buffer_size = reqs["buffer_size"][0]
            logging.set_buffer_size(buffer_size)
        elif cmd == "get_last":
            max_line = int(reqs["max_line"][0])
            data = logging.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"][0])
            data = logging.get_new_lines(last_no)
        else:
            logging.error('PAC %s %s %s ', self.address_string(), self.command, self.path)

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            if reqs['cmd'] == ['get_config']:
                data = json.dumps(user_config, default=lambda o: o.__dict__)
            elif reqs['cmd'] == ['set_config']:
                user_config.php_password = self.postvars['php_password'][0]
                user_config.php_server = self.postvars['php_server'][0]
                user_config.proxy_enable = self.postvars['proxy_enable'][0]
                user_config.proxy_host = self.postvars['proxy_host'][0]
                user_config.proxy_port = self.postvars['proxy_port'][0]
                user_config.proxy_username = self.postvars['proxy_username'][0]
                user_config.proxy_password = self.postvars['proxy_password'][0]
                user_config.save()

                data = '{"res":"success"}'
                self.send_response('text/html', data)

                http_request("http://127.0.0.1:8085/init_module?module=php_proxy&cmd=restart")
                return
        except Exception as e:
            logging.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response('text/html', data)


    def req_is_ready_handler(self):
        data = "True"

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

if __name__ == "__main__":
    pass