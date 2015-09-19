#!/usr/bin/env python
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
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

root_path = os.path.abspath(os.path.join(current_path, os.pardir))

import yaml
import json

import launcher_log
import module_init
import config
import autorun
import update_from_github

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
        module_menus = {}
        #config.load()
        modules = config.get(['modules'], None)
        for module in modules:
            values = modules[module]
            if module != "launcher" and config.get(["modules", module, "auto_start"], 0) != 1:
                continue

            #version = values["current_version"]
            menu_path = os.path.join(root_path, module, "web_ui", "menu.yaml")
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
    def send_not_found(self):
        self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
    def do_POST(self):
        #url_path = urlparse.urlparse(self.path).path
        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    launcher_log.warn("request %s no module in path", self.path)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_POST()
                return

    def do_GET(self):
        try:
            refer = self.headers.getheader('Referer')
            netloc = urlparse.urlparse(refer).netloc
            if not netloc.startswith("127.0.0.1") and not netloc.startswitch("localhost"):
                launcher_log.warn("web control ref:%s refuse", netloc)
                return
        except:
            pass

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            launcher_log.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        url_path = urlparse.urlparse(self.path).path
        if url_path == '/':
            return self.req_index_handler()

        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    launcher_log.warn("request %s no module in path", url_path)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_GET()
                return
            else:
                file_path = os.path.join(root_path, module, url_path_list[3:].join('/'))
        else:
            file_path = os.path.join(current_path, 'web_ui' + url_path)


        launcher_log.debug ('launcher web_control %s %s %s ', self.address_string(), self.command, self.path)
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
        elif url_path == '/download':
            self.req_download_handler()
        elif url_path == '/init_module':
            self.req_init_module_handler()
        elif url_path == '/quit':
            self.send_response('text/html', '{"status":"success"}')
            module_init.stop_all()
            os._exit(0)
        elif url_path == '/restart':
            self.send_response('text/html', '{"status":"success"}')
            update_from_github.restart_xxnet()
        else:
            self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Not Found')
            launcher_log.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def send_file(self, filename, mimetype):
        try:
            with open(filename, 'rb') as fp:
                data = fp.read()
            tme = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:public, max-age=31536000\r\nExpires: %s\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (tme, mimetype, len(data))).encode())
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
            if config.get(['modules', 'gae_proxy', 'auto_start'], 0) == 1:
                target_module = 'gae_proxy'
                target_menu = 'status'
            else:
                target_module = 'launcher'
                target_menu = 'about'


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

        right_content_file = os.path.join(root_path, target_module, "web_ui", target_menu + ".html")
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

        current_version = update_from_github.current_version()

        if reqs['cmd'] == ['get_config']:
            config.load()
            check_update = config.get(["update", "check_update"], 1)
            if check_update == 0:
                check_update = "dont-check"
            elif check_update == 1:
                check_update = "long-term-stable"

            data = '{ "check_update": "%s", "popup_webui": %d, "show_systray": %d, "auto_start": %d, "php_enable": %d, "gae_proxy_enable": %d }' %\
                   (check_update
                    , config.get(["modules", "launcher", "popup_webui"], 1)
                    , config.get(["modules", "launcher", "show_systray"], 1)
                    , config.get(["modules", "launcher", "auto_start"], 0)
                    , config.get(["modules", "php_proxy", "auto_start"], 0)
                    , config.get(["modules", "gae_proxy", "auto_start"], 0))
        elif reqs['cmd'] == ['set_config']:
            if 'check_update' in reqs:
                check_update = reqs['check_update'][0]
                if check_update not in ["dont-check", "long-term-stable", "stable", "test"]:
                    data = '{"res":"fail, check_update:%s"}' % check_update
                else:
                    config.set(["update", "check_update"], check_update)
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
            elif 'show_systray' in reqs :
                show_systray = int(reqs['show_systray'][0])
                if show_systray != 0 and show_systray != 1:
                    data = '{"res":"fail, show_systray:%s"}' % show_systray
                else:
                    config.set(["modules", "launcher", "show_systray"], show_systray)
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
            elif 'gae_proxy_enable' in reqs :
                gae_proxy_enable = int(reqs['gae_proxy_enable'][0])
                if gae_proxy_enable != 0 and gae_proxy_enable != 1:
                    data = '{"res":"fail, gae_proxy_enable:%s"}' % gae_proxy_enable
                else:
                    config.set(["modules", "gae_proxy", "auto_start"], gae_proxy_enable)
                    config.save()
                    if gae_proxy_enable:
                        module_init.start("gae_proxy")
                    else:
                        module_init.stop("gae_proxy")
                    self.load_module_menus()
                    data = '{"res":"success"}'
            elif 'php_enable' in reqs :
                php_enable = int(reqs['php_enable'][0])
                if php_enable != 0 and php_enable != 1:
                    data = '{"res":"fail, php_enable:%s"}' % php_enable
                else:
                    config.set(["modules", "php_proxy", "auto_start"], php_enable)
                    config.save()
                    if php_enable:
                        module_init.start("php_proxy")
                    else:
                        module_init.stop("php_proxy")
                    self.load_module_menus()
                    data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'
        elif reqs['cmd'] == ['get_new_version']:
            versions = update_from_github.get_github_versions()
            data = '{"res":"success", "test_version":"%s", "stable_version":"%s", "current_version":"%s"}' % (versions[0][1], versions[1][1], current_version)
            launcher_log.info("%s", data)
        elif reqs['cmd'] == ['update_version']:
            version = reqs['version'][0]
            try:
                update_from_github.update_version(version)
                data = '{"res":"success"}'
            except Exception as e:
                launcher_log.info("update_test_version fail:%r", e)
                data = '{"res":"fail", "error":"%s"}' % e

        self.send_response('text/html', data)

    def req_download_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_progress']:
            data = json.dumps(update_from_github.download_progress)

        self.send_response('text/html', data)

    def req_init_module_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        try:
            module = reqs['module'][0]
            config.load()

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
            launcher_log.exception("init_module except:%s", e)

        self.send_response("text/html", data)

