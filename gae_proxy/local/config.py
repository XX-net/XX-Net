#!/usr/bin/env python
# coding:utf-8


import ConfigParser
import os
import re
import io
import xlog



class Config(object):
    current_path = os.path.dirname(os.path.abspath(__file__))

    def load(self):
        """load config from proxy.ini"""
        current_path = os.path.dirname(os.path.abspath(__file__))
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'proxy.ini'))

        self.DATA_PATH = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'data', 'gae_proxy'))
        if not os.path.isdir(self.DATA_PATH):
            self.DATA_PATH = current_path

        # load ../../../data/gae_proxy/config.ini, set by web_ui
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'config.ini'))
        self.CONFIG.read(self.CONFIG_FILENAME)
        if os.path.isfile(self.CONFIG_USER_FILENAME):
            with open(self.CONFIG_USER_FILENAME, 'rb') as fp:
                content = fp.read()
                self.CONFIG.readfp(io.BytesIO(content))

        # load ../../../data/gae_proxy/manual.ini, set by manual
        self.CONFIG_MANUAL_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'manual.ini'))
        if os.path.isfile(self.CONFIG_MANUAL_FILENAME):
            with open(self.CONFIG_MANUAL_FILENAME, 'rb') as fp:
                content = fp.read()
                try:
                    self.CONFIG.readfp(io.BytesIO(content))
                    xlog.info("load manual.ini success")
                except Exception as e:
                    xlog.exception("data/gae_proxy/manual.ini load error:%s", e)

        self.LISTEN_IP = self.CONFIG.get('listen', 'ip')
        self.LISTEN_PORT = self.CONFIG.getint('listen', 'port')
        self.LISTEN_VISIBLE = self.CONFIG.getint('listen', 'visible')
        self.LISTEN_DEBUGINFO = self.CONFIG.getint('listen', 'debuginfo')

        self.GAE_APPIDS = re.findall(r'[\w\-\.]+', self.CONFIG.get('gae', 'appid').replace('.appspot.com', ''))
        self.GAE_PASSWORD = self.CONFIG.get('gae', 'password').strip()

        fwd_endswith = []
        fwd_hosts = []
        direct_endswith = []
        direct_hosts = []
        gae_endswith = []
        gae_hosts = []
        for k, v in self.CONFIG.items('hosts'):
            if v == "fwd":
                if k.startswith('.'):
                    fwd_endswith.append(k)
                else:
                    fwd_hosts.append(k)
            elif v == "direct":
                if k.startswith('.'):
                    direct_endswith.append(k)
                else:
                    direct_hosts.append(k)
            elif v == "gae":
                if k.startswith('.'):
                    gae_endswith.append(k)
                else:
                    gae_hosts.append(k)
        self.HOSTS_FWD_ENDSWITH = tuple(fwd_endswith)
        self.HOSTS_FWD = tuple(fwd_hosts)
        self.HOSTS_GAE_ENDSWITH = tuple(gae_endswith)
        self.HOSTS_GAE = tuple(gae_hosts)
        self.HOSTS_DIRECT_ENDSWITH = tuple(direct_endswith)
        self.HOSTS_DIRECT = tuple(direct_hosts)

        self.AUTORANGE_MAXSIZE = self.CONFIG.getint('autorange', 'maxsize')
        self.AUTORANGE_WAITSIZE = self.CONFIG.getint('autorange', 'waitsize')
        self.AUTORANGE_BUFSIZE = self.CONFIG.getint('autorange', 'bufsize')
        self.AUTORANGE_THREADS = self.CONFIG.getint('autorange', 'threads')

        self.PAC_ENABLE = self.CONFIG.getint('pac', 'enable')
        self.PAC_IP = self.CONFIG.get('pac', 'ip')
        self.PAC_PORT = self.CONFIG.getint('pac', 'port')
        self.PAC_FILE = self.CONFIG.get('pac', 'file').lstrip('/')
        self.PAC_GFWLIST = self.CONFIG.get('pac', 'gfwlist')
        self.PAC_ADBLOCK = self.CONFIG.get('pac', 'adblock') if self.CONFIG.has_option('pac', 'adblock') else ''
        self.PAC_EXPIRED = self.CONFIG.getint('pac', 'expired')
        self.pac_url = 'http://%s:%d/%s\n' % (self.PAC_IP, self.PAC_PORT, self.PAC_FILE)

        self.CONTROL_ENABLE = self.CONFIG.getint('control', 'enable')
        self.CONTROL_IP = self.CONFIG.get('control', 'ip')
        self.CONTROL_PORT = self.CONFIG.getint('control', 'port')

        self.PROXY_ENABLE = self.CONFIG.getint('proxy', 'enable')
        self.PROXY_TYPE = self.CONFIG.get('proxy', 'type')
        self.PROXY_HOST = self.CONFIG.get('proxy', 'host')
        self.PROXY_PORT = self.CONFIG.get('proxy', 'port')
        if self.PROXY_PORT == "":
            self.PROXY_PORT = 0
        else:
            self.PROXY_PORT = int(self.PROXY_PORT)
        self.PROXY_USER = self.CONFIG.get('proxy', 'user')
        self.PROXY_PASSWD = self.CONFIG.get('proxy', 'passwd')

        self.LOVE_ENABLE = self.CONFIG.getint('love', 'enable')
        self.LOVE_TIP = self.CONFIG.get('love', 'tip').encode('utf8').decode('unicode-escape').split('|')

        self.USE_IPV6 = self.CONFIG.getint('google_ip', 'use_ipv6')
        self.https_max_connect_thread = config.CONFIG.getint("connect_manager", "https_max_connect_thread")
        self.connect_interval = config.CONFIG.getint("connect_manager", "connect_interval")

        # change to True when finished import CA cert to browser
        # launcher will wait import ready then open browser to show status, check update etc
        self.cert_import_ready = False



config = Config()
config.load()

