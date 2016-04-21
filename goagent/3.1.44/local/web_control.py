#!/usr/bin/env python
# coding:utf-8

import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, 'python27', '1.0'))

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
import datetime

import logging
from config import config
from appids_manager import appid_manager
from google_ip import google_ip
import connect_manager
import ConfigParser

os.environ['HTTPS_PROXY'] = ''
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir, os.pardir))

import yaml

class User_config(object):
    appid = ''
    password = ''

    proxy_enable = "0"
    proxy_type = "HTTP"
    proxy_host = ""
    proxy_port = ""
    proxy_user = ""
    proxy_passwd = ""

    def __init__(self):
        self.load()

    def load(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        CONFIG = ConfigParser.ConfigParser()
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, 'data', 'goagent', 'config.ini'))

        try:
            if os.path.isfile(CONFIG_USER_FILENAME):
                CONFIG.read(CONFIG_USER_FILENAME)
            else:
                return

            try:
                self.appid = CONFIG.get('gae', 'appid')
                self.password = CONFIG.get('gae', 'password')
            except:
                pass

            self.proxy_enable = CONFIG.get('proxy', 'enable')
            self.proxy_type = CONFIG.get('proxy', 'type')
            self.proxy_host = CONFIG.get('proxy', 'host')
            self.proxy_port = CONFIG.get('proxy', 'port')
            self.proxy_user = CONFIG.get('proxy', 'user')
            self.proxy_passwd = CONFIG.get('proxy', 'passwd')
        except Exception as e:
            logging.warn("User_config.load except:%s", e)

    def save(self):
        CONFIG_USER_FILENAME = os.path.abspath( os.path.join(root_path, 'data', 'goagent', 'config.ini'))
        try:
            f = open(CONFIG_USER_FILENAME, 'w')
            if self.appid != "":
                f.write("[gae]\n")
                f.write("appid = %s\n" % self.appid)
                f.write("password = %s\n\n" % self.password)
            f.write("[proxy]\n")
            f.write("enable = %s\n" % self.proxy_enable)
            f.write("type = %s\n" % self.proxy_type)
            f.write("host = %s\n" % self.proxy_host)
            f.write("port = %s\n" % self.proxy_port)
            f.write("user = %s\n" % self.proxy_user)
            f.write("passwd = %s\n" % self.proxy_passwd)
            f.close()
        except:
            logging.warn("launcher.config save user config fail:%s", CONFIG_USER_FILENAME)


user_config = User_config()

import ctypes
class OSVERSIONINFOEXW(ctypes.Structure):
    _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                ('dwMajorVersion', ctypes.c_ulong),
                ('dwMinorVersion', ctypes.c_ulong),
                ('dwBuildNumber', ctypes.c_ulong),
                ('dwPlatformId', ctypes.c_ulong),
                ('szCSDVersion', ctypes.c_wchar*128),
                ('wServicePackMajor', ctypes.c_ushort),
                ('wServicePackMinor', ctypes.c_ushort),
                ('wSuiteMask', ctypes.c_ushort),
                ('wProductType', ctypes.c_byte),
                ('wReserved', ctypes.c_byte)]

def win32_version():
    """
    Get's the OS major and minor versions.  Returns a tuple of
    (OS_MAJOR, OS_MINOR).
    """
    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        raise Exception("Failed to get OS version")

    version_string = "Version:%d-%d; Build:%d; Platform:%d; CSD:%s; ServicePack:%d-%d; Suite:%d; ProductType:%d" %  (
        os_version.dwMajorVersion, os_version.dwMinorVersion,
        os_version.dwBuildNumber,
        os_version.dwPlatformId,
        os_version.szCSDVersion,
        os_version.wServicePackMajor, os_version.wServicePackMinor,
        os_version.wSuiteMask,
        os_version.wReserved
    )

    return version_string

