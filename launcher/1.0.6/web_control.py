#!/usr/bin/env python
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

import re
import SocketServer, socket, ssl
import BaseHTTPServer
import errno
import urlparse
import threading
import urllib2
import time
import datetime

root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))

import yaml

import logging
import module_init
import config
import autorun

NetWorkIOError = (socket.error, ssl.SSLError, OSError)



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

module_menus = {}
class Http_Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    deploy_proc = None


    def load_module_menus(self):
        global module_menus
        #config.load()
        modules = config.get(['modules'], None)
        for module in modules:
            values = modules[module]
            version = values["current_version"]
            menu_path = os.path.join(root_path, module, version, "web_ui", "menu.yaml")
            if not os.path.isfile(menu_path):
                continue
            module_menu = yaml.load(file(menu_path, 'r'))
            module_menus[module] = module_menu

        module_menus = sorted(module_menus.iteritems(), key=lambda (k,v): (v['menu_sort_id']))
        #for k,v in self.module_menus:
        #    logging.debug("m:%s id:%d", k, v['menu_sort_id'])

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def send_response(self, mimetype, data):
        self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, len(data))).encode())
        self.wfile.write(data)

    def do_GET(self):
        logging.debug ('launcher web_control %s "%s %s ', self.address_string(), self.command, self.path)
        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            logging.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        url_path = urlparse.urlparse(self.path).path
        if url_path == '/':
            return self.req_index_handler()

        if len(url_path.split('/')) >= 3 and url_path.split('/')[1] == "modules":
            module = url_path.split('/')[2]
            #config.load()
            modules_versoin = config.get(['modules', module, 'current_version'], None)
            file_path = os.path.join(root_path, module, modules_versoin, url_path.split('/')[3:].join('/'))
        else:
            file_path = os.path.join(current_path, 'web_ui' + url_path)


        if os.path.isfile(file_path):
            if file_path.endswith('.js'):
                mimetype = 'application/javascript'
            elif file_path.endswith('.css'):
                mimetype = 'text/css'
            elif file_path.endswith('.html'):
                mimetype = 'text/html'
            elif file_path.endswith('.jpg'):
                mimetype = 'image/jpeg'
            elif file_path.endswith('.png'):
                mimetype = 'image/png'
            else:
                mimetype = 'text/plain'


            self.send_file(file_path, mimetype)
        elif url_path == '/config':
            self.req_config_handler()
        elif url_path == '/init_module':
            self.req_init_module_handler()
        elif url_path == '/quit':
            self.send_response('application/json', '{"status":"success"}')
            module_init.stop_all()
            os._exit(0)
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            logging.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_file(self, filename, mimetype):
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
            tme = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%H:%M:%S-%a/%d/%b/%Y')
            self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:public, max-age=31536000\r\nexpires: %s\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (tme, mimetype, len(data))).encode())
            self.wfile.write(data)
        except:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Open file fail')

    def req_index_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)

        try:
            target_module = reqs['module'][0]
            target_menu = reqs['menu'][0]
        except:
            target_module = 'goagent'
            target_menu = 'status'

        if len(module_menus) == 0:
            self.load_module_menus()

        index_path = os.path.join(current_path, 'web_ui', "index.html")
        with open(index_path, "r") as f:
            index_content = f.read()

        menu_content = ''
        for module,v in module_menus:
            #logging.debug("m:%s id:%d", module, v['menu_sort_id'])
            title = v["module_title"]
            menu_content += '<li class="nav-header">%s</li>\n' % title
            for sub_id in v['sub_menus']:
                sub_title = v['sub_menus'][sub_id]['title']
                sub_url = v['sub_menus'][sub_id]['url']
                if target_module == title and target_menu == sub_url:
                    active = 'class="active"'
                else:
                    active = ''
                menu_content += '<li %s><a href="/?module=%s&menu=%s">%s</a></li>\n' % (active, module, sub_url, sub_title)

        right_content_file = os.path.join(root_path, target_module, config.get(["modules", target_module, "current_version"]), "web_ui", target_menu + ".html")
        if os.path.isfile(right_content_file):
            with open(right_content_file, "r") as f:
                right_content = f.read()
        else:
            right_content = ""

        data = (index_content.decode('utf-8') % (menu_content, right_content.decode('utf-8') )).encode('utf-8')
        self.send_response('text/html', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_config']:
            config.load()
            data = '{ "check_update": "%d", "popup_webui": %d, "auto_start": %d }' %\
                   (config.get(["update", "check_update"], 1)
                    , config.get(["modules", "launcher", "popup_webui"], 1)
                    , config.get(["modules", "launcher", "auto_start"], 0))
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
                    config.set(["modules", "launcher", "popup_webui"], popup_webui)
                    config.save()

                    data = '{"res":"success"}'
            elif 'auto_start' in reqs :
                auto_start = int(reqs['auto_start'][0])
                if auto_start != 0 and auto_start != 1:
                    data = '{"res":"fail, auto_start:%s"}' % auto_start
                else:
                    if auto_start:
                        autorun.enable()
                    else:
                        autorun.disable()

                    config.set(["modules", "launcher", "auto_start"], auto_start)
                    config.save()

                    data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'

        self.send_response('application/json', data)

    def req_init_module_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            module = reqs['module'][0]
            config.load()
            modules_versoin = config.get(['modules', module, 'current_version'], None)

            if reqs['cmd'] == ['start']:
                result = module_init.start(module)
                data = '{ "module": "%s", "cmd": "start", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == ['stop']:
                result = module_init.stop(module)
                data = '{ "module": "%s", "cmd": "stop", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == ['restart']:
                result_stop = module_init.stop(module)
                result_start = module_init.start(module)
                data = '{ "module": "%s", "cmd": "restart", "stop_result": "%s", "start_result": "%s" }' % (module, result_stop, result_start)
        except Exception as e:
            logging.exception("init_module except:%s", e)

        self.send_response("application/json", data)

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


def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url)
        return req
    except Exception as e:
        #logging.exception("web_control http_request:%s fail:%s", url, e)
        return False

def confirm_xxnet_exit():
    for i in range(10):
        if http_request("http://127.0.0.1:8085/quit") == False:
            return True
        time.sleep(1)
    return False

if __name__ == "__main__":
    #confirm_xxnet_exit()
    http_request("http://getbootstrap.com/dist/js/bootstrap.min.js")
