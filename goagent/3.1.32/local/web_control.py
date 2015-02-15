#!/usr/bin/env python
# coding:utf-8




import BaseHTTPServer
import urlparse
import json
import os
import re
import subprocess
import cgi
from httplib2 import Http
import sys

import logging
from config import config

from google_ip import google_ip
import connect_manager
import ConfigParser


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))

class User_config(object):
    appid = ''
    password = ''

    def __init__(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()

        # load ../../data/goagent/config.ini
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, 'data', 'goagent', 'config.ini'))
        self.load()

    def load(self):
        self.appid = ''
        self.password = ''
        try:
            if os.path.isfile(self.CONFIG_USER_FILENAME):
                self.CONFIG.read(self.CONFIG_USER_FILENAME)
            else:
                return

            self.appid = self.CONFIG.get('gae', 'appid')
            self.password = self.CONFIG.get('gae', 'password')
        except Exception as e:
            logging.exception("User_config.load except:%s", e)

    def save(self, appid, password):
        try:
            f = open(self.CONFIG_USER_FILENAME, 'w')
            if appid != "":
                f.write("[gae]\n")
                f.write("appid = %s\n" % appid)
                f.write("password = %s\n" % password)
            f.close()
        except:
            logging.warn("launcher.config save user config fail:%s", self.CONFIG_USER_FILENAME)


user_config = User_config()

def http_request(url, method="GET"):
    h = Http()
    resp, content = h.request(url, method)
    return content

class RemoveContralServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    deploy_proc = None

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_GET(self):
        path = urlparse.urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/status":
            return self.req_status_handler()
        elif path == '/deploy':
            return self.req_deploy_handler()
        elif path == "/ip_list":
            return self.req_ip_list_handler()
        elif path == "/ssl_pool":
            return self.req_ssl_pool_handler()
        elif path == "/quit":
            config.keep_run = False
            data = "Quit"
            self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % ('text/plain', len(data))).encode())
            self.wfile.write(data)
            return
        else:
            logging.warn('Control Req %s "%s %s ', self.address_string(), self.command, self.path)

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            logging.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return


        filename = os.path.normpath('./' + path)
        if self.path.startswith(('http://', 'https://')):
            data = b'HTTP/1.1 200\r\nCache-Control: max-age=86400\r\nExpires:Oct, 01 Aug 2100 00:00:00 GMT\r\nConnection: close\r\n'

            data += b'\r\n'
            self.wfile.write(data)
            logging.info('%s "%s %s HTTP/1.1" 200 -', self.address_string(), self.command, self.path)
        elif os.path.isfile(filename):
            if filename.endswith('.pac'):
                mimetype = 'text/plain'
            else:
                mimetype = 'application/octet-stream'
            #self.send_file(filename, mimetype)
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def do_POST(self):
        logging.debug ('HTTP %s "%s %s ', self.address_string(), self.command, self.path)
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
        if path == '/deploy':
            return self.req_deploy_handler()
        elif path == "/config":
            return self.req_config_handler()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_response(self, mimetype, data):
        mimetype = 'text/plain'
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
            logging.error('PAC %s "%s %s ', self.address_string(), self.command, self.path)

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_status_handler(self):
        import platform,sys

        if "user-agent" in self.headers.dict:
            user_agent = self.headers.dict["user-agent"]
        else:
            user_agent = ""

        gws_ip_num = len(google_ip.gws_ip_list)
        res_arr = {"gws_ip_num": gws_ip_num,
                   "sys_platform":sys.platform,
                   "os_system":platform.system(),
                   "os_version":platform.version(),
                   "os_release":platform.release(),
                   "browser":user_agent,
                   "goagent_version": config.__version__,
                   "python_version": config.python_version,
                   "proxy_listen":config.LISTEN_IP + ":" + str(config.LISTEN_PORT),
                   "gae_appid":config.GAE_APPIDS,
                   "pac_url":config.pac_url}
        data = json.dumps(res_arr)

        self.send_response('text/plain', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            if reqs['cmd'] == ['get_config']:
                user_config.load()
                data = '{ "appid": "%s", "passwd": "%s" }' % (user_config.appid, user_config.password)
            elif reqs['cmd'] == ['set_config']:
                appid = self.postvars['appid'][0]
                passwd = self.postvars['passwd'][0]
                user_config.save(appid=appid, password=passwd)

                data = '{"res":"success"}'
                self.send_response('text/plain', data)

                http_request("http://127.0.0.1:8085/init_module?module=goagent&cmd=restart")
                return
        except Exception as e:
            logging.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response('text/plain', data)


    def req_deploy_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        log_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'upload.log'))

        if reqs['cmd'] == ['deploy']:
            try:
                if os.path.isfile(log_path):
                    os.remove(log_path)
                script_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'uploader.py'))
                appid = self.postvars['appid'][0]
                email = self.postvars['email'][0]
                passwd = self.postvars['passwd'][0]
                self.deploy_proc = subprocess.Popen([sys.executable, script_path, appid, email, passwd], stdout=subprocess.PIPE)
                data = '{"res":"success"}'
            except Exception as e:
                data = '{"res":"fail", "error":"%s"}' % e

        elif reqs['cmd'] == ['get_log']:
            if os.path.isfile(log_path):
                with open(log_path, "r") as f:
                    content = f.read()
            else:
                content = ""

            if self.deploy_proc:
                proc_status = self.deploy_proc.poll()
                if not proc_status == None:
                    # process is ended
                    content += "\r\n== END ==\n"

            data = content


        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_ip_list_handler(self):
        data = ""
        i = 1
        for ip in google_ip.gws_ip_list:
            handshake_time = google_ip.ip_dict[ip]["handshake_time"]
            timeout = google_ip.ip_dict[ip]["timeout"]
            history = google_ip.ip_dict[ip]["history"]
            t0 = 0
            str = ''
            for item in history:
                t = item[0]
                v = item[1]
                if t0 == 0:
                    t0 = t
                time_per = int((t - t0) * 1000)
                t0 = t
                str += "%d(%s) " % (time_per, v)
            data += "%d \t %s      \t %d \t %d \t %s\r\n" % (i, ip, handshake_time, timeout, str)
            i += 1


        mimetype = 'text/plain'
        self.send_response(mimetype, data)


    def req_ssl_pool_handler(self):
        data = connect_manager.https_manager.conn_pool.to_string()

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

