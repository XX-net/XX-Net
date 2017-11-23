#!/usr/bin/env python
# coding:utf-8


import cgi
import datetime
import hashlib
import json
import locale
import os
import platform
import re
import subprocess
import sys
import time
import urllib2
import urlparse

from xlog import getLogger


xlog = getLogger("cloudflare_front")
from config import config

from scan_ip_log import scan_ip_log
import ConfigParser
import connect_control
import ip_utils
import check_local_network
import check_ip
import cert_util
import simple_http_server
import openssl_wrap
from front import front
from ip_manager import ip_manager

os.environ['HTTPS_PROXY'] = ''
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, os.pardir))
web_ui_path = os.path.join(current_path, os.path.pardir, "web_ui")


import yaml


class User_special(object):
    def __init__(self):
        self.appid = ''
        self.password = ''

        self.proxy_enable = "0"
        self.proxy_type = "HTTP"
        self.proxy_host = ""
        self.proxy_port = ""
        self.proxy_user = ""
        self.proxy_passwd = ""

        self.host_appengine_mode = "gae"
        self.auto_adjust_scan_ip_thread_num = 1
        self.scan_ip_thread_num = 0
        self.use_ipv6 = 0

class User_config(object):
    user_special = User_special()

    def __init__(self):
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(top_path, 'data', 'x_tunnel', 'cloudflare_config.ini'))
        self.load()

    def load(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')

        self.DEFAULT_CONFIG = ConfigParser.ConfigParser()
        DEFAULT_CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'default_config.ini'))


        self.USER_CONFIG = ConfigParser.ConfigParser()

        try:
            if os.path.isfile(DEFAULT_CONFIG_FILENAME):
                self.DEFAULT_CONFIG.read(DEFAULT_CONFIG_FILENAME)
            else:
                return

            if os.path.isfile(self.CONFIG_USER_FILENAME):
                self.USER_CONFIG.read(self.CONFIG_USER_FILENAME)
            else:
                return

            self.user_special.proxy_enable = self.USER_CONFIG.get('proxy', 'enable')
            self.user_special.proxy_type = self.USER_CONFIG.get('proxy', 'type')
            self.user_special.proxy_host = self.USER_CONFIG.get('proxy', 'host')
            self.user_special.proxy_port = self.USER_CONFIG.get('proxy', 'port')
            self.user_special.proxy_user = self.USER_CONFIG.get('proxy', 'user')
            self.user_special.proxy_passwd = self.USER_CONFIG.get('proxy', 'passwd')

        except Exception as e:
            xlog.warn("User_config.load except:%s", e)

    def save(self):
        try:
            f = open(self.CONFIG_USER_FILENAME, 'w')

            f.write("[proxy]\n")
            f.write("enable = %s\n" % self.user_special.proxy_enable)
            f.write("type = %s\n" % self.user_special.proxy_type)
            f.write("host = %s\n" % self.user_special.proxy_host)
            f.write("port = %s\n" % self.user_special.proxy_port)
            f.write("user = %s\n" % self.user_special.proxy_user)
            f.write("passwd = %s\n\n" % self.user_special.proxy_passwd)

            f.close()
            xlog.info("save config to %s", self.CONFIG_USER_FILENAME)
        except:
            xlog.exception("launcher.config save user config fail:%s", self.CONFIG_USER_FILENAME)


user_config = User_config()


def get_openssl_version():
    return "%s %s h2:%s" % (openssl_wrap.openssl_version,
                           openssl_wrap.ssl_version,
                           openssl_wrap.support_alpn_npn)

def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url)
    except Exception as e:
        xlog.exception("web_control http_request:%s fail:%s", url, e)
    return

deploy_proc = None