def os_detail():
    if sys.platform == "win32":
        return win32_version()
    elif sys.platform == "linux" or sys.platform == "linux2":
        distname,version,id = platform.linux_distribution()
        return "Dist:%s; Version:%s; ID:%s" % (distname,version,id)
    elif sys.platform == "darwin":
        release, versioninfo, machine = platform.mac_ver()
        return "Release:%s; Version:%s Machine:%s" % (release, versioninfo, machine)
    else:
        return "None"



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
            if not "127.0.0.1" in netloc:
                logging.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

        path = urlparse.urlparse(self.path).path
        if path == "/log":
            return self.req_log_handler()
        elif path == "/status":
            return self.req_status_handler()
        else:
            logging.debug('GoAgent Web_control %s "%s %s ', self.address_string(), self.command, self.path)


        if path == '/deploy':
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
            logging.warn('Control Req %s %s %s ', self.address_string(), self.command, self.path)

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
        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not "127.0.0.1" in netloc:
                logging.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass
        logging.debug ('GoAgent web_control %s %s %s ', self.address_string(), self.command, self.path)
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
            logging.exception("xxnet_version fail")
        return "get_version_fail"

    def req_status_handler(self):
        if "user-agent" in self.headers.dict:
            user_agent = self.headers.dict["user-agent"]
        else:
            user_agent = ""

        launcher_version = self.get_launcher_version()
        gws_ip_num = len(google_ip.gws_ip_list)
        res_arr = {"gws_ip_num": gws_ip_num,
                   "sys_platform":sys.platform,
                   "os_system":platform.system(),
                   "os_version":platform.version(),
                   "os_release":platform.release(),
                   "architecture":platform.architecture(),
                   "os_detail":os_detail(),
                   "browser":user_agent,
                   "xxnet_version":RemoteContralServerHandler.xxnet_version(),
                   "launcher_version":launcher_version,
                   "goagent_version": config.__version__,
                   "python_version": config.python_version,
                   "proxy_listen":config.LISTEN_IP + ":" + str(config.LISTEN_PORT),
                   "gae_appid":"|".join(config.GAE_APPIDS),
                   "working_appid":"|".join(appid_manager.working_appid_list),
                   "out_of_quota_appids":"|".join(appid_manager.out_of_quota_appids),
                   "not_exist_appids":"|".join(appid_manager.not_exist_appids),
                   "pac_url":config.pac_url}
        data = json.dumps(res_arr)

        self.send_response('application/json', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            if reqs['cmd'] == ['get_config']:
                data = json.dumps(user_config, default=lambda o: o.__dict__)
            elif reqs['cmd'] == ['set_config']:
                user_config.appid = self.postvars['appid'][0]
                user_config.password = self.postvars['passwd'][0]
                user_config.proxy_enable = self.postvars['proxy_enable'][0]
                user_config.proxy_type = self.postvars['proxy_type'][0]
                user_config.proxy_host = self.postvars['proxy_host'][0]
                user_config.proxy_port = self.postvars['proxy_port'][0]
                user_config.proxy_user = self.postvars['proxy_user'][0]
                user_config.proxy_passwd = self.postvars['proxy_passwd'][0]
                user_config.save()

                data = '{"res":"success"}'
                self.send_response('application/json', data)

                http_request("http://127.0.0.1:8085/init_module?module=goagent&cmd=restart")
                return
        except Exception as e:
            logging.exception("req_config_handler except:%s", e)
            data = '{"res":"fail", "except":"%s"}' % e
        self.send_response('application/json', data)


    def req_deploy_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        log_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'upload.log'))
        time_now = datetime.datetime.today().strftime('%H:%M:%S-%a/%d/%b/%Y')

        if reqs['cmd'] == ['deploy']:
            if RemoteContralServerHandler.deploy_proc and RemoteContralServerHandler.deploy_proc.poll() == None:
                logging.warn("deploy is running, request denied.")
                data = '{"res":"deploy is running", "time":"%s"}' % (time_now)
            else:
                try:
                    if os.path.isfile(log_path):
                        os.remove(log_path)
                    script_path = os.path.abspath(os.path.join(current_path, os.pardir, "server", 'uploader.py'))
                    appid = self.postvars['appid'][0]
                    email = self.postvars['email'][0]
                    passwd = self.postvars['passwd'][0]
                    RemoteContralServerHandler.deploy_proc = subprocess.Popen([sys.executable, script_path, appid, email, passwd], stdout=subprocess.PIPE)
                    logging.info("deploy begin.")
                    data = '{"res":"success", "time":"%s"}' % time_now
                except Exception as e:
                    data = '{"res":"%s", "time":"%s"}' % (e, time_now)

        elif reqs['cmd'] == ['get_log']:
            if self.deploy_proc and os.path.isfile(log_path):
                with open(log_path, "r") as f:
                    content = f.read()
            else:
                content = ""

            status = 'init'
            if RemoteContralServerHandler.deploy_proc:
                if RemoteContralServerHandler.deploy_proc.poll() == None:
                    status = 'running'
                else:
                    status = 'finished'

            data = json.dumps({'status':status,'log':content, 'time':time_now})

        self.send_response('application/json', data)

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

if __name__ == "__main__":
    print RemoteContralServerHandler.xxnet_version()