#!/usr/bin/env python
# coding:utf-8

import os
import time

import global_var


class None_tray():
    def notify_general(self, msg="msg", title="Title", buttons={}, timeout=3600):
        pass

    def on_quit(self, widget=None, data=None):
        import module_init

        global_var.running = False
        module_init.stop_all()
        os._exit(0)

    def serve_forever(self):
        while global_var.running:
            time.sleep(10)


sys_tray = None_tray()


def main():
    sys_tray.serve_forever()


if __name__ == '__main__':
    main()