process = 0
server = 0
def start():
    global process, server
    # should use config.yaml to bing ip
    server = LocalServer(("127.0.0.1", 8085), Http_Handler)
    process = threading.Thread(target=server.serve_forever)
    process.setDaemon(True)
    process.start()

def stop():
    global process, server
    if process == 0:
        return

    launcher_log.info("begin to exit web control")
    server.shutdown()
    server.server_close()
    process.join()
    launcher_log.info("launcher web control exited.")
    process = 0


def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url, timeout=30)
        return req
    except Exception as e:
        #logging.exception("web_control http_request:%s fail:%s", url, e)
        return False

def confirm_xxnet_exit():
    # suppose xxnet is running, try to close it
    is_xxnet_exit = False
    launcher_log.debug("start confirm_xxnet_exit")
    for i in range(30):
        if http_request("http://127.0.0.1:8087/quit") == False:
            launcher_log.debug("good, xxnet:8087 cleared!")
            is_xxnet_exit = True
            break
        else:
            launcher_log.debug("<%d>: try to terminate xxnet:8087" % i)
        time.sleep(1)
    for i in range(30):
        if http_request("http://127.0.0.1:8085/quit") == False:
            launcher_log.debug("good, xxnet:8085 clear!")
            is_xxnet_exit = True
            break
        else:
            launcher_log.debug("<%d>: try to terminate xxnet:8085" % i)
        time.sleep(1)
    launcher_log.debug("finished confirm_xxnet_exit")
    return is_xxnet_exit

def confirm_module_ready(port):
    if port == 0:
        launcher_log.error("confirm_module_ready with port 0")
        time.sleep(1)
        return False

    for i in range(200):
        req = http_request("http://127.0.0.1:%d/is_ready" % port)
        if req == False:
            time.sleep(1)
            continue

        content = req.read(1024)
        req.close()
        #logging.debug("cert_import_ready return:%s", content)
        if content == "True":
            return True
        else:
            time.sleep(1)
    return False

if __name__ == "__main__":
    #confirm_xxnet_exit()
    http_request("http://getbootstrap.com/dist/js/bootstrap.min.js")
