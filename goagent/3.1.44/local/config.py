#!/usr/bin/env python
# coding:utf-8




import ConfigParser
import os
import sys
import re
import io
import collections
import fnmatch





class Config(object):
    """Global Config Object"""

    current_path = os.path.dirname(os.path.abspath(__file__))

    version = current_path.split(os.path.sep)[-2]

    __version__ = version
    python_version = sys.version[:5]


    def load(self):
        """load config from proxy.ini"""
        current_path = os.path.dirname(os.path.abspath(__file__))
        ConfigParser.RawConfigParser.OPTCRE = re.compile(r'(?P<option>[^=\s][^=]*)\s*(?P<vi>[=])\s*(?P<value>.*)$')
        self.CONFIG = ConfigParser.ConfigParser()
        self.CONFIG_FILENAME = os.path.abspath( os.path.join(current_path, 'proxy.ini'))

        self.DATA_PATH = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, os.pardir, 'data', 'goagent'))
        if not os.path.isdir(self.DATA_PATH):
            self.DATA_PATH = current_path

        # load ../../../data/goagent/config.ini
        self.CONFIG_USER_FILENAME = os.path.abspath( os.path.join(self.DATA_PATH, 'config.ini'))

        self.CONFIG.read(self.CONFIG_FILENAME)
        if os.path.isfile(self.CONFIG_USER_FILENAME):
            with open(self.CONFIG_USER_FILENAME, 'rb') as fp:
                content = fp.read()
                self.CONFIG.readfp(io.BytesIO(content))

        self.LISTEN_IP = self.CONFIG.get('listen', 'ip')
        self.LISTEN_PORT = self.CONFIG.getint('listen', 'port')
        self.LISTEN_VISIBLE = self.CONFIG.getint('listen', 'visible')
        self.LISTEN_DEBUGINFO = self.CONFIG.getint('listen', 'debuginfo')

        self.GAE_APPIDS = re.findall(r'[\w\-\.]+', self.CONFIG.get('gae', 'appid').replace('.appspot.com', ''))
        self.GAE_PASSWORD = self.CONFIG.get('gae', 'password').strip()

        self.HOSTS_MAP = collections.OrderedDict((k, v or k) for k, v in self.CONFIG.items('hosts') if '\\' not in k and ':' not in k and not k.startswith('.'))
        self.HOSTS_POSTFIX_MAP = collections.OrderedDict((k, v) for k, v in self.CONFIG.items('hosts') if '\\' not in k and ':' not in k and k.startswith('.'))
        self.HOSTS_POSTFIX_ENDSWITH = tuple(self.HOSTS_POSTFIX_MAP)

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

        self.keep_run = True

    def info(self):
        info = ''
        info += '------------------------------------------------------\n'
        info += 'GoAgent Version    : %s (python/%s )\n' % (self.__version__, sys.version[:5])
        info += 'Listen Address     : %s:%d\n' % (self.LISTEN_IP, self.LISTEN_PORT)
        if self.CONTROL_ENABLE:
            info += 'Control Address    : %s:%d\n' % (self.CONTROL_IP, self.CONTROL_PORT)
        if self.PROXY_ENABLE:
            info += '%s Proxy    : %s:%s\n' % (self.PROXY_TYPE, self.PROXY_HOST, self.PROXY_PORT)
        info += 'Debug INFO         : %s\n' % self.LISTEN_DEBUGINFO if self.LISTEN_DEBUGINFO else ''
        info += 'GAE APPID          : %s\n' % '|'.join(self.GAE_APPIDS)
        if self.PAC_ENABLE:
            info += 'Pac Server         : http://%s:%d/%s\n' % (self.PAC_IP, self.PAC_PORT, self.PAC_FILE)
            #info += 'Pac File           : file://%s\n' % os.path.join(self.DATA_PATH, self.PAC_FILE)
        info += '------------------------------------------------------\n'
        return info


config = Config()
config.load()