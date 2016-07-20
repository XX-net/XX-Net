#!/usr/bin/env python
# coding:utf-8


import platform
import env_info
import urlparse
import json
import os
import re
import subprocess
import cgi
import urllib2
import sys
import datetime
import locale
import time
import hashlib


from xlog import getLogger


xlog = getLogger("gae_proxy")
from config import config
from appids_manager import appid_manager
from google_ip import google_ip
from google_ip_range import ip_range
from connect_manager import https_manager
from scan_ip_log import scan_ip_log
import ConfigParser
import connect_control
import ip_utils
import check_local_network
import check_ip
import cert_util
import simple_http_server
import test_appid
from http_dispatcher import http_dispatch
import openssl_wrap


os.environ['HTTPS_PROXY'] = ''
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))
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
        self.load()

    def load(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')

        self.DEFAULT_CONFIG = ConfigParser.ConfigParser()
        DEFAULT_CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'proxy.ini'))


        self.USER_CONFIG = ConfigParser.ConfigParser()
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(top_path, 'data', 'gae_proxy', 'config.ini'))

        try:
            if os.path.isfile(DEFAULT_CONFIG_FILENAME):
                self.DEFAULT_CONFIG.read(DEFAULT_CONFIG_FILENAME)
                self.user_special.scan_ip_thread_num = self.DEFAULT_CONFIG.getint('google_ip', 'max_scan_ip_thread_num')
            else:
                return

            if os.path.isfile(CONFIG_USER_FILENAME):
                self.USER_CONFIG.read(CONFIG_USER_FILENAME)
            else:
                return

            try:
                self.user_special.appid = self.USER_CONFIG.get('gae', 'appid')
                self.user_special.password = self.USER_CONFIG.get('gae', 'password')
            except:
                pass

            try:
                self.user_special.host_appengine_mode = self.USER_CONFIG.get('hosts', 'appengine.google.com')
            except:
                pass

            try:
                self.user_special.scan_ip_thread_num = config.CONFIG.getint('google_ip', 'max_scan_ip_thread_num')
            except:
                self.user_special.scan_ip_thread_num = self.DEFAULT_CONFIG.getint('google_ip', 'max_scan_ip_thread_num')

            try:
                self.user_special.auto_adjust_scan_ip_thread_num = config.CONFIG.getint('google_ip', 'auto_adjust_scan_ip_thread_num')
            except:
                pass

            try:
                self.user_special.use_ipv6 = config.CONFIG.getint('google_ip', 'use_ipv6')
            except:
                pass

            self.user_special.proxy_enable = self.USER_CONFIG.get('proxy', 'enable')
            self.user_special.proxy_type = self.USER_CONFIG.get('proxy', 'type')
            self.user_special.proxy_host = self.USER_CONFIG.get('proxy', 'host')
            self.user_special.proxy_port = self.USER_CONFIG.get('proxy', 'port')
            self.user_special.proxy_user = self.USER_CONFIG.get('proxy', 'user')
            self.user_special.proxy_passwd = self.USER_CONFIG.get('proxy', 'passwd')

        except Exception as e:
            xlog.warn("User_config.load except:%s", e)

    def save(self):
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(top_path, 'data', 'gae_proxy', 'config.ini'))
        try:
            f = open(CONFIG_USER_FILENAME, 'w')
            if self.user_special.appid != "":
                f.write("[gae]\n")
                f.write("appid = %s\n" % self.user_special.appid)
                f.write("password = %s\n\n" % self.user_special.password)

            f.write("[proxy]\n")
            f.write("enable = %s\n" % self.user_special.proxy_enable)
            f.write("type = %s\n" % self.user_special.proxy_type)
            f.write("host = %s\n" % self.user_special.proxy_host)
            f.write("port = %s\n" % self.user_special.proxy_port)
            f.write("user = %s\n" % self.user_special.proxy_user)
            f.write("passwd = %s\n\n" % self.user_special.proxy_passwd)

            """
            if self.user_special.host_appengine_mode != "gae":
                f.write("[hosts]\n")
                f.write("appengine.google.com = %s\n" % self.user_special.host_appengine_mode)
                f.write("www.google.com = %s\n\n" % self.user_special.host_appengine_mode)
            """

            f.write("[google_ip]\n")

            if int(self.user_special.auto_adjust_scan_ip_thread_num) != self.DEFAULT_CONFIG.getint('google_ip', 'auto_adjust_scan_ip_thread_num'):
                f.write("auto_adjust_scan_ip_thread_num = %d\n\n" % int(self.user_special.auto_adjust_scan_ip_thread_num))
            if int(self.user_special.scan_ip_thread_num) != self.DEFAULT_CONFIG.getint('google_ip', 'max_scan_ip_thread_num'):
                f.write("max_scan_ip_thread_num = %d\n\n" % int(self.user_special.scan_ip_thread_num))

            if int(self.user_special.use_ipv6) != self.DEFAULT_CONFIG.getint('google_ip', 'use_ipv6'):
                f.write("use_ipv6 = %d\n\n" % int(self.user_special.use_ipv6))

            f.close()
        except:
            xlog.warn("launcher.config save user config fail:%s", CONFIG_USER_FILENAME)


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
            xlog.debug('GAEProxy Web_control %s %s %s ', self.address_string(), self.command, self.path)


        if path == '/deploy':
            return self.req_deploy_handler()
        elif path == "/config":
            return self.req_config_handler()
        elif path == "/ip_list":
            return self.req_ip_list_handler()
        elif path == "/scan_ip":
            return self.req_scan_ip_handler()
        elif path == "/ssl_pool":
            return self.req_ssl_pool_handler()
        elif path == "/workers":
            return self.req_workers_handler()
        elif path == "/download_cert":
            return self.req_download_cert_handler()
        elif path == "/is_ready":
            return self.req_is_ready_handler()
        elif path == "/test_ip":
            return self.req_test_ip_handler()
        elif path == "/check_ip":
            return self.req_check_ip_handler()
        elif path == "/quit":
            connect_control.keep_running = False
            data = "Quit"
            self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % ('text/plain', len(data))).encode())
            self.wfile.write(data)
            #sys.exit(0)
            #quit()
            #os._exit(0)
            return
        elif path.startswith("/wizard/"):
            file_path = os.path.abspath(os.path.join(web_ui_path, '/'.join(path.split('/')[1:])))
            if not os.path.isfile(file_path):
                self.wfile.write(b'HTTP/1.1 404 Not Found\r\n\r\n')
                xlog.warn('%s %s %s wizard file %s not found', self.address_string(), self.command, self.path, file_path)
                return

            if file_path.endswith('.html'):
                mimetype = 'text/html'
            elif file_path.endswith('.png'):
                mimetype = 'image/png'
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                mimetype = 'image/jpeg'
            else:
                mimetype = 'application/octet-stream'

            self.send_file(file_path, mimetype)
            return
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

        xlog.debug ('GAEProxy web_control %s %s %s ', self.address_string(), self.command, self.path)
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
        elif path == "/scan_ip":
            return self.req_scan_ip_handler()
        elif path.startswith("/importip"):
            return self.req_importip_handler()
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
        if cmd == "set_buffer_size" :
            if not reqs["buffer_size"]:
                data = '{"res":"fail", "reason":"size not set"}'
                mimetype = 'text/plain'
                self.send_response_nc(mimetype, data)
                return

            buffer_size = reqs["buffer_size"][0]
            xlog.set_buffer_size(buffer_size)
        elif cmd == "get_last":
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
        if "user-agent" in self.headers.dict:
            user_agent = self.headers.dict["user-agent"]
        else:
            user_agent = ""

        good_ip_num = google_ip.good_ip_num
        if good_ip_num > len(google_ip.gws_ip_list):
            good_ip_num = len(google_ip.gws_ip_list)

        res_arr = {
                   "sys_platform": "%s, %s" % (platform.machine(), platform.platform()),
                   "os_system": platform.system(),
                   "os_version": platform.version(),
                   "os_release": platform.release(),
                   "architecture": platform.architecture(),
                   "os_detail": env_info.os_detail(),
                   "language": self.get_os_language(),
                   "browser": user_agent,
                   "xxnet_version": self.xxnet_version(),
                   "python_version": platform.python_version(),
                   "openssl_version": get_openssl_version(),

                   "proxy_listen": config.LISTEN_IP + ":" + str(config.LISTEN_PORT),
                   "pac_url": config.pac_url,
                   "use_ipv6": config.CONFIG.getint("google_ip", "use_ipv6"),

                   "gae_appid": "|".join(config.GAE_APPIDS),
                   "working_appid": "|".join(appid_manager.working_appid_list),
                   "out_of_quota_appids": "|".join(appid_manager.out_of_quota_appids),
                   "not_exist_appids": "|".join(appid_manager.not_exist_appids),

                   "network_state": check_local_network.network_stat,
                   "ip_num": len(google_ip.gws_ip_list),
                   "good_ip_num": good_ip_num,
                   "connected_link_new": len(https_manager.new_conn_pool.pool),
                   "connected_link_used": len(https_manager.gae_conn_pool.pool),
                   "worker_h1": http_dispatch.h1_num,
                   "worker_h2": http_dispatch.h2_num,
                   "is_idle": int(http_dispatch.is_idle()),
                   "scan_ip_thread_num": google_ip.scan_thread_count,
                   "ip_quality": google_ip.ip_quality(),
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
                    if appids and google_ip.good_ip_num:
                        fail_appid_list = test_appid.test_appids(appids)
                        if len(fail_appid_list):
                            fail_appid = "|".join(fail_appid_list)
                            return self.send_response_nc('text/html', '{"res":"fail", "reason":"appid fail:%s"}' % fail_appid)

                    appid_updated = True
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
                appid_manager.reset_appid()
                import connect_manager
                connect_manager.load_proxy_config()
                connect_manager.https_manager.load_config()
                if appid_updated:
                    http_dispatch.close_all_worker()

                google_ip.reset()
                check_ip.load_proxy_config()

                data = '{"res":"success"}'
                self.send_response_nc('text/html', data)
                #http_request("http://127.0.0.1:8085/init_module?module=gae_proxy&cmd=restart")
                return
        except Exception as e:
            xlog.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response_nc('text/html', data)


    def req_deploy_handler(self):
        global deploy_proc
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        log_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'upload.log'))
        time_now = datetime.datetime.today().strftime('%H:%M:%S-%a/%d/%b/%Y')

        if reqs['cmd'] == ['deploy']:
            appid = self.postvars['appid'][0]
            debug = int(self.postvars['debug'][0])

            if deploy_proc and deploy_proc.poll() == None:
                xlog.warn("deploy is running, request denied.")
                data = '{"res":"deploy is running", "time":"%s"}' % time_now

            else:
                try:
                    if os.path.isfile(log_path):
                        os.remove(log_path)
                    script_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'uploader.py'))

                    args = [sys.executable, script_path, appid]
                    if debug:
                        args.append("-debug")

                    deploy_proc = subprocess.Popen(args)
                    xlog.info("deploy begin.")
                    data = '{"res":"success", "time":"%s"}' % time_now
                except Exception as e:
                    data = '{"res":"%s", "time":"%s"}' % (e, time_now)

        elif reqs['cmd'] == ['cancel']:
            if deploy_proc and deploy_proc.poll() == None:
                deploy_proc.kill()
                data = '{"res":"deploy is killed", "time":"%s"}' % time_now
            else:
                data = '{"res":"deploy is not running", "time":"%s"}' % time_now

        elif reqs['cmd'] == ['get_log']:
            if deploy_proc and os.path.isfile(log_path):
                with open(log_path, "r") as f:
                    content = f.read()
            else:
                content = ""

            status = 'init'
            if deploy_proc:
                if deploy_proc.poll() == None:
                    status = 'running'
                else:
                    status = 'finished'

            data = json.dumps({'status': status, 'log': content, 'time': time_now})

        self.send_response_nc('text/html', data)

    def req_importip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['importip']:
            count = 0
            ip_list = self.postvars['ipList'][0]
            addresses = ip_list.split('|')
            for ip in addresses:
                if not ip_utils.check_ip_valid(ip):
                    continue
                if google_ip.add_ip(ip, 100, "google.com", "gws"):
                    count += 1
            data = '{"res":"%s"}' % count
            google_ip.save_ip_list(force=True)

        elif reqs['cmd'] == ['exportip']:
            data = '{"res":"'
            for ip in google_ip.gws_ip_list:
                if google_ip.ip_dict[ip]['fail_times'] > 0:
                    continue
                data += "%s|" % ip
            data = data[0: len(data) - 1]
            data += '"}'

        self.send_response_nc('text/html', data)

    def req_test_ip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)

        ip = reqs['ip'][0]
        result = check_ip.test_gae_ip2(ip)
        if not result or not result.support_gae:
            data = "{'res':'fail'}"
        else:
            data = json.dumps("{'ip':'%s', 'handshake':'%s', 'server':'%s', 'domain':'%s'}" %
                  (ip, result.handshake_time, result.server_type, result.domain))

        self.send_response_nc('text/html', data)

    def req_ip_list_handler(self):
        time_now = time.time()
        data = "<html><body><div  style='float: left; white-space:nowrap;font-family: monospace;'>"
        data += "time:%d  pointer:%d<br>\r\n" % (time_now, google_ip.gws_ip_pointer)
        data += "<table><tr><th>N</th><th>IP</th><th>HS</th><th>Fails</th>"
        data += "<th>down_fail</th><th>links</th>"
        data += "<th>get_time</th><th>success_time</th><th>fail_time</th><th>down_fail_time</th>"
        data += "<th>data_active</th><th>transfered_data</th><th>Trans</th>"
        data += "<th>history</th></tr>\n"
        i = 1
        for ip in google_ip.gws_ip_list:
            handshake_time = google_ip.ip_dict[ip]["handshake_time"]

            fail_times = google_ip.ip_dict[ip]["fail_times"]
            down_fail = google_ip.ip_dict[ip]["down_fail"]
            links = google_ip.ip_dict[ip]["links"]

            get_time = google_ip.ip_dict[ip]["get_time"]
            if get_time:
                get_time = time_now - get_time

            success_time = google_ip.ip_dict[ip]["success_time"]
            if success_time:
                success_time = time_now - success_time

            fail_time = google_ip.ip_dict[ip]["fail_time"]
            if fail_time:
                fail_time = time_now - fail_time

            down_fail_time = google_ip.ip_dict[ip]["down_fail_time"]
            if down_fail_time:
                down_fail_time = time_now - down_fail_time

            data_active = google_ip.ip_dict[ip]["data_active"]
            if data_active:
                active_time = time_now - data_active
            else:
                active_time = 0

            history = google_ip.ip_dict[ip]["history"]
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

    def req_scan_ip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ""
        if reqs['cmd'] == ['get_range']:
            data = ip_range.load_range_content()

        elif reqs['cmd'] == ['update']:
            #update ip_range if needed
            content = self.postvars['ip_range'][0]

            #check ip_range checksums, update if needed
            default_digest = hashlib.md5(ip_range.load_range_content(default=True)).hexdigest()
            old_digest = hashlib.md5(ip_range.load_range_content()).hexdigest()
            new_digest = hashlib.md5(content).hexdigest()

            if new_digest == default_digest:
                ip_range.remove_user_range()

            else:
                if old_digest != new_digest:
                    ip_range.update_range_content(content)

            if old_digest != new_digest:
                ip_range.load_ip_range()

            #update auto_adjust_scan_ip and scan_ip_thread_num
            should_auto_adjust_scan_ip = int(self.postvars['auto_adjust_scan_ip_thread_num'][0])
            thread_num_for_scan_ip = int(self.postvars['scan_ip_thread_num'][0])

            #update user config settings
            user_config.user_special.auto_adjust_scan_ip_thread_num = should_auto_adjust_scan_ip
            user_config.user_special.scan_ip_thread_num = thread_num_for_scan_ip
            user_config.save()

            #update google_ip settings
            google_ip.auto_adjust_scan_ip_thread_num = should_auto_adjust_scan_ip

            if google_ip.max_scan_ip_thread_num != thread_num_for_scan_ip:
                google_ip.adjust_scan_thread_num(thread_num_for_scan_ip)

            #reponse 
            data='{"res":"success"}'

        elif reqs['cmd'] == ['get_scan_ip_log']:
            data = scan_ip_log.get_log_content()

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def req_ssl_pool_handler(self):
        data = "New conn:\n"
        data += https_manager.new_conn_pool.to_string()

        data += "\nGAE conn:\n"
        data += https_manager.gae_conn_pool.to_string()

        for host in https_manager.host_conn_pool:
            data += "\nHost:%s\n" % host
            data += https_manager.host_conn_pool[host].to_string()

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def req_workers_handler(self):
        data = http_dispatch.to_string()

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def req_download_cert_handler(self):
        filename = cert_util.CertUtil.ca_keyfile
        with open(filename, 'rb') as fp:
            data = fp.read()
        mimetype = 'application/x-x509-ca-cert'

        self.wfile.write(('HTTP/1.1 200\r\nContent-Disposition: inline; filename=CA.crt\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def req_is_ready_handler(self):
        data = "%s" % config.cert_import_ready

        mimetype = 'text/plain'
        self.send_response_nc(mimetype, data)

    def req_check_ip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ""
        if reqs['cmd'] == ['get_process']:
            all_ip_num = len(google_ip.ip_dict)
            left_num = google_ip.scan_exist_ip_queue.qsize()
            good_num = google_ip.good_ip_num
            data = json.dumps(dict(all_ip_num=all_ip_num, left_num=left_num, good_num=good_num))
            self.send_response_nc('text/plain', data)
        elif reqs['cmd'] == ['start']:
            left_num = google_ip.scan_exist_ip_queue.qsize()
            if left_num:
                self.send_response_nc('text/plain', '{"res":"fail", "reason":"running"}')
            else:
                google_ip.start_scan_all_exist_ip()
                self.send_response_nc('text/plain', '{"res":"success"}')
        elif reqs['cmd'] == ['stop']:
            left_num = google_ip.scan_exist_ip_queue.qsize()
            if not left_num:
                self.send_response_nc('text/plain', '{"res":"fail", "reason":"not running"}')
            else:
                google_ip.stop_scan_all_exist_ip()
                self.send_response_nc('text/plain', '{"res":"success"}')
        else:
            return self.send_not_exist()
