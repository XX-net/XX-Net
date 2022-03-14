#!/usr/bin/env python
# coding:utf-8

import os
import time


class None_tray():
    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        pass

    def on_quit(self, widget=None, data=None):
        import module_init

        module_init.stop_all()
        os._exit(0)

    def serve_forever(self):
        while True:
            time.sleep(100)


sys_tray = None_tray()


def main():
    sys_tray.serve_forever()


if __name__ == '__main__':
    main()
