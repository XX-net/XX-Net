#!/usr/bin/env python
# coding:utf-8

import ConfigParser, io, os, re, sys
import SocketServer, socket, ssl
import BaseHTTPServer
import errno
import urlparse
import subprocess
import threading

import logging
import module_init
import config
import cgi

NetWorkIOError = (socket.error, ssl.SSLError, OSError)


class User_config(object):
    appid = ''
    password = ''

    def __init__(self):
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()

        current_path = os.path.dirname(os.path.abspath(__file__))
        # load ../../data/goagent/config.ini
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'data', 'goagent', 'config.ini'))

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
        except:
            pass
    def save(self, appid, password):
        path = "/2"
        try:
            f = open(self.CONFIG_USER_FILENAME, 'w')
            f.write("[gae]\n")
            f.write("appid = %s\n" % appid)
            f.write("password = %s\n" % password)
            f.write("path = %s\n" % path)
            f.close()
        except:
            logging.warn("launcher.config save user config fail:%s", self.CONFIG_USER_FILENAME)

    def clean(self):
        self.appid = ''
        self.password = ''
        self.CONFIG.remove_section('gae')
        try:
            os.remove(self.CONFIG_USER_FILENAME)
        except:
            logging.warn("launcher clean goagent user config fail:%s", self.CONFIG_USER_FILENAME)

user_config = User_config()

class LocalServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

    def close_request(self, request):
        try:
            request.close()
        except Exception:
            pass

    def finish_request(self, request, client_address):
        try:
            self.RequestHandlerClass(request, client_address, self)
        except NetWorkIOError as e:
            if e[0] not in (errno.ECONNABORTED, errno.ECONNRESET, errno.EPIPE):
                raise

    def handle_error(self, *args):
        """make ThreadingTCPServer happy"""
        etype, value = sys.exc_info()[:2]
        if isinstance(value, NetWorkIOError) and 'bad write retry' in value.args[1]:
            etype = value = None
        else:
            del etype, value
            SocketServer.ThreadingTCPServer.handle_error(self, *args)

class Http_Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    deploy_proc = None
    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def do_HEAD(s):
        print "do_HEAD"
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
 #       self.wfile.write(b'HTTP/1.1 200\r\nConnection: close\r\n\r\n')

    def do_CONNECT(self):
        self.wfile.write(b'HTTP/1.1 403\r\nConnection: close\r\n\r\n')

    def do_POST(self):
        logging.debug ('HTTP %s "%s %s ', self.address_string(), self.command, self.path)
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            self.postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            self.postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            self.postvars = {}

        path = urlparse.urlparse(self.path).path
        if path == '/goagent_deploy':
            self.req_goagent_deploy_handler()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def do_GET(self):
        logging.debug ('HTTP %s "%s %s ', self.address_string(), self.command, self.path)
        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            logging.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        path = urlparse.urlparse(self.path).path
        if path == '/':
            path = 'index.html'
        filename = os.path.normpath('./html/' + path)
        if os.path.isfile(filename):
            if filename.endswith('.js'):
                mimetype = 'application/javascript'
            elif filename.endswith('.css'):
                mimetype = 'text/css'
            elif filename.endswith('.html'):
                mimetype = 'text/html'
            elif filename.endswith('.jpg'):
                mimetype = 'image/jpeg'
            elif filename.endswith('.png'):
                mimetype = 'image/png'
            else:
                mimetype = 'text/plain'


            self.send_file(filename, mimetype)
        elif path == '/status':
            self.req_status_handler()
        elif path == '/goagent_config':
            self.req_goagent_config_handler()
        elif path == '/goagent_deploy':
            self.req_goagent_deploy_handler()
        elif path == '/quit':
            module_init.stop_all()
            #stop()
            os._exit(0)
        elif path == '/config':
            self.req_config_handler()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_file(self, filename, mimetype):
        data = ''
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
                self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
                self.wfile.write(data)
        except:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Open file fail')

    def req_status_handler(self):
        data = "status ok"
        mimetype = 'text/plain'
        self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def req_goagent_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_config']:
            user_config.load()
            data = '{ "appid": "%s", "passwd": "%s" }' % (user_config.appid, user_config.password)
        elif reqs['cmd'] == ['set_config']:
            if reqs['appid'] and reqs['passwd']:
                appid = reqs['appid'][0]
                if appid == '':
                    user_config.clean()
                else:
                    user_config.save(appid=appid, password=reqs['passwd'][0])

                module_init.stop("goagent")
                module_init.start("goagent")
                data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'

        mimetype = 'text/plain'
        self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)


    def req_goagent_deploy_handler(self):
        import config
        goagent_version = config.config["modules"]["goagent"]["current_version"]
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        log_path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, "goagent", goagent_version, "server", 'upload.log'))

        if reqs['cmd'] == ['deploy']:
            try:
                if os.path.isfile(log_path):
                    os.remove(log_path)
                script_path = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, "goagent", goagent_version, "server", 'uploader.py'))
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
        self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_config']:
            config.load()
            data = '{ "check_update": "%d", "popup_webui": %d }' % (config.get(["update", "check_update"], 1), config.get(["web_ui", "popup_webui"], 1) )
        elif reqs['cmd'] == ['set_config']:
            if 'check_update' in reqs:
                check_update = int(reqs['check_update'][0])
                if check_update != 0 and check_update != 1:
                    data = '{"res":"fail, check_update:%s"}' % check_update
                else:
                    config.config["update"]["check_update"] = int(check_update)
                    config.save()

                    data = '{"res":"success"}'

            elif 'popup_webui' in reqs :
                popup_webui = int(reqs['popup_webui'][0])
                if popup_webui != 0 and popup_webui != 1:
                    data = '{"res":"fail, popup_webui:%s"}' % popup_webui
                else:
                    config.set(["web_ui", "popup_webui"], popup_webui)
                    config.save()

                    data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'

        mimetype = 'text/plain'
        self.wfile.write(('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)


process = 0
server = 0
def start():
    global process, server
    server = LocalServer(("127.0.0.1", 8085), Http_Handler)
    process = threading.Thread(target=server.serve_forever)
    process.setDaemon(True)
    process.start()

def stop():
    global process, server
    if process == 0:
        return

    logging.info("begin to exit web control")
    server.shutdown()
    server.server_close()
    process.join()
    logging.info("launcher web control exited.")
    process = 0