class ControlHandler(simple_http_server.HttpServerHandler):
    def __init__(self, client_address, headers, command, path, rfile, wfile):
        self.client_address = client_address
        self.headers = headers
        self.command = command
        self.path = path
        self.rfile = rfile
        self.wfile = wfile

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_GET(self):
        path = urlparse.urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/status":
            return self.req_status_handler()
        else:
            xlog.debug('cloudflare Web_control %s %s %s ', self.address_string(), self.command, self.path)

        if path == "/config":
            return self.req_config_handler()
        elif path == "/ip_list":
            return self.req_ip_list_handler()
        elif path == "/workers":
            return self.req_workers_handler()
        elif path == "/debug":
            return self.req_debug_handler()
        else:
            xlog.warn('Control Req %s %s %s ', self.address_string(), self.command, self.path)

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            xlog.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        filename = os.path.normpath('./' + path)
        if self.path.startswith(('http://', 'https://')):
            data = b'HTTP/1.1 200\r\nCache-Control: max-age=86400\r\nExpires:Oct, 01 Aug 2100 00:00:00 GMT\r\nConnection: close\r\n'

            data += b'\r\n'
            self.wfile.write(data)
            xlog.info('%s "%s %s HTTP/1.1" 200 -', self.address_string(), self.command, self.path)
        elif os.path.isfile(filename):
            if filename.endswith('.pac'):
                mimetype = 'text/plain'
            else:
                mimetype = 'application/octet-stream'
            #self.send_file(filename, mimetype)
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def do_POST(self):
        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                xlog.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

        xlog.debug ('cloudflare web_control %s %s %s ', self.address_string(), self.command, self.path)
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
            xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def req_log_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        cmd = "get_last"
        if reqs["cmd"]:
            cmd = reqs["cmd"][0]

        if cmd == "get_last":
            max_line = int(reqs["max_line"][0])
            data = xlog.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"][0])
            data = xlog.get_new_lines(last_no)
        else:
            xlog.error('PAC %s %s %s ', self.address_string(), self.command, self.path)

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def get_launcher_version(self):
        data_path = os.path.abspath( os.path.join(top_path, 'data', 'launcher', 'config.yaml'))
        try:
            config = yaml.load(file(data_path, 'r'))
            return config["modules"]["launcher"]["current_version"]
            #print yaml.dump(config)
        except yaml.YAMLError, exc:
            print "Error in configuration file:", exc
            return "unknown"

    @staticmethod
    def xxnet_version():
        version_file = os.path.join(root_path, "version.txt")
        try:
            with open(version_file, "r") as fd:
                version = fd.read()
            return version
        except Exception as e:
            xlog.exception("xxnet_version fail")
        return "get_version_fail"

    def get_os_language(self):
        if hasattr(self, "lang_code"):
            return self.lang_code

        try:
            lang_code, code_page = locale.getdefaultlocale()
            #('en_GB', 'cp1252'), en_US,
            self.lang_code = lang_code
            return lang_code
        except:
            #Mac fail to run this
            pass

        if sys.platform == "darwin":
            try:
                oot = os.pipe()
                p = subprocess.Popen(["/usr/bin/defaults", 'read', 'NSGlobalDomain', 'AppleLanguages'],stdout=oot[1])
                p.communicate()
                lang_code = os.read(oot[0],10000)
                self.lang_code = lang_code
                return lang_code
            except:
                pass

        lang_code = 'Unknown'
        return lang_code

    def req_status_handler(self):

        good_ip_num = ip_manager.good_ip_num
        if good_ip_num > len(ip_manager.gws_ip_list):
            good_ip_num = len(ip_manager.gws_ip_list)

        res_arr = {
                   "xxnet_version": self.xxnet_version(),
                   "python_version": platform.python_version(),
                   "openssl_version": get_openssl_version(),

                   "proxy_listen": config.LISTEN_IP + ":" + str(config.LISTEN_PORT),
                   "pac_url": config.pac_url,
                   "use_ipv6": config.CONFIG.getint("ip_manager", "use_ipv6"),

                   "network_state": check_local_network.network_stat,
                   "ip_num": len(ip_manager.gws_ip_list),
                   "good_ip_num": good_ip_num,
                   "scan_ip_thread_num": ip_manager.scan_thread_count,
                   "ip_quality": ip_manager.ip_quality(),
                   "block_stat": connect_control.block_stat(),

                   "high_prior_connecting_num": connect_control.high_prior_connecting_num,
                   "low_prior_connecting_num": connect_control.low_prior_connecting_num,
                   "high_prior_lock": len(connect_control.high_prior_lock),
                   "low_prior_lock": len(connect_control.low_prior_lock),
                   }
        data = json.dumps(res_arr, indent=0, sort_keys=True)
        self.send_response_nc('text/html', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        appid_updated = False

        try:
            if reqs['cmd'] == ['get_config']:
                data = json.dumps(user_config.user_special, default=lambda o: o.__dict__)
            elif reqs['cmd'] == ['set_config']:
                appids = self.postvars['appid'][0]
                if appids != user_config.user_special.appid:
                    user_config.user_special.appid = appids

                user_config.user_special.proxy_enable = self.postvars['proxy_enable'][0]
                user_config.user_special.proxy_type = self.postvars['proxy_type'][0]
                user_config.user_special.proxy_host = self.postvars['proxy_host'][0]
                user_config.user_special.proxy_port = self.postvars['proxy_port'][0]
                try:
                    user_config.user_special.proxy_port = int(user_config.user_special.proxy_port)
                except:
                    user_config.user_special.proxy_port = 0

                user_config.user_special.proxy_user = self.postvars['proxy_user'][0]
                user_config.user_special.proxy_passwd = self.postvars['proxy_passwd'][0]
                user_config.user_special.host_appengine_mode = self.postvars['host_appengine_mode'][0]

                use_ipv6 = int(self.postvars['use_ipv6'][0])
                if user_config.user_special.use_ipv6 != use_ipv6:
                    if use_ipv6:
                        if not check_local_network.check_ipv6():
                            xlog.warn("IPv6 was enabled, but check failed.")
                            return self.send_response_nc('text/html', '{"res":"fail", "reason":"IPv6 fail"}')

                    user_config.user_special.use_ipv6 = use_ipv6

                user_config.save()

                config.load()

                ip_manager.reset()
                check_ip.load_proxy_config()

                data = '{"res":"success"}'
                self.send_response_nc('text/html', data)
                #http_request("http://127.0.0.1:8085/init_module?module=gae_proxy&cmd=restart")
                return
        except Exception as e:
            xlog.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response_nc('text/html', data)

    def req_ip_list_handler(self):
        time_now = time.time()
        data = "<html><body><div  style='float: left; white-space:nowrap;font-family: monospace;'>"
        data += "time:%d  pointer:%d<br>\r\n" % (time_now, ip_manager.gws_ip_pointer)
        data += "<table><tr><th>N</th><th>IP</th><th>HS</th><th>Fails</th>"
        data += "<th>down_fail</th><th>links</th>"
        data += "<th>get_time</th><th>success_time</th><th>fail_time</th><th>down_fail_time</th>"
        data += "<th>data_active</th><th>transfered_data</th><th>Trans</th>"
        data += "<th>history</th></tr>\n"
        i = 1
        for ip in ip_manager.gws_ip_list:
            handshake_time = ip_manager.ip_dict[ip]["handshake_time"]

            fail_times = ip_manager.ip_dict[ip]["fail_times"]
            down_fail = ip_manager.ip_dict[ip]["down_fail"]
            links = ip_manager.ip_dict[ip]["links"]

            get_time = ip_manager.ip_dict[ip]["get_time"]
            if get_time:
                get_time = time_now - get_time

            success_time = ip_manager.ip_dict[ip]["success_time"]
            if success_time:
                success_time = time_now - success_time

            fail_time = ip_manager.ip_dict[ip]["fail_time"]
            if fail_time:
                fail_time = time_now - fail_time

            down_fail_time = ip_manager.ip_dict[ip]["down_fail_time"]
            if down_fail_time:
                down_fail_time = time_now - down_fail_time

            data_active = ip_manager.ip_dict[ip]["data_active"]
            if data_active:
                active_time = time_now - data_active
            else:
                active_time = 0

            history = ip_manager.ip_dict[ip]["history"]
            t0 = 0
            str_out = ''
            for item in history:
                t = item[0]
                v = item[1]
                if t0 == 0:
                    t0 = t
                time_per = int((t - t0) * 1000)
                t0 = t
                str_out += "%d(%s) " % (time_per, v)
            data += "<tr><td>%d</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>" \
                    "<td>%d</td><td>%d</td><td>%s</td></tr>\n" % \
                    (i, ip, handshake_time, fail_times, down_fail, links, get_time, success_time, fail_time, down_fail_time, \
                    active_time, str_out)
            i += 1

        data += "</table></div></body></html>"
        mimetype = 'text/html'
        self.send_response_nc(mimetype, data)

    def req_workers_handler(self):
        out_str = ""
        for host in front.dispatchs:
            http_dispatch = front.dispatchs[host]
            data = http_dispatch.to_string()
            out_str += "  %s:\n %s" % (host, data)

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, out_str)

    def req_debug_handler(self):
        data = ""
        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)