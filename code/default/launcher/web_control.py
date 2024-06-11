#!/usr/bin/env python
# coding:utf-8

import os, sys
import errno
import re
import socket, ssl
import time
import threading
import json
import cgi
import traceback
import base64

try:
    from urllib.parse import urlparse, urlencode, parse_qs
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse, parse_qs
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

try:
    from urllib.request import ProxyHandler
    from urllib.request import build_opener
except ImportError:
    from urllib2 import ProxyHandler
    from urllib2 import build_opener


current_path = os.path.dirname(os.path.abspath(__file__))
default_path = os.path.abspath(os.path.join(current_path, os.pardir))
if __name__ == "__main__":
    noarch_lib = os.path.abspath(os.path.join(default_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)


import sys_platform
from xlog import getLogger, keep_log

xlog = getLogger("launcher")
import module_init
from config import config, valid_language, app_name
import autorun
import update
import update_from_github
import simple_http_client
import simple_http_server
import utils
from simple_i18n import SimpleI18N
import env_info

NetWorkIOError = (socket.error, ssl.SSLError, OSError)

current_version = utils.to_bytes(update_from_github.current_version())
i18n_translator = SimpleI18N()
i18n_translator.add_translate(b"APP_NAME", utils.to_bytes(app_name))
i18n_translator.add_translate(b"APP_VERSION", current_version)
module_menus = {}


class FakeHttpHandler(simple_http_server.HttpServerHandler):
    def handle_one_request(self):
        # This function will replace simple_http_server HttpHandler.handle_one_request to hold all http requests.
        # Doing this is to simulate bug.
        self.close_connection = 0


CORS_header = {
    "Allow": "GET,POST,OPTIONS",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,Sec-Fetch-Site,Sec-Fetch-Mode,Sec-Fetch-Dest",
    "Connection": "close",
}


class Http_Handler(simple_http_server.HttpServerHandler):
    deploy_proc = None

    def load_module_menus(self):
        global module_menus
        new_module_menus = {}

        modules = config.all_modules
        for module in modules:
            if getattr(config, "enable_" + module) != 1:
                continue

            menu_path = os.path.join(default_path, module, "web_ui", "menu.json")  # launcher & gae_proxy modules
            if not os.path.isfile(menu_path):
                continue

            # i18n code lines (Both the locale dir & the template dir are module-dependent)
            locale_dir = os.path.abspath(os.path.join(default_path, module, 'lang'))
            stream = i18n_translator.render(locale_dir, menu_path)
            module_menu = json.loads(utils.to_str(stream))
            new_module_menus[module] = module_menu

        module_menus = sorted(iter(new_module_menus.items()), key=lambda k_and_v: (k_and_v[1]['menu_sort_id']))
        # for k,v in self.module_menus:
        #    xlog.debug("m:%s id:%d", k, v['menu_sort_id'])

    def do_OPTIONS(self):
        # xlog.debug('%s "%s headers:%s from:%s', self.command, self.path, self.headers, self.address_string())
        try:
            origin = utils.to_str(self.headers.get(b'Origin'))
            # if origin not in self.config.allow_web_origins:
            #     return

            header = {
                "Allow": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS",
                "Access-Control-Allow-Headers": "Authorization,Content-Type",
            }
            return self.send_response(headers=header)
        except Exception as e:
            xlog.exception("options fail:%r", e)
            return self.send_not_found()

    def do_POST(self):
        self.headers = utils.to_str(self.headers)
        self.path = utils.to_str(self.path)

        refer = self.headers.get('Referer')
        if refer:
            refer_loc = urlparse(refer).netloc
            host = self.headers.get('Host')
            if refer_loc != host and refer_loc not in config.allowed_refers:
                xlog.warn("web control ref:%s host:%s", refer_loc, host)
                return

            self.set_CORS(CORS_header)

        try:
            content_type = self.headers.get('Content-Type', "")
            ctype, pdict = cgi.parse_header(content_type)
            if ctype == 'multipart/form-data':
                self.postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.get('Content-Length'))
                content = self.rfile.read(length)
                self.postvars = parse_qs(content, keep_blank_values=True)
                self.postvars = self.unpack_reqs(self.postvars)
            elif ctype == 'application/json':
                length = int(self.headers.get('Content-Length'))
                content = self.rfile.read(length)
                self.postvars = json.loads(content)
            else:
                self.postvars = {}
                content = b''
        except Exception as e:
            xlog.exception("do_POST %s except:%r", self.path, e)
            self.postvars = {}

        url_path_list = self.path.split('/')
        url_path = urlparse(self.path).path
        if len(url_path_list) >= 3 and url_path_list[1] == "module":
            module = url_path_list[2]
            if len(url_path_list) >= 4 and url_path_list[3] == "control":
                if module not in module_init.proc_handler:
                    xlog.warn("request %s no module in path", self.path)
                    return self.send_not_found()

                path = '/' + '/'.join(url_path_list[4:])
                controler = module_init.proc_handler[module]["imp"].local.web_control. \
                    ControlHandler(self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.set_CORS(self.res_headers)
                controler.postvars = utils.to_str(self.postvars)
                try:
                    controler.do_POST()
                    return
                except Exception as e:
                    xlog.exception("POST %s except:%r", path, e)

        elif url_path == "/set_proxy_applist":
            return self.set_proxy_applist()

        elif url_path.startswith("/openai/"):
            status, res_headers, res_body = module_init.proc_handler["x_tunnel"]["imp"].local.openai_handler.handle_openai(
                "POST", url_path, self.headers, content, self.connection)
            return self.send_response(content=res_body, headers=res_headers, status=status)

        else:
            self.send_not_found()
            xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def do_GET(self):
        self.headers = utils.to_str(self.headers)
        self.path = utils.to_str(self.path)

        refer = self.headers.get('Referer')
        if refer:
            refer_loc = urlparse(refer).netloc
            host = self.headers.get('Host')
            if refer_loc != host and refer_loc not in config.allowed_refers:
                xlog.warn("web control ref:%s host:%s", refer_loc, host)
                return

            self.set_CORS(CORS_header)

        # check for '..', which will leak file
        if re.search(r'(\.{2})', self.path) is not None:
            self.wfile.write(b'HTTP/1.1 404\r\n\r\n')
            xlog.warn('%s %s %s haking', self.address_string(), self.command, self.path)
            return

        if config.webui_auth:
            auth = self.headers.get("Authorization")
            if not auth or not auth.startswith("Basic "):
                return self.send_response(content="", headers={
                    "WWW-Authenticate": 'Basic realm="Access to admin"'
                }, status=401)

            try:
                user_pass = base64.b64decode(auth[6:])
                user_pass = utils.to_str(user_pass)
                user, password = user_pass.split(":")[0:2]
            except Exception as e:
                xlog.warn("decode auth fail:%r", e)
                return self.send_response(content="", headers={
                    "WWW-Authenticate": 'Basic realm="Access to admin"'
                }, status=401)

            if config.webui_auth.get(user) != password:
                return self.send_response(content="", headers={
                    "WWW-Authenticate": 'Basic realm="Access to admin"'
                }, status=401)

        url_path = urlparse(self.path).path
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
                controler = module_init.proc_handler[module]["imp"].local.web_control.ControlHandler(
                    self.client_address, self.headers, self.command, path, self.rfile, self.wfile)
                controler.set_CORS(self.res_headers)
                controler.do_GET()
                return
            else:
                relate_path = '/'.join(url_path_list[3:])
                file_path = os.path.join(default_path, module, "web_ui", relate_path)
                if not os.path.isfile(file_path):
                    return self.send_not_found()

                # i18n code lines (Both the locale dir & the template dir are module-dependent)
                locale_dir = os.path.abspath(os.path.join(default_path, module, 'lang'))
                content = i18n_translator.render(locale_dir, file_path)
                return self.send_response('text/html', content)
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
        else:
            xlog.debug('launcher web_control %s %s %s ', self.address_string(), self.command, self.path)
            if url_path == '/config':
                self.req_config_handler()
            elif url_path == "/log":
                return self.req_log_handler()
            elif url_path == "/keep_log":
                return self.req_keep_log_handler()
            elif url_path == "/suck_threads":
                return self.req_suck_threads()
            elif url_path == "/hold_8085":
                return self.req_hold_8085()
            elif url_path == '/update':
                self.req_update_handler()
            elif url_path == '/config_proxy':
                self.req_config_proxy_handler()
            elif url_path == '/installed_app':
                self.req_get_installed_app()
            elif url_path == '/init_module':
                self.req_init_module_handler()
            elif url_path == '/quit':
                content = b'System: %s Exited successfully.' % utils.to_bytes(sys_platform.platform)
                try:
                    self.send_response('text/html', content)
                    self.wfile.flush()
                except:
                    pass

                xlog.info("start quit")
                if sys_platform.platform in ["android", "ios"]:
                    try:
                        xlog.info("request http://localhost:8084/quit/")
                        simple_http_client.request("GET", "http://localhost:8084/quit/", timeout=1)
                    except Exception as e:
                        xlog.warn("request http://localhost:8084/quit/ e:%r", e)
                        pass

                sys_platform.on_quit()
            elif url_path == "/debug":
                self.req_debug_handler()
            elif url_path == "/log_files":
                self.req_log_files()
            elif url_path == "/mem_info":
                self.req_mem_info_handler()
            elif url_path == "/gc":
                self.req_gc_handler()
            elif url_path == '/restart':
                self.send_response('text/html', '{"status":"success"}')
                update_from_github.restart_xxnet()
            else:
                self.send_not_found()
                xlog.info('%s "%s %s HTTP/1.1" 404 -', self.address_string(), self.command, self.path)

    def req_index_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)

        try:
            target_module = reqs['module'][0]
            target_menu = reqs['menu'][0]
        except:
            if config.enable_x_tunnel:
                target_module = 'x_tunnel'
                target_menu = 'config'
            # elif config.get(['modules', 'smart_router', 'auto_start'], 0) == 1:
            #     target_module = 'smart_router'
            #     target_menu = 'config'
            elif config.enable_gae_proxy:
                target_module = 'gae_proxy'
                target_menu = 'status'
            else:
                target_module = 'launcher'
                target_menu = 'about'

        if len(module_menus) == 0:
            self.load_module_menus()

        # i18n code lines (Both the locale dir & the template dir are module-dependent)
        locale_dir = os.path.abspath(os.path.join(current_path, 'lang'))
        fn = os.path.join(current_path, "web_ui", "index.html")
        try:
            index_content = i18n_translator.render(locale_dir, fn)
        except Exception as e:
            xlog.warn("render %s except:%r", fn, e)
            return self.send_not_found()

        menu_content = b''
        for module, v in module_menus:
            # xlog.debug("m:%s id:%d", module, v['menu_sort_id'])
            title = v["module_title"]
            menu_content += b'<li class="nav-header">%s</li>\n' % utils.to_bytes(title)
            for sub_id in v['sub_menus']:
                list_meta = b''
                web_id = v['sub_menus'][sub_id].get("id")
                if web_id:
                    list_meta += b' id="%s"' % sub_id

                sub_title = v['sub_menus'][sub_id]['title']
                if "url" in v['sub_menus'][sub_id]:
                    sub_url = v['sub_menus'][sub_id]['url']
                    if target_module == module and target_menu == sub_url:
                        list_meta += b'class="active"'

                    menu_content += b'<li %s><a href="/?module=%s&menu=%s">%s</a></li>\n' % utils.to_bytes(
                        (list_meta, module, sub_url, sub_title))
                elif "api_url" in v['sub_menus'][sub_id]:
                    api_url = v['sub_menus'][sub_id]["api_url"]
                    menu_content += b'<li %s><a href="%s">%s</a></li>\n' % utils.to_bytes(
                        (list_meta, api_url, sub_title))

        right_content_file = os.path.join(default_path, target_module, "web_ui", target_menu + ".html")
        if os.path.isfile(right_content_file):
            # i18n code lines (Both the locale dir & the template dir are module-dependent)
            locale_dir = os.path.abspath(os.path.join(default_path, target_module, 'lang'))
            right_content = i18n_translator.render(locale_dir, os.path.join(default_path, target_module, "web_ui",
                                                                            target_menu + ".html"))
        else:
            right_content = b""

        data = index_content % (config.enable_gae_proxy, menu_content, right_content)
        self.send_response('text/html', data)

    def req_config_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)
        reqs = self.unpack_reqs(reqs)
        data = ''

        if reqs['cmd'] == 'get_config':

            if module_init.xargs.get("allow_remote", 0):
                allow_remote_connect = 1
            else:
                allow_remote_connect = config.allow_remote_connect

            dat = {
                "platform": sys_platform.platform,
                "check_update": config.check_update,
                "language": config.language or i18n_translator.lang,
                "popup_webui": config.popup_webui,
                "allow_remote_connect": allow_remote_connect,
                "allow_remote_switch": config.allow_remote_connect,
                "show_systray": config.show_systray,
                "show_android_notification": config.show_android_notification,
                "auto_start": config.auto_start,
                "show_detail": config.gae_show_detail,
                "gae_proxy_enable": config.enable_gae_proxy,
                "x_tunnel_enable": config.enable_x_tunnel,
                "smart_router_enable": config.enable_smart_router,
                "system-proxy": config.os_proxy_mode,
                "show-compat-suggest": config.show_compat_suggest,
                "no_mess_system": config.no_mess_system,
                "keep_old_ver_num": config.keep_old_ver_num,
                "postUpdateStat": config.postUpdateStat,
            }
            data = json.dumps(dat)
        elif reqs['cmd'] == 'set_config':
            if 'skip_version' in reqs:
                skip_version = reqs['skip_version']
                skip_version_type = reqs['skip_version_type']
                if skip_version_type not in ["stable", "test"]:
                    data = '{"res":"fail"}'
                else:
                    setattr(config, "skip_%s_version" % skip_version_type, skip_version)
                    config.save()
                    if skip_version in update_from_github.update_info:
                        update_from_github.update_info = ''
                    data = '{"res":"success"}'
            elif 'check_update' in reqs:
                check_update = reqs['check_update']
                if check_update not in ["dont-check", "stable", "notice-stable", "test", "notice-test"]:
                    data = '{"res":"fail, check_update:%s"}' % check_update
                else:
                    if config.check_update != check_update:
                        update_from_github.init_update_info(check_update)
                        config.check_update = check_update
                        config.save()

                    data = '{"res":"success"}'
            elif 'language' in reqs:
                language = reqs['language']

                if language not in valid_language:
                    data = '{"res":"fail, language:%s"}' % language
                else:
                    config.language = language
                    config.save()

                    i18n_translator.lang = language
                    self.load_module_menus()

                    data = '{"res":"success"}'
            elif 'popup_webui' in reqs:
                popup_webui = int(reqs['popup_webui'])
                if popup_webui != 0 and popup_webui != 1:
                    data = '{"res":"fail, popup_webui:%s"}' % popup_webui
                else:
                    config.popup_webui = popup_webui
                    config.save()

                    data = '{"res":"success"}'
            elif 'allow_remote_switch' in reqs:
                allow_remote_switch = int(reqs['allow_remote_switch'])
                if allow_remote_switch != 0 and allow_remote_switch != 1:
                    data = '{"res":"fail, allow_remote_connect:%s"}' % allow_remote_switch
                else:

                    try:
                        del module_init.xargs["allow_remote"]
                    except:
                        pass

                    if allow_remote_switch:
                        module_init.call_each_module("set_bind_ip", {
                            "ip": "0.0.0.0"
                        })
                    else:
                        module_init.call_each_module("set_bind_ip", {
                            "ip": "127.0.0.1"
                        })

                    config.allow_remote_connect = allow_remote_switch
                    config.save()

                    xlog.debug("restart web control.")
                    stop()
                    module_init.stop_all()
                    time.sleep(1)
                    start(allow_remote_switch)
                    module_init.start_all_auto()

                    xlog.debug("launcher web control restarted.")
                    data = '{"res":"success"}'
            elif 'show_systray' in reqs:
                show_systray = int(reqs['show_systray'])
                if show_systray != 0 and show_systray != 1:
                    data = '{"res":"fail, show_systray:%s"}' % show_systray
                else:
                    config.show_systray = show_systray
                    config.save()

                    data = '{"res":"success"}'
            elif 'show_android_notification' in reqs:
                show_android_notification = int(reqs['show_android_notification'])
                if show_android_notification != 0 and show_android_notification != 1:
                    data = '{"res":"fail, show_systray:%s"}' % show_android_notification
                else:
                    config.show_android_notification = show_android_notification
                    config.save()

                    data = '{"res":"success"}'
            elif 'show_compat_suggest' in reqs:
                show_compat_suggest = int(reqs['show_compat_suggest'])
                if show_compat_suggest != 0 and show_compat_suggest != 1:
                    data = '{"res":"fail, show_compat_suggest:%s"}' % show_compat_suggest
                else:
                    config.show_compat_suggest = show_compat_suggest
                    config.save()

                    data = '{"res":"success"}'
            elif 'no_mess_system' in reqs:
                no_mess_system = int(reqs['no_mess_system'])
                if no_mess_system != 0 and no_mess_system != 1:
                    data = '{"res":"fail, no_mess_system:%s"}' % no_mess_system
                else:
                    config.no_mess_system = no_mess_system
                    config.save()

                    data = '{"res":"success"}'
            elif 'keep_old_ver_num' in reqs:
                keep_old_ver_num = int(reqs['keep_old_ver_num'])
                if keep_old_ver_num < 0 or keep_old_ver_num > 99:
                    data = '{"res":"fail, keep_old_ver_num:%s not in range 0 to 99"}' % keep_old_ver_num
                else:
                    config.keep_old_ver_num = keep_old_ver_num
                    config.save()

                    data = '{"res":"success"}'
            elif 'auto_start' in reqs:
                auto_start = int(reqs['auto_start'])
                if auto_start != 0 and auto_start != 1:
                    data = '{"res":"fail, auto_start:%s"}' % auto_start
                else:
                    if auto_start:
                        autorun.enable()
                    else:
                        autorun.disable()

                    config.auto_start = auto_start
                    config.save()

                    data = '{"res":"success"}'
            elif 'show_detail' in reqs:
                show_detail = int(reqs['show_detail'])
                if show_detail != 0 and show_detail != 1:
                    data = '{"res":"fail, show_detail:%s"}' % show_detail
                else:
                    config.gae_show_detail = show_detail
                    config.save()

                    data = '{"res":"success"}'
            elif 'gae_proxy_enable' in reqs:
                gae_proxy_enable = int(reqs['gae_proxy_enable'])
                if gae_proxy_enable != 0 and gae_proxy_enable != 1:
                    data = '{"res":"fail, gae_proxy_enable:%s"}' % gae_proxy_enable
                else:
                    config.enable_gae_proxy = gae_proxy_enable
                    config.save()
                    if gae_proxy_enable:
                        module_init.start("gae_proxy")
                    else:
                        module_init.stop("gae_proxy")

                    if config.enable_smart_router:
                        module_init.stop("smart_router")
                        module_init.start("smart_router")

                    self.load_module_menus()
                    data = '{"res":"success"}'
            elif 'x_tunnel_enable' in reqs:
                x_tunnel_enable = int(reqs['x_tunnel_enable'])
                if x_tunnel_enable != 0 and x_tunnel_enable != 1:
                    data = '{"res":"fail, x_tunnel_enable:%s"}' % x_tunnel_enable
                else:
                    config.enable_x_tunnel = x_tunnel_enable
                    config.save()
                    if x_tunnel_enable:
                        module_init.start("x_tunnel")
                    else:
                        module_init.stop("x_tunnel")
                    self.load_module_menus()
                    data = '{"res":"success"}'
            elif 'smart_router_enable' in reqs:
                smart_router_enable = int(reqs['smart_router_enable'])
                if smart_router_enable != 0 and smart_router_enable != 1:
                    data = '{"res":"fail, smart_router_enable:%s"}' % smart_router_enable
                else:
                    config.enable_smart_router = smart_router_enable
                    config.save()
                    if smart_router_enable:
                        module_init.start("smart_router")
                    else:
                        module_init.stop("smart_router")
                    self.load_module_menus()
                    data = '{"res":"success"}'
            elif 'postUpdateStat' in reqs:
                postUpdateStat = reqs['postUpdateStat']
                if postUpdateStat not in ["noChange", "isNew", "isPostUpdate"]:
                    data = '{"res":"fail, postUpdateStat:%s"}' % postUpdateStat
                else:
                    config.postUpdateStat = postUpdateStat
                    config.save()
                    data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'
        elif reqs['cmd'] == 'get_version':
            current_version = update_from_github.current_version()
            data = '{"current_version":"%s"}' % current_version

        self.send_response('text/html', data)

    def req_update_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_info']:
            data = update_from_github.update_info
            if data == '' or data[0] != '{':
                data = '{"type":"%s"}' % data
        elif reqs['cmd'] == ['set_info']:
            update_from_github.update_info = reqs['info']
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['start_check']:
            update_from_github.init_update_info(reqs['check_update'])
            update.check_update()
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['get_progress']:
            data = json.dumps(update_from_github.progress)
        elif reqs['cmd'] == ['get_new_version']:
            current_version = update_from_github.current_version()
            github_versions = update_from_github.get_github_versions()
            data = '{"res":"success", "test_version":"%s", "stable_version":"%s", "current_version":"%s"}' % (
            github_versions[0][1], github_versions[1][1], current_version)
            xlog.info("%s", data)
        elif reqs['cmd'] == ['update_version']:
            version = reqs['version']

            checkhash = 1
            if 'checkhash' in reqs and reqs['checkhash'] == '0':
                checkhash = 0

            update_from_github.start_update_version(version, checkhash)
            data = '{"res":"success"}'
        elif reqs['cmd'] == ['set_localversion']:
            version = reqs['version']

            if update_from_github.update_current_version(version):
                data = '{"res":"success"}'
            else:
                data = '{"res":"false", "reason": "version not exist"}'
        elif reqs['cmd'] == ['get_localversions']:
            local_versions = update_from_github.get_local_versions()

            s = ""
            for v in local_versions:
                if not s == "":
                    s += ","
                s += ' { "v":"%s" , "folder":"%s" } ' % (v[0], v[1])
            data = '[  %s  ]' % (s)
        elif reqs['cmd'] == ['del_localversion']:
            if update_from_github.del_version(reqs['version']):
                data = '{"res":"success"}'
            else:
                data = '{"res":"fail"}'

        self.send_response('text/html', data)

    def req_config_proxy_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)
        data = ''

        if reqs['cmd'] == ['get_config']:
            data = {
                "enable": config.global_proxy_enable,
                "type": config.global_proxy_type,
                "host": config.global_proxy_host,
                "port": config.global_proxy_port,
                "user": config.global_proxy_username,
                "passwd": config.global_proxy_password,
            }
            data = json.dumps(data)
        elif reqs['cmd'] == ['set_config']:
            enable = int(reqs['enable'])
            type = reqs['type']
            host = reqs['host']
            port = int(reqs['port'])
            user = reqs['user']
            passwd = reqs['passwd']

            if int(enable) and not test_proxy(type, host, port, user, passwd):
                return self.send_response('text/html', '{"res":"fail", "reason": "test proxy fail"}')

            config.global_proxy_enable = enable
            config.global_proxy_type = type
            config.global_proxy_host = host
            config.global_proxy_port = port
            config.global_proxy_username = user
            config.global_proxy_password = passwd
            config.save()

            module_init.call_each_module("set_proxy", {
                "enable": enable,
                "type": type,
                "host": host,
                "port": port,
                "user": user,
                "passwd": passwd
            })

            data = '{"res":"success"}'
        self.send_response('text/html', data)

    def req_get_installed_app(self):
        if sys_platform.platform != 'android':
            # simulate data for developing
            data = {
                "proxy_by_app": config.proxy_by_app,
                "installed_app_list": [
                    {
                        "name": "Test",
                        "package": "com.test"
                    },{
                        "name": "APP",
                        "package": "com.app"
                    },{
                        "name": "com.google.foundation.Foundation.Application.",
                        "package": "com.google.application"
                    }
                ]
            }
            time.sleep(5)
        else:
            res = simple_http_client.request("GET", "http://localhost:8084/installed_app_list/")
            data = json.loads(res.text)
            data["proxy_by_app"] = config.proxy_by_app

        for app in data["installed_app_list"]:
            package = app["package"]
            if package in config.enabled_app_list:
                app["enable"] = True
            else:
                app["enable"] = False

        if config.proxy_by_app:
            # Pass the config in html.
            content = '<div id="proxy_by_app_config" checked hidden></div>'
        else:
            content = '<div id="proxy_by_app_config" hidden></div>'

        for app in data["installed_app_list"]:
            if app["enable"]:
                checked = " checked "
            else:
                checked = ""

            content += '<div class="row-fluid"> <div class="config_label" >'\
                        + app["name"] \
                        + '</div><div class="config_switch"><input class="app_item" id="'\
                        + app['package']\
                        + '" type="checkbox" data-toggle="switch" '\
                        + checked\
                        + '/></div></div>\n'\

        # jquery can't work on dynamic insert elements.
        # load html content from backend is the best way to make it works.

        return self.send_response("text/html", content)

    def set_proxy_applist(self):
        self.postvars = utils.to_str(self.postvars)
        xlog.debug("set_proxy_applist %r", self.postvars)
        config.proxy_by_app = int(self.postvars.get('proxy_by_app') == "true")
        config.enabled_app_list = self.postvars.get("enabled_app_list[]", [])
        xlog.debug("set_proxy_applist proxy_by_app:%s", config.proxy_by_app)
        xlog.debug("set_proxy_applist enabled_app_list:%s", config.enabled_app_list)
        config.save()

        data = {
            "res": "success"
        }
        self.send_response("text/html", json.dumps(data))

    def req_init_module_handler(self):
        req = urlparse(self.path).query
        reqs = self.unpack_reqs(parse_qs(req, keep_blank_values=True))
        data = ''

        try:
            module = reqs['module']
            config.load()

            if reqs['cmd'] == 'start':
                result = module_init.start(module)
                data = '{ "module": "%s", "cmd": "start", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == 'stop':
                result = module_init.stop(module)
                data = '{ "module": "%s", "cmd": "stop", "result": "%s" }' % (module, result)
            elif reqs['cmd'] == 'restart':
                result_stop = module_init.stop(module)
                result_start = module_init.start(module)
                data = '{ "module": "%s", "cmd": "restart", "stop_result": "%s", "start_result": "%s" }' % (
                module, result_stop, result_start)
        except Exception as e:
            xlog.exception("init_module except:%s", e)

        self.send_response("text/html", data, headers={"Access-Control-Allow-Origin": "*"})

    def req_keep_log_handler(self):
        keep_log()
        data = "Keep log success."

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_suck_threads(self):
        self.send_response('text/plain', "Start suck threads")
        while True:
            threading.Thread(target=time.sleep, args=(1000,)).start()

    def req_hold_8085(self):
        global server
        self.send_response('text/plain', "Hold 8085")
        server.handler = FakeHttpHandler

    def req_log_handler(self):
        req = urlparse(self.path).query
        reqs = self.unpack_reqs(parse_qs(req, keep_blank_values=True))
        data = ''

        if reqs["cmd"]:
            cmd = reqs["cmd"]
        else:
            cmd = "get_last"

        if cmd == "get_last":
            max_line = int(reqs["max_line"])
            data = xlog.get_last_lines(max_line)
        elif cmd == "get_new":
            last_no = int(reqs["last_no"])
            data = xlog.get_new_lines(last_no)
        else:
            xlog.error('xtunnel log cmd:%s', cmd)

        mimetype = 'text/plain'
        self.send_response(mimetype, data)

    def req_gc_handler(self):
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)

        import gc
        count = gc.get_count()

        if "collect" in reqs:
            gc.collect()

        self.send_response("text/plain", "gc collected, count:%d,%d,%d" % count)

    @staticmethod
    def list_fds():
        """List process currently open FDs and their target """
        if not sys.platform.startswith('linux'):
            return ""

        dat = ""
        base = '/proc/self/fd'
        of = list(os.listdir(base))
        dat += "Num: %d\r\n" % (len(of))
        for num in of:
            path = None
            try:
                path = os.readlink(os.path.join(base, num))
            except OSError as err:
                # Last FD is always the "listdir" one (which may be closed)
                if err.errno != errno.ENOENT:
                    path = str(err)
            except Exception as e:
                path = str(e)
            dat += " [%s]: %s\r\n" % (num, path)

        return dat

    def req_debug_handler(self):
        dat = ""

        try:
            dat += "Opened files: \r\n%s \r\n" % self.list_fds()

            dat += "thread num:%d\r\n" % threading.active_count()
            for thread in threading.enumerate():
                dat += "\nThread: %s \r\n" % (thread.name)
                stack = sys._current_frames()[thread.ident]
                st = traceback.extract_stack(stack)
                stl = traceback.format_list(st)
                dat += " \n".join(stl)

        except Exception as e:
            xlog.exception("debug:%r", e)

        self.send_response("text/plain", dat)

    def req_log_files(self):
        # pack data folder and response
        x_tunnel_local = os.path.abspath(os.path.join(default_path, 'x_tunnel', 'local'))
        sys.path.append(x_tunnel_local)
        from upload_logs import pack_logs

        data = pack_logs(200 * 1024 * 1024)
        self.send_response("application/zip", data)

    def req_mem_info_handler(self):
        global mem_stat
        req = urlparse(self.path).query
        reqs = parse_qs(req, keep_blank_values=True)

        try:
            import tracemalloc
            import gc
            import os
            import linecache

            python_lib = os.path.dirname(os.__file__)
            gc.collect()

            if not mem_stat:
                tracemalloc.start()

            if not mem_stat or "reset" in reqs:
                mem_stat = tracemalloc.take_snapshot()

            snapshot = tracemalloc.take_snapshot()

            if "compare" in reqs:
                top_stats = snapshot.compare_to(mem_stat, 'traceback')
            else:
                top_stats = snapshot.statistics('traceback')

            dat = ""
            for stat in top_stats[:100]:
                print(("%s memory blocks: %.1f KiB" % (stat.count, stat.size / 1024)))
                lines = stat.traceback.format()
                ll = "\n".join(lines)
                ln = len(lines)
                pl = ""
                for i in range(ln, 0, -1):
                    line = lines[i - 1]
                    print(line)
                    if line[8:].startswith(python_lib):
                        break
                    if not line.startswith("  File"):
                        pl = line
                        continue
                    if not line[8:].startswith(default_path):
                        break
                    ll = line[8:] + "\n" + pl

                if ll[0] == "[":
                    pass

                dat += "%d KB, count:%d %s\n" % (stat.size / 1024, stat.count, ll)

            if hasattr(threading, "_start_trace"):
                dat += "\n\nThread stat:\n"
                for path in threading._start_trace:
                    n = threading._start_trace[path]
                    if n <= 1:
                        continue
                    dat += "%s => %d\n\n" % (path, n)

            dat += "thread num:%d<br>" % threading.active_count()

            self.send_response("text/plain", dat)
        except Exception as e:
            xlog.exception("debug:%r", e)
            self.send_response("text/html", "no mem_top")


mem_stat = None


def test_proxy(type, host, port, user, passwd):
    if not host:
        return False

    if host == "127.0.0.1":
        if port in [8087, 1080, 8086]:
            xlog.warn("set LAN Proxy to %s:%d fail.", host, port)
            return False

    client = simple_http_client.Client(proxy={
        "type": type,
        "host": host,
        "port": int(port),
        "user": user if len(user) else None,
        "pass": passwd if len(passwd) else None
    }, timeout=3)

    urls = [
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://code.jquery.com",
        "https://cdn.bootcss.com",
        "https://cdnjs.cloudflare.com"]

    for url in urls:
        header = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, sdch",
            "accept-language": 'en-US,en;q=0.8,ja;q=0.6,zh-CN;q=0.4,zh;q=0.2',
            "connection": "keep-alive"
        }
        try:
            response = client.request("HEAD", url, header, "")
            if response:
                return True
        except Exception as e:
            xlog.exception("test_proxy %s fail:%r", url, e)
            pass

    return False


server = None


def start(allow_remote=0):
    global server
    # should use config.yaml to bind ip
    if not allow_remote:
        allow_remote = config.allow_remote_connect
    host_ip = config.control_ip
    host_port = config.control_port

    if allow_remote:
        xlog.info("allow remote access WebUI")

    listen_ips = []
    if allow_remote and ("0.0.0.0" not in listen_ips or "::" not in listen_ips):
        listen_ips.append("0.0.0.0")
    else:
        if isinstance(host_ip, str):
            listen_ips = [host_ip]
        else:
            listen_ips = list(host_ip)

    addresses = [(listen_ip, host_port) for listen_ip in listen_ips]

    xlog.info("begin to start web control:%s", addresses)

    server = simple_http_server.HTTPServer(addresses, Http_Handler, logger=xlog)
    server.start()

    xlog.info("launcher web control started.")


