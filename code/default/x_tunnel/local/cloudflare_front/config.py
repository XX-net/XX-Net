#!/usr/bin/env python
# coding:utf-8


import ConfigParser
import os
import re
import io


from xlog import getLogger
xlog = getLogger("cloudflare_front")



class Config(object):
    current_path = os.path.dirname(os.path.abspath(__file__))

    def load(self):
        """load config from proxy.ini"""
        current_path = os.path.dirname(os.path.abspath(__file__))
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'default_config.ini'))

        self.DATA_PATH = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir, 'data', 'x_tunnel'))
        if not os.path.isdir(self.DATA_PATH):
            self.DATA_PATH = current_path

        self.CONFIG.read(self.CONFIG_FILENAME)

        # load ../../../data/gae_proxy/manual.ini, set by manual
        self.CONFIG_MANUAL_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'cloudflare_manual.ini'))
        if os.path.isfile(self.CONFIG_MANUAL_FILENAME):
            with open(self.CONFIG_MANUAL_FILENAME, 'rb') as fp:
                content = fp.read()
                try:
                    self.CONFIG.readfp(io.BytesIO(content))
                    xlog.info("load manual.ini success")
                except Exception as e:
                    xlog.exception("%s load error:%s", self.CONFIG_MANUAL_FILENAME, e)

        # load ../../../data/gae_proxy/config.ini, set by web_ui
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'cloudflare_config.ini'))
        if os.path.isfile(self.CONFIG_USER_FILENAME):
            with open(self.CONFIG_USER_FILENAME, 'rb') as fp:
                content = fp.read()
                try:
                    self.CONFIG.readfp(io.BytesIO(content))
                except Exception as e:
                    xlog.exception("%s load error:%s", self.CONFIG_USER_FILENAME, e)

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

        self.log_file = config.CONFIG.getint("system", "log_file")
        self.do_profile = config.CONFIG.getint("system", "do_profile")

        # change to True when finished import CA cert to browser
        # launcher will wait import ready then open browser to show status, check update etc
        self.cert_import_ready = False

    def get(self, section, key, default=""):
        try:
            value = self.CONFIG.get(section, key)
        except:
            value = default

        return value

    def getint(self, section, key, default=0):
        return int(self.get(section, key, str(default)))


config = Config()
config.load()

