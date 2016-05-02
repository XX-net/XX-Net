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
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
data_gae_proxy_path = os.path.join(data_path, 'gae_proxy')
python_path = os.path.abspath( os.path.join(root_path, 'python27', '1.0'))

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
import threading
import urllib2

__file__ = os.path.abspath(__file__)
if os.path.islink(__file__):
    __file__ = getattr(os, 'readlink', lambda x: x)(__file__)
work_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(work_path)


def create_data_path():
    if not os.path.isdir(data_path):
        os.mkdir(data_path)

    if not os.path.isdir(data_gae_proxy_path):
        os.mkdir(data_gae_proxy_path)
create_data_path()


from config import config

from xlog import getLogger
xlog = getLogger("gae_proxy")
xlog.set_buffer(2000)
if config.log_file:
    log_file = os.path.join(data_gae_proxy_path, "local.log")
    xlog.set_file(log_file)

from cert_util import CertUtil
import pac_server
import simple_http_server
import proxy_handler
import connect_control
import env_info
import connect_manager
from gae_handler import spawn_later


# launcher/module_init will check this value for start/stop finished
ready = False

def pre_start():

    if config.PAC_ENABLE:
        pac_ip = config.PAC_IP
        url = 'http://%s:%d/%s' % (pac_ip, config.PAC_PORT, config.PAC_FILE)
        spawn_later(600, urllib2.build_opener(urllib2.ProxyHandler({})).open, url)


def log_info():
    xlog.info('------------------------------------------------------')
    xlog.info('Python Version     : %s', platform.python_version())
    xlog.info('OS                 : %s', env_info.os_detail())
    xlog.info('Listen Address     : %s:%d', config.LISTEN_IP, config.LISTEN_PORT)
    if config.PROXY_ENABLE:
        xlog.info('%s Proxy    : %s:%s', config.PROXY_TYPE, config.PROXY_HOST, config.PROXY_PORT)
    xlog.info('GAE APPID          : %s', '|'.join(config.GAE_APPIDS))
    if config.PAC_ENABLE:
        xlog.info('Pac Server         : http://%s:%d/%s', config.PAC_IP, config.PAC_PORT, config.PAC_FILE)
        #info += 'Pac File           : file://%s\n' % os.path.join(self.DATA_PATH, self.PAC_FILE)
    xlog.info('------------------------------------------------------')


def main():
    global ready

    connect_control.keep_running = True
    config.load()
    connect_manager.https_manager.load_config()

    xlog.debug("## GAEProxy set keep_running: %s", connect_control.keep_running)
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
    #xlog.basicConfig(level=xlog.DEBUG if config.LISTEN_DEBUGINFO else xlog.INFO, format='%(levelname)s - %(asctime)s %(message)s', datefmt='[%b %d %H:%M:%S]')
    pre_start()
    log_info()

    CertUtil.init_ca()

    proxy_daemon = simple_http_server.HTTPServer((config.LISTEN_IP, config.LISTEN_PORT), proxy_handler.GAEProxyHandler)
    proxy_thread = threading.Thread(target=proxy_daemon.serve_forever)
    proxy_thread.setDaemon(True)
    proxy_thread.start()

    if config.PAC_ENABLE:
        pac_daemon = simple_http_server.HTTPServer((config.PAC_IP, config.PAC_PORT), pac_server.PACServerHandler)
        pac_thread = threading.Thread(target=pac_daemon.serve_forever)
        pac_thread.setDaemon(True)
        pac_thread.start()

    ready = True  # checked by launcher.module_init

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
    ready = False  # checked by launcher.module_init
    xlog.debug("## GAEProxy set keep_running: %s", connect_control.keep_running)

    if do_profile:
        pr.disable()
        pr.print_stats()


# called by launcher/module/stop
def terminate():
    xlog.info("start to terminate GAE_Proxy")
    connect_control.keep_running = False
    xlog.debug("## Set keep_running: %s", connect_control.keep_running)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stdout)
    except KeyboardInterrupt:
        terminate()
        sys.exit()
