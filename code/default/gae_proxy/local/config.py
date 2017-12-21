#!/usr/bin/env python
# coding:utf-8


import ConfigParser
import os
import re
import io


from xlog import getLogger
xlog = getLogger("gae_proxy")



class Config(object):
    current_path = os.path.dirname(os.path.abspath(__file__))

    def load(self):
        """load config from proxy.ini"""
        current_path = os.path.dirname(os.path.abspath(__file__))
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'proxy.ini'))

        self.DATA_PATH = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, os.pardir, 'data', 'gae_proxy'))
        if not os.path.isdir(self.DATA_PATH):
            self.DATA_PATH = current_path

        self.CONFIG.read(self.CONFIG_FILENAME)

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

        # load ../../../data/gae_proxy/config.ini, set by web_ui
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'config.ini'))
        if os.path.isfile(self.CONFIG_USER_FILENAME):
            with open(self.CONFIG_USER_FILENAME, 'rb') as fp:
                content = fp.read()
                try:
                    self.CONFIG.readfp(io.BytesIO(content))
                except Exception as e:
                    xlog.exception("data/gae_proxy/config.ini load error:%s", e)

        self.LISTEN_IP = self.CONFIG.get('listen', 'ip')
        self.LISTEN_PORT = self.CONFIG.getint('listen', 'port')

        self.PUBLIC_APPIDS = [x.strip() for x in self.CONFIG.get('gae', 'public_appid').split("|")]
        if self.CONFIG.get('gae', 'appid'):
            self.GAE_APPIDS = [x.strip() for x in self.CONFIG.get('gae', 'appid').split("|")]
        else:
            self.GAE_APPIDS = []
        self.GAE_PASSWORD = self.CONFIG.get('gae', 'password').strip()
        self.GAE_VALIDATE = self.CONFIG.getint('gae', 'validate')

        self.PROXY_HOSTS_ONLY = []
        for x in self.CONFIG.get('switch_rule', 'proxy_hosts_only').split("|"):
            x = x.strip()
            if len(x):
                self.PROXY_HOSTS_ONLY.append(x)
        if len(self.PROXY_HOSTS_ONLY):
            xlog.info("Only these hosts will proxy: %s", self.PROXY_HOSTS_ONLY)

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

        br_sites = []
        br_endswith = []
        for k, v in self.CONFIG.items('br_sites'):
            if k.startswith("."):
                br_endswith.append(k)
            else:
                br_sites.append(k)
        self.br_sites = tuple(br_sites)
        self.br_endswith = tuple(br_endswith)

        # hack here:
        # 2.x.x version save host mode to direct in data/gae_proxy/config.ini
        # now(2016.5.5) many google ip don't support direct mode.
        try:
            direct_hosts.remove("appengine.google.com")
        except:
            pass
        try:
            direct_hosts.remove("www.google.com")
        except:
            pass
        self.HOSTS_DIRECT_ENDSWITH = tuple(direct_endswith)
        self.HOSTS_DIRECT = tuple(direct_hosts)

        self.AUTORANGE_MAXSIZE = self.CONFIG.getint('autorange', 'maxsize')
        self.AUTORANGE_THREADS = self.CONFIG.getint('autorange', 'threads')

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
        if self.PROXY_ENABLE:
            xlog.info("use LAN proxy: %s://%s:%s", self.PROXY_TYPE, self.PROXY_HOST, self.PROXY_PORT)

        self.USE_IPV6 = self.CONFIG.get('google_ip', 'use_ipv6')
        if self.USE_IPV6 not in ["auto", "force_ipv4", "force_ipv6"]:
            xlog.debug("config use_ipv6 %s upgrade to auto", self.USE_IPV6)
            self.USE_IPV6 = "auto"

        self.max_links_per_ip = self.CONFIG.getint('google_ip', 'max_links_per_ip')
        self.record_ip_history = self.CONFIG.getint('google_ip', 'record_ip_history')
        self.ip_connect_interval = self.CONFIG.getint('google_ip', 'ip_connect_interval')

        self.https_max_connect_thread = config.CONFIG.getint("connect_manager", "https_max_connect_thread")
        self.connect_interval = config.CONFIG.getint("connect_manager", "connect_interval")

        self.log_file = config.CONFIG.getint("system", "log_file")
        self.do_profile = config.CONFIG.getint("system", "do_profile")

        # change to True when finished import CA cert to browser
        # launcher will wait import ready then open browser to show status, check update etc
        self.cert_import_ready = False



config = Config()
config.load()

