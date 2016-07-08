#!/usr/bin/env python
# coding:utf-8

import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, 'python27', '1.0'))
    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

import re
import socket, ssl
import urlparse
import threading
import urllib2
import time

root_path = os.path.abspath(os.path.join(current_path, os.pardir))

import yaml
import json

from instances import xlog
import module_init
import config
import autorun
import update_from_github
import simple_http_server
from simple_i18n import SimpleI18N

NetWorkIOError = (socket.error, ssl.SSLError, OSError)

i18n_translator = SimpleI18N(config.get(['language'], None))

module_menus = {}
class Http_Handler(simple_http_server.HttpServerHandler):
    deploy_proc = None

    def load_module_menus(self):
        global module_menus
        new_module_menus = {}
        #config.load()
        modules = config.get(['modules'], None)
        for module in modules:
            values = modules[module]
            if module != "launcher" and config.get(["modules", module, "auto_start"], 0) != 1: # skip php_proxy module
                continue

            menu_path = os.path.join(root_path, module, "web_ui", "menu.yaml") # launcher & gae_proxy modules
            if not os.path.isfile(menu_path):
                continue

            # i18n code lines (Both the locale dir & the template dir are module-dependent)
            locale_dir = os.path.abspath(os.path.join(root_path, module, 'lang'))
            stream = i18n_translator.render(locale_dir, menu_path)
            module_menu = yaml.load(stream)
            new_module_menus[module] = module_menu

        module_menus = sorted(new_module_menus.iteritems(), key=lambda (k,v): (v['menu_sort_id']))
        #for k,v in self.module_menus:
        #    xlog.debug("m:%s id:%d", k, v['menu_sort_id'])

    def do_POST(self):
        refer = self.headers.getheader('Referer')
        if refer:
            refer_loc = urlparse.urlparse(refer).netloc
            host = self.headers.getheader('host')
            if refer_loc != host:
                xlog.warn("web control ref:%s host:%s", refer_loc, host)
                return

        #url_path = urlparse.urlparse(self.path).path
        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    xlog.warn("request %s no module in path", self.path)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_POST()
                return

    def do_GET(self):
        refer = self.headers.getheader('Referer')
        if refer:
            refer_loc = urlparse.urlparse(refer).netloc
            host = self.headers.getheader('host')
            if refer_loc != host:
                xlog.warn("web control ref:%s host:%s", refer_loc, host)
                return

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            xlog.warn('%s %s %s haking', self.address_string(), self.command, self.path )
            return

        url_path = urlparse.urlparse(self.path).path
        if url_path == '/':
            return self.req_index_handler()

        url_path_list = self.path.split('/')
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    xlog.warn("request %s no module in path", url_path)
                    self.send_not_found()
                    return

                if "imp" not in module_init.proc_handler[module]:
                    xlog.warn("request module:%s start fail", module)
                    self.send_not_found()
                    return

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.do_GET()
                return
            else:
                relate_path = '/'.join(url_path_list[3:])
                file_path = os.path.join(root_path, module, "web_ui", relate_path)
                if not os.path.isfile(file_path):
                    return self.send_not_found()

                # i18n code lines (Both the locale dir & the template dir are module-dependent)
                locale_dir = os.path.abspath(os.path.join(root_path, module, 'lang'))
                content = i18n_translator.render(locale_dir, file_path)
                return self.send_response('text/html', content)
        else:
            file_path = os.path.join(current_path, 'web_ui' + url_path)

        xlog.debug ('launcher web_control %s %s %s ', self.address_string(), self.command, self.path)
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
        elif url_path == '/update':
            self.req_update_handler()
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
            self.send_not_found()
            xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

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

        # i18n code lines (Both the locale dir & the template dir are module-dependent)
        locale_dir = os.path.abspath(os.path.join(current_path, 'lang'))
        index_content = i18n_translator.render(locale_dir, os.path.join(current_path, "web_ui", "index.html"))

        current_version = update_from_github.current_version()
        menu_content = ''
        for module,v in module_menus:
            #xlog.debug("m:%s id:%d", module, v['menu_sort_id'])
            title = v["module_title"]
            menu_content += '<li class="nav-header">%s</li>\n' % title
            for sub_id in v['sub_menus']:
                sub_title = v['sub_menus'][sub_id]['title']
                sub_url = v['sub_menus'][sub_id]['url']
                if target_module == module and target_menu == sub_url:
                    active = 'class="active"'
                else:
                    active = ''
                menu_content += '<li %s><a href="/?module=%s&menu=%s">%s</a></li>\n' % (active, module, sub_url, sub_title)

        right_content_file = os.path.join(root_path, target_module, "web_ui", target_menu + ".html")
        if os.path.isfile(right_content_file):
            # i18n code lines (Both the locale dir & the template dir are module-dependent)
            locale_dir = os.path.abspath(os.path.join(root_path, target_module, 'lang'))
            right_content = i18n_translator.render(locale_dir, os.path.join(root_path, target_module, "web_ui", target_menu + ".html"))

        else:
            right_content = ""

        data = (index_content.decode('utf-8') % (current_version, current_version, menu_content, right_content.decode('utf-8') )).encode('utf-8')
        self.send_response('text/html', data)

    def req_config_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_config']:
            config.load()
            check_update = config.get(["update", "check_update"], 1)
            if check_update == 0:
                check_update = "dont-check"
            elif check_update == 1:
                check_update = "stable"

            data = '{ "check_update": "%s", "language": "%s", "popup_webui": %d, "allow_remote_connect": %d, \
             "show_systray": %d, "auto_start": %d, "show_detail": %d, "gae_proxy_enable": %d, "x_tunnel_enable": %d}' %\
                   (check_update
                    , config.get(["language"], i18n_translator.lang)
                    , config.get(["modules", "launcher", "popup_webui"], 1)
                    , config.get(["modules", "launcher", "allow_remote_connect"], 0)
                    , config.get(["modules", "launcher", "show_systray"], 1)
                    , config.get(["modules", "launcher", "auto_start"], 0)
                    , config.get(["modules", "gae_proxy", "show_detail"], 0)
                    , config.get(["modules", "gae_proxy", "auto_start"], 0)
                    , config.get(["modules", "x_tunnel", "auto_start"], 0)
                    )
        elif reqs['cmd'] == ['set_config']:
            if 'check_update' in reqs:
                check_update = reqs['check_update'][0]
                if check_update not in ["dont-check", "stable", "test"]:
                    data = '{"res":"fail, check_update:%s"}' % check_update
                else:
                    config.set(["update", "check_update"], check_update)
                    config.save()

                    data = '{"res":"success"}'

            elif 'language' in reqs:
                language = reqs['language'][0]

                if language not in i18n_translator.get_valid_languages():
                    data = '{"res":"fail, language:%s"}' % language
                else:
                    config.set(["language"], language)
                    config.save()

                    i18n_translator.lang = language
                    self.load_module_menus()

                    data = '{"res":"success"}'

            elif 'popup_webui' in reqs:
                popup_webui = int(reqs['popup_webui'][0])
                if popup_webui != 0 and popup_webui != 1:
                    data = '{"res":"fail, popup_webui:%s"}' % popup_webui
                else:
                    config.set(["modules", "launcher", "popup_webui"], popup_webui)
                    config.save()

                    data = '{"res":"success"}'

            elif 'allow_remote_connect' in reqs:
                allow_remote_connect = int(reqs['allow_remote_connect'][0])
                if allow_remote_connect != 0 and allow_remote_connect != 1:
                    data = '{"res":"fail, allow_remote_connect:%s"}' % allow_remote_connect
                else:
                    config.set(["modules", "launcher", "allow_remote_connect"], allow_remote_connect)
                    config.save()

                    data = '{"res":"success"}'

                    xlog.debug("restart web control.")
                    stop()
                    time.sleep(1)
                    start()
                    xlog.debug("launcher web control restarted.")

            elif 'show_systray' in reqs:
                show_systray = int(reqs['show_systray'][0])
                if show_systray != 0 and show_systray != 1:
                    data = '{"res":"fail, show_systray:%s"}' % show_systray
                else:
                    config.set(["modules", "launcher", "show_systray"], show_systray)
                    config.save()

                    data = '{"res":"success"}'

            elif 'auto_start' in reqs:
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

            elif 'show_detail' in reqs:
                show_detail = int(reqs['show_detail'][0])
                if show_detail != 0 and show_detail != 1:
                    data = '{"res":"fail, show_detail:%s"}' % show_detail
                else:
                    config.set(["modules", "gae_proxy", "show_detail"], show_detail)
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
            elif 'x_tunnel_enable' in reqs :
                x_tunnel_enable = int(reqs['x_tunnel_enable'][0])
                if x_tunnel_enable != 0 and x_tunnel_enable != 1:
                    data = '{"res":"fail, x_tunnel_enable:%s"}' % x_tunnel_enable
                else:
                    config.set(["modules", "x_tunnel", "auto_start"], x_tunnel_enable)
                    config.save()
                    if x_tunnel_enable:
                        module_init.start("x_tunnel")
                    else:
                        module_init.stop("x_tunnel")
                    self.load_module_menus()
                    data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'

        self.send_response('text/html', data)

    def req_update_handler(self):
        req = urlparse.urlparse(self.path).query
        reqs = urlparse.parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_progress']:
            data = json.dumps(update_from_github.progress)
        elif reqs['cmd'] == ['get_new_version']:
            current_version = update_from_github.current_version()
            github_versions = update_from_github.get_github_versions()
            data = '{"res":"success", "test_version":"%s", "stable_version":"%s", "current_version":"%s"}' % (github_versions[0][1], github_versions[1][1], current_version)
            xlog.info("%s", data)
        elif reqs['cmd'] == ['update_version']:
            version = reqs['version'][0]
            update_from_github.start_update_version(version)
            data = '{"res":"success"}'
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
            xlog.exception("init_module except:%s", e)

        self.send_response("text/html", data)

process = 0
server = 0
def start():
    global process, server
    # should use config.yaml to bind ip
    allow_remote = config.get(["modules", "launcher", "allow_remote_connect"], 0)
    host_port = config.get(["modules", "launcher", "control_port"], 8085)

    if allow_remote:
        host_addr = "0.0.0.0"
    else:
        host_addr = "127.0.0.1"

    xlog.info("begin to start web control")

    server = simple_http_server.HTTPServer((host_addr, host_port), Http_Handler)
    process = threading.Thread(target=server.serve_forever)
    process.setDaemon(True)
    process.start()

    xlog.info("launcher web control started.")

def stop():
    global process, server
    if process == 0:
        return

    xlog.info("begin to exit web control")
    server.shutdown()
    server.server_close()
    process.join()
    xlog.info("launcher web control exited.")
    process = 0


def http_request(url, method="GET"):
    proxy_handler = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(proxy_handler)
    try:
        req = opener.open(url, timeout=30)
        return req
    except Exception as e:
        #xlog.exception("web_control http_request:%s fail:%s", url, e)
        return False

def confirm_xxnet_exit():
    """suppose xxnet is running, try to close it

    """
    is_xxnet_exit = False
    xlog.debug("start confirm_xxnet_exit")

    for i in range(30):
        # gae_proxy(default port:8087)
        if http_request("http://127.0.0.1:8087/quit") == False:
            xlog.debug("good, xxnet:8087 cleared!")
            is_xxnet_exit = True
            break
        else:
            xlog.debug("<%d>: try to terminate xxnet:8087" % i)
        time.sleep(1)


    for i in range(30):
        # web_control(default port:8085)
        host_port = config.get(["modules", "launcher", "control_port"], 8085)
        req_url = "http://127.0.0.1:{port}/quit".format(port=host_port)
        if http_request(req_url) == False:
            xlog.debug("good, xxnet:%s clear!" % host_port)
            is_xxnet_exit = True
            break
        else:
            xlog.debug("<%d>: try to terminate xxnet:%s" % (i, host_port))
        time.sleep(1)
    xlog.debug("finished confirm_xxnet_exit")
    return is_xxnet_exit

def confirm_module_ready(port):
    if port == 0:
        xlog.error("confirm_module_ready with port 0")
        time.sleep(1)
        return False

    for i in range(200):
        req = http_request("http://127.0.0.1:%d/is_ready" % port)
        if req == False:
            time.sleep(1)
            continue

        content = req.read(1024)
        req.close()
        #xlog.debug("cert_import_ready return:%s", content)
        if content == "True":
            return True
        else:
            time.sleep(1)
    return False

if __name__ == "__main__":
    pass
    #confirm_xxnet_exit()
    # http_request("http://getbootstrap.com/dist/js/bootstrap.min.js")
