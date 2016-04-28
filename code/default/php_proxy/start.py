#!/usr/bin/env python
# coding:utf-8

import os, sys


__file__ = os.path.abspath(__file__)
if os.path.islink(__file__):
    __file__ = getattr(os, 'readlink', lambda x: x)(__file__)

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_path)
import local.proxy as php_proxy



try:
    php_proxy.main()
except KeyboardInterrupt:
    sys.exit()