#!/usr/bin/env python
# coding:utf-8

import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))
web_ui_path = os.path.join(current_path, os.path.pardir, "web_ui")

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


import xlog
from config import config
from appids_manager import appid_manager
from google_ip import google_ip
from google_ip_range import ip_range
from connect_manager import https_manager
from scan_ip_log import scan_ip_log
import ConfigParser
import connect_control
import ip_utils
import check_ip
import cert_util

os.environ['HTTPS_PROXY'] = ''
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

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
        self.ip_connect_interval = 10
        self.auto_adjust_scan_ip_thread_num = 1
        self.scan_ip_thread_num = 0
        self.use_ipv6 = 0
        self.connect_interval = 200

class User_config(object):
    user_special = User_special()

    def __init__(self):
        self.load()

    def load(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')

        self.DEFAULT_CONFIG = ConfigParser.ConfigParser()
        DEFAULT_CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'proxy.ini'))


        self.USER_CONFIG = ConfigParser.ConfigParser()
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, 'data', 'gae_proxy', 'config.ini'))

        try:
            if os.path.isfile(DEFAULT_CONFIG_FILENAME):
                self.DEFAULT_CONFIG.read(DEFAULT_CONFIG_FILENAME)
                self.user_special.scan_ip_thread_num = self.DEFAULT_CONFIG.getint('google_ip', 'max_scan_ip_thread_num')
                self.ip_connect_interval = self.DEFAULT_CONFIG.getint('google_ip', 'ip_connect_interval')
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
                self.user_special.ip_connect_interval = config.CONFIG.getint('google_ip', 'ip_connect_interval')
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

            try:
                self.user_special.connect_interval = config.CONFIG.getint("connect_manager", "connect_interval")
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
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, 'data', 'gae_proxy', 'config.ini'))
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

            if self.user_special.host_appengine_mode != "gae":
                f.write("[hosts]\n")
                f.write("appengine.google.com = %s\n" % self.user_special.host_appengine_mode)
                f.write("www.google.com = %s\n\n" % self.user_special.host_appengine_mode)

            f.write("[google_ip]\n")
            if self.user_special.ip_connect_interval != self.DEFAULT_CONFIG.getint('google_ip', 'ip_connect_interval'):
                f.write("ip_connect_interval = %d\n" % int(self.user_special.ip_connect_interval))

            if int(self.user_special.auto_adjust_scan_ip_thread_num) != self.DEFAULT_CONFIG.getint('google_ip', 'auto_adjust_scan_ip_thread_num'):
                f.write("auto_adjust_scan_ip_thread_num = %d\n\n" % int(self.user_special.auto_adjust_scan_ip_thread_num))
            if int(self.user_special.scan_ip_thread_num) != self.DEFAULT_CONFIG.getint('google_ip', 'max_scan_ip_thread_num'):
                f.write("max_scan_ip_thread_num = %d\n\n" % int(self.user_special.scan_ip_thread_num))

            if int(self.user_special.use_ipv6) != self.DEFAULT_CONFIG.getint('google_ip', 'use_ipv6'):
                f.write("use_ipv6 = %d\n\n" % int(self.user_special.use_ipv6))

            f.write("[connect_manager]\n")
            if int(self.user_special.connect_interval) != self.DEFAULT_CONFIG.getint('connect_manager', 'connect_interval'):
                f.write("connect_interval = %d\n\n" % int(self.user_special.connect_interval))

            f.close()
        except:
            xlog.warn("launcher.config save user config fail:%s", CONFIG_USER_FILENAME)


user_config = User_config()




def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url)
    except Exception as e:
        xlog.exception("web_control http_request:%s fail:%s", url, e)
    return

deploy_proc = None
class ControlHandler():

    def __init__(self, client_address, headers, command, path, rfile, wfile):
        self.client_address = client_address
        self.headers = headers
        self.command = command
        self.path = path
        self.rfile = rfile
        self.wfile = wfile

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_GET(self):

        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                xlog.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

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
        elif path == "/download_cert":
            return self.req_download_cert_handler()
        elif path == "/is_ready":
            return self.req_is_ready_handler()
        elif path == "/test_ip":
            return self.req_test_ip_handler()
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
        self.send_response(mimetype, data)

    def get_launcher_version(self):
        data_path = os.path.abspath( os.path.join(root_path, 'data', 'launcher', 'config.yaml'))
        try:
            config = yaml.load(file(data_path, 'r'))
            return config["modules"]["launcher"]["current_version"]
            #print yaml.dump(config)
        except yaml.YAMLError, exc:
            print "Error in configuration file:", exc
            return "unknown"

    @staticmethod
    def xxnet_version():
        readme_file = os.path.join(root_path, "README.md")
        try:
            fd = open(readme_file, "r")
            lines = fd.readlines()
            import re
            p = re.compile(r'https://codeload.github.com/XX-net/XX-Net/zip/([0-9]+)\.([0-9]+)\.([0-9]+)') #zip/([0-9]+).([0-9]+).([0-9]+)
            #m = p.match(content)
            for line in lines:
                m = p.match(line)
                if m:
                    version = m.group(1) + "." + m.group(2) + "." + m.group(3)
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

        gws_ip_num = len(google_ip.gws_ip_list)
        res_arr = {"gws_ip_num": gws_ip_num,
                   "sys_platform":"%s, %s" % (platform.machine(), platform.platform()),
                   "os_system":platform.system(),
                   "os_version":platform.version(),
                   "os_release":platform.release(),
                   "architecture":platform.architecture(),
                   "os_detail":env_info.os_detail(),
                   "language":self.get_os_language(),
                   "browser":user_agent,
                   "xxnet_version":self.xxnet_version(),
                   "python_version": platform.python_version(),
                   "proxy_listen":config.LISTEN_IP + ":" + str(config.LISTEN_PORT),
                   "gae_appid":"|".join(config.GAE_APPIDS),
                   "connected_link":"%d,%d" % (len(https_manager.new_conn_pool.pool), len(https_manager.gae_conn_pool.pool)),
                   "working_appid":"|".join(appid_manager.working_appid_list),
                   "out_of_quota_appids":"|".join(appid_manager.out_of_quota_appids),
                   "not_exist_appids":"|".join(appid_manager.not_exist_appids),
                   "pac_url":config.pac_url,
                   "ip_connect_interval":config.CONFIG.getint("google_ip", "ip_connect_interval"),
                   "scan_ip_thread_num":google_ip.searching_thread_count,
                   "ip_handshake_100":google_ip.ip_handshake_th(100),
                   "block_stat":connect_control.block_stat(),
                   "use_ipv6":config.CONFIG.getint("google_ip", "use_ipv6"),
                   "high_prior_connecting_num":connect_control.high_prior_connecting_num,
                   "low_prior_connecting_num":connect_control.low_prior_connecting_num,
                   "high_prior_lock":len(connect_control.high_prior_lock),
                   "low_prior_lock":len(connect_control.low_prior_lock),
                   }
        data = json.dumps(res_arr, indent=0, sort_keys=True)
        self.send_response('text/html', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            if reqs['cmd'] == ['get_config']:
                data = json.dumps(user_config.user_special, default=lambda o: o.__dict__)
            elif reqs['cmd'] == ['set_config']:
                user_config.user_special.appid = self.postvars['appid'][0]
                user_config.user_special.password = self.postvars['password'][0]
                user_config.user_special.proxy_enable = self.postvars['proxy_enable'][0]
                user_config.user_special.proxy_type = self.postvars['proxy_type'][0]
                user_config.user_special.proxy_host = self.postvars['proxy_host'][0]
                user_config.user_special.proxy_port = self.postvars['proxy_port'][0]
                user_config.user_special.proxy_user = self.postvars['proxy_user'][0]
                user_config.user_special.proxy_passwd = self.postvars['proxy_passwd'][0]
                user_config.user_special.host_appengine_mode = self.postvars['host_appengine_mode'][0]
                user_config.user_special.ip_connect_interval = int(self.postvars['ip_connect_interval'][0])
                user_config.user_special.use_ipv6 = int(self.postvars['use_ipv6'][0])
                user_config.user_special.connect_interval = int(self.postvars['connect_interval'][0])
                user_config.save()

                config.load()
                appid_manager.reset_appid()
                import connect_manager
                connect_manager.load_sock()
                connect_manager.https_manager.load_config()
                connect_manager.forwork_manager.load_config()

                google_ip.load_config()
                check_ip.load_sock()

                data = '{"res":"success"}'
                self.send_response('text/html', data)
                #http_request("http://127.0.0.1:8085/init_module?module=gae_proxy&cmd=restart")
                return
        except Exception as e:
            xlog.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response('text/html', data)


    def req_deploy_handler(self):
        global deploy_proc
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        log_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'upload.log'))
        time_now = datetime.datetime.today().strftime('%H:%M:%S-%a/%d/%b/%Y')

        if reqs['cmd'] == ['deploy']:
            appid = self.postvars['appid'][0]

            if deploy_proc and deploy_proc.poll() == None:
                xlog.warn("deploy is running, request denied.")
                data = '{"res":"deploy is running", "time":"%s"}' % (time_now)

            else:
                try:
                    if os.path.isfile(log_path):
                        os.remove(log_path)
                    script_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'uploader.py'))

                    email = self.postvars['email'][0]
                    passwd = self.postvars['passwd'][0]
                    rc4_passwd = self.postvars['rc4_passwd'][0]
                    deploy_proc = subprocess.Popen([sys.executable, script_path, appid, email, passwd, rc4_passwd])
                    xlog.info("deploy begin.")
                    data = '{"res":"success", "time":"%s"}' % time_now
                except Exception as e:
                    data = '{"res":"%s", "time":"%s"}' % (e, time_now)

        elif reqs['cmd'] == ['cancel']:
            if deploy_proc and deploy_proc.poll() == None:
                deploy_proc.kill()
                data = '{"res":"deploy is killed", "time":"%s"}' % (time_now)
            else:
                data = '{"res":"deploy is not running", "time":"%s"}' % (time_now)

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

            data = json.dumps({'status':status,'log':content, 'time':time_now})

        self.send_response('text/html', data)

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
                data += "%s|" % ip
            data = data[0 : len(data) - 1]
            data += '"}'

        self.send_response('text/html', data)

    def req_test_ip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        ip = reqs['ip'][0]
        result = check_ip.test_gws(ip)
        if not result:
            data = "{'res':'fail'}"
        else:
            data = json.dumps("{'ip':'%s', 'handshake':'%s', 'server':'%s', 'domain':'%s'}" %
                  (ip, result.handshake_time, result.server_type, result.domain))

        self.send_response('text/html', data)

    def req_ip_list_handler(self):
        time_now = time.time()
        data = ""
        data += "pointer:%d\r\n" % google_ip.gws_ip_pointer
        data += "N \t IP      \t\t Han \t Fail \t Trans \t Tran_t \t his\r\n"
        i = 1
        for ip in google_ip.gws_ip_list:
            handshake_time = google_ip.ip_dict[ip]["handshake_time"]
            fail_times = google_ip.ip_dict[ip]["fail_times"]
            transfered_data = google_ip.ip_dict[ip]["transfered_data"]
            data_active = google_ip.ip_dict[ip]["data_active"]
            if data_active:
                data_active = time_now - data_active
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
            data += "%d \t %s      \t %d \t %d \t %d \t %d \t %s\r\n" % \
                    (i, ip, handshake_time, fail_times, transfered_data, data_active, str)
            i += 1

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_scan_ip_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ""
        if reqs['cmd'] == ['get_range']:
            data = ip_range.load_range_content()
        elif reqs['cmd'] == ['set_range']:
            content = self.postvars['ip_range'][0]
            ip_range.update_range_content(content)
            ip_range.load_ip_range()
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['set_auto_adjust_scan_ip_thread_num']:
            user_config.user_special.auto_adjust_scan_ip_thread_num = int(self.postvars['auto_adjust_scan_ip_thread_num'][0])
            user_config.save()

            google_ip.auto_adjust_scan_ip_thread_num = user_config.user_special.auto_adjust_scan_ip_thread_num
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['set_scan_thread_num']:
            user_config.user_special.scan_ip_thread_num = int(self.postvars['scan_ip_thread_num'][0])
            user_config.save()

            scan_ip_thread_num = int(self.postvars['scan_ip_thread_num'][0])
            google_ip.update_scan_thread_num(scan_ip_thread_num)
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['get_scan_ip_log']:
            data = scan_ip_log.get_log_content()

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_ssl_pool_handler(self):
        data = https_manager.gae_conn_pool.to_string()

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_download_cert_handler(self):
        filename = cert_util.CertUtil.ca_keyfile
        with open(filename, 'rb') as fp:
            data = fp.read()
        mimetype = "text/plain"

        self.wfile.write(('HTTP/1.1 200\r\nContent-Disposition: attachment; filename=CA.crt\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def req_is_ready_handler(self):
        data = "%s" % config.cert_import_ready

        mimetype = 'text/plain'
        self.send_response(mimetype, data)
