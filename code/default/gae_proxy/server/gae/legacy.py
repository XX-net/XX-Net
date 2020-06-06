#!/usr/bin/env python
# coding:utf-8

import time
from gae import __version__

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain; charset=UTF-8')])
    if environ['PATH_INFO'] == '/robots.txt':
        yield '\n'.join(['User-agent: *', 'Disallow: /'])
    else:
        timestamp = long(environ['CURRENT_VERSION_ID'].split('.')[1])/2**28
        ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp+8*3600))
        yield "GoAgent 服务端已经在 %s 升级到 %s 版本, 请更新您的客户端。" % (ctime, __version__)
