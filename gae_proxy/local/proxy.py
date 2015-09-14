#!/usr/bin/env python2
# coding:utf-8
# Based on GAppProxy 2.0.0 by Du XiaoGang <dugang.2008@gmail.com>
# Based on WallProxy 0.4.0 by Hust Moon <www.ehust@gmail.com>
# Contributor:
#      Phus Lu           <phus.lu@gmail.com>
#      Hewig Xu          <hewigovens@gmail.com>
#      Ayanamist Yang    <ayanamist@gmail.com>
#      V.E.O             <V.E.O@tom.com>
#      Max Lv            <max.c.lv@gmail.com>
#      AlsoTang          <alsotang@gmail.com>
#      Christopher Meng  <cickumqt@gmail.com>
#      Yonsm Guo         <YonsmGuo@gmail.com>
#      Parkman           <cseparkman@gmail.com>
#      Ming Bai          <mbbill@gmail.com>
#      Bin Yu            <yubinlove1991@gmail.com>
#      lileixuan         <lileixuan@gmail.com>
#      Cong Ding         <cong@cding.org>
#      Zhang Youfu       <zhangyoufu@gmail.com>
#      Lu Wei            <luwei@barfoo>
#      Harmony Meow      <harmony.meow@gmail.com>
#      logostream        <logostream@gmail.com>
#      Rui Wang          <isnowfy@gmail.com>
#      Wang Wei Qiang    <wwqgtxx@gmail.com>
#      Felix Yan         <felixonmars@gmail.com>
#      QXO               <qxodream@gmail.com>
#      Geek An           <geekan@foxmail.com>
#      Poly Rabbit       <mcx_221@foxmail.com>
#      oxnz              <yunxinyi@gmail.com>
#      Shusen Liu        <liushusen.smart@gmail.com>
#      Yad Smood         <y.s.inside@gmail.com>
#      Chen Shuang       <cs0x7f@gmail.com>
#      cnfuyu            <cnfuyu@gmail.com>
#      cuixin            <steven.cuixin@gmail.com>




import sys
import os

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)

if sys.platform == "win32":
    win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
    sys.path.append(win32_lib)
elif sys.platform.startswith("linux"):
    linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
    sys.path.append(linux_lib)
elif sys.platform == "darwin":
    darwin_lib = os.path.abspath( os.path.join(python_path, 'lib', 'darwin'))
    sys.path.append(darwin_lib)
    extra_lib = "/System/Library/Frameworks/Python.framework/Versions/2.7/Extras/lib/python"
    sys.path.append(extra_lib)

import time
import traceback
import platform

import errno
import xlog
import random
import threading
import SocketServer
import urllib2

__file__ = os.path.abspath(__file__)
if os.path.islink(__file__):
    __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
work_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(work_path)

from cert_util import CertUtil
import pac_server

import socket, ssl
NetWorkIOError = (socket.error, ssl.SSLError, OSError)

import proxy_handler
import connect_control
import env_info
from config import config

from gae_handler import spawn_later

ready = False





class LocalProxyServer(SocketServer.ThreadingTCPServer):
    """Local Proxy Server"""
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





def pre_start():

    def get_windows_running_process_list():
        import os
        import glob
        import ctypes
        import collections
        Process = collections.namedtuple('Process', 'pid name exe')
        process_list = []
        if os.name == 'nt':
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            lpidProcess= (ctypes.c_ulong * 1024)()
            cb = ctypes.sizeof(lpidProcess)
            cbNeeded = ctypes.c_ulong()
            ctypes.windll.psapi.EnumProcesses(ctypes.byref(lpidProcess), cb, ctypes.byref(cbNeeded))
            nReturned = cbNeeded.value/ctypes.sizeof(ctypes.c_ulong())
            pidProcess = [i for i in lpidProcess][:nReturned]
            has_queryimage = hasattr(ctypes.windll.kernel32, 'QueryFullProcessImageNameA')
            for pid in pidProcess:
                hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid)
                if hProcess:
                    modname = ctypes.create_string_buffer(2048)
                    count = ctypes.c_ulong(ctypes.sizeof(modname))
                    if has_queryimage:
                        ctypes.windll.kernel32.QueryFullProcessImageNameA(hProcess, 0, ctypes.byref(modname), ctypes.byref(count))
                    else:
                        ctypes.windll.psapi.GetModuleFileNameExA(hProcess, 0, ctypes.byref(modname), ctypes.byref(count))
                    exe = modname.value
                    name = os.path.basename(exe)
                    process_list.append(Process(pid=pid, name=name, exe=exe))
                    ctypes.windll.kernel32.CloseHandle(hProcess)
        elif sys.platform.startswith('linux'):
            for filename in glob.glob('/proc/[0-9]*/cmdline'):
                pid = int(filename.split('/')[2])
                exe_link = '/proc/%d/exe' % pid
                if os.path.exists(exe_link):
                    exe = os.readlink(exe_link)
                    name = os.path.basename(exe)
                    process_list.append(Process(pid=pid, name=name, exe=exe))
        else:
            try:
                import psutil
                process_list = psutil.get_process_list()
            except Exception as e:
                xlog.exception('psutil.get_windows_running_process_list() failed: %r', e)
        return process_list


    if sys.platform == 'cygwin':
        xlog.info('cygwin is not officially supported, please continue at your own risk :)')
        #sys.exit(-1)
    elif os.name == 'posix':
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_NOFILE, (8192, -1))
        except Exception as e:
            pass
    elif os.name == 'nt':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(u'GoAgent ')
        if not config.LISTEN_VISIBLE:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        else:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
        if config.LOVE_ENABLE and random.randint(1, 100) <= 5:
            title = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetConsoleTitleW(ctypes.byref(title), len(title)-1)
            ctypes.windll.kernel32.SetConsoleTitleW('%s %s' % (title.value, random.choice(config.LOVE_TIP)))
        blacklist = {'360safe': False,
                     'QQProtect': False, }
        softwares = [k for k, v in blacklist.items() if v]
        if softwares:
            tasklist = '\n'.join(x.name for x in get_windows_running_process_list()).lower()
            softwares = [x for x in softwares if x.lower() in tasklist]
            if softwares:
                title = u'GoAgent 建议'
                error = u'某些安全软件(如 %s)可能和本软件存在冲突，造成 CPU 占用过高。\n如有此现象建议暂时退出此安全软件来继续运行GoAgent' % ','.join(softwares)
                ctypes.windll.user32.MessageBoxW(None, error, title, 0)
                #sys.exit(0)
    if config.GAE_APPIDS[0] == 'gae_proxy':
        xlog.critical('please edit %s to add your appid to [gae] !', config.CONFIG_FILENAME)
        sys.exit(-1)
    if config.PAC_ENABLE:
        pac_ip = config.PAC_IP
        url = 'http://%s:%d/%s' % (pac_ip, config.PAC_PORT, config.PAC_FILE)
        spawn_later(600, urllib2.build_opener(urllib2.ProxyHandler({})).open, url)

def log_info():
    xlog.info('------------------------------------------------------')
    xlog.info('Python Version     : %s', platform.python_version())
    xlog.info('OS                 : %s', env_info.os_detail())
    xlog.info('Listen Address     : %s:%d', config.LISTEN_IP, config.LISTEN_PORT)
    if config.CONTROL_ENABLE:
        xlog.info('Control Address    : %s:%d', config.CONTROL_IP, config.CONTROL_PORT)
    if config.PROXY_ENABLE:
        xlog.info('%s Proxy    : %s:%s', config.PROXY_TYPE, config.PROXY_HOST, config.PROXY_PORT)
    xlog.info('GAE APPID          : %s', '|'.join(config.GAE_APPIDS))
    if config.PAC_ENABLE:
        xlog.info('Pac Server         : http://%s:%d/%s', config.PAC_IP, config.PAC_PORT, config.PAC_FILE)
        #info += 'Pac File           : file://%s\n' % os.path.join(self.DATA_PATH, self.PAC_FILE)
    xlog.info('------------------------------------------------------')

def main():
    global ready
    # to profile gae_proxy, run proxy.py, visit some web by proxy, then visit http://127.0.0.1:8084/quit to quit and print result.
    do_profile = False
    if do_profile:
        import cProfile, pstats
        pr = cProfile.Profile()
        pr.enable()

    global __file__
    __file__ = os.path.abspath(__file__)
    if os.path.islink(__file__):
        __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    xlog.basicConfig(level=xlog.DEBUG if config.LISTEN_DEBUGINFO else xlog.INFO, format='%(levelname)s - %(asctime)s %(message)s', datefmt='[%b %d %H:%M:%S]')
    pre_start()
    log_info()

    CertUtil.init_ca()

    proxy_daemon = LocalProxyServer((config.LISTEN_IP, config.LISTEN_PORT), proxy_handler.GAEProxyHandler)
    proxy_thread = threading.Thread(target=proxy_daemon.serve_forever)
    proxy_thread.setDaemon(True)
    proxy_thread.start()

    if config.PAC_ENABLE:
        pac_daemon = LocalProxyServer((config.PAC_IP, config.PAC_PORT), pac_server.PACServerHandler)
        pac_thread = threading.Thread(target=pac_daemon.serve_forever)
        pac_thread.setDaemon(True)
        pac_thread.start()

    ready = True #checked by launcher.module_init

    while connect_control.keep_running:
        time.sleep(1)

    xlog.info("Exiting gae_proxy module...")
    proxy_daemon.shutdown()
    proxy_daemon.server_close()
    proxy_thread.join()
    if config.PAC_ENABLE:
        pac_daemon.shutdown()
        pac_daemon.server_close()
        pac_thread.join()
    ready = False #checked by launcher.module_init
    xlog.info("Finished Exiting gae_proxy module...")

    if do_profile:
        pr.disable()
        pr.print_stats()

def terminate():
    connect_control.keep_running = False

if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stdout)
    except KeyboardInterrupt:
        terminate()
        sys.exit()
