#!/usr/bin/env python
# coding:utf-8

import os
import sys


__file__ = os.path.abspath(__file__)
if os.path.islink(__file__):
    __file__ = getattr(os, 'readlink', lambda x: x)(__file__)

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.path.pardir))
sys.path.append(root_path)
import x_tunnel.local.client as client


def main():
    try:
        client.main()
    except KeyboardInterrupt:
        sys.exit()

if __name__ == "__main__":
    main()