def stop():
    global server
    xlog.info("begin to exit web control")
    server.shutdown()
    xlog.info("launcher web control exited.")


def http_request(url, method="GET", timeout=30):
    proxy_handler = ProxyHandler({})
    opener = build_opener(proxy_handler)
    try:
        req = opener.open(url, timeout=timeout)
        return req
    except Exception as e:
        # xlog.exception("web_control http_request:%s fail:%s", url, e)
        return False


def confirm_xxnet_not_running():
    # if xxnet is already running, try exit it
    is_xxnet_exit = False
    host_port = config.control_port
    req_url = "http://127.0.0.1:{port}/quit".format(port=host_port)
    xlog.debug("start confirm_xxnet_exit url:%s", req_url)

    for i in range(30):
        if http_request(req_url, timeout=5) == False:
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
        xlog.error("confirm_module_ready with port: 0")
        time.sleep(1)
        return False

    for i in range(200):
        req = http_request("http://127.0.0.1:%d/is_ready" % port)
        if req == False:
            time.sleep(1)
            continue

        content = req.read(1024)
        req.close()
        # xlog.debug("cert_import_ready return:%s", content)
        if content == "True":
            return True
        else:
            time.sleep(1)
    return False


if __name__ == "__main__":
    pass
    # confirm_xxnet_exit()
