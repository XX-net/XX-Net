#!/usr/bin/env python
# -*- coding: utf-8 -*-


import threading
import time
import logging
import os
from config import config
import traceback

current_path = os.path.dirname(os.path.abspath(__file__))


class Check_ipv6():

    good_ip_file_name = "good_ipv6.txt"
    good_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, good_ip_file_name))
    default_good_ip_file = os.path.join(current_path, good_ip_file_name)
    bad_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, "bad_ipv6.txt"))


    searching_thread_count = 0

    ip_dict = {} # ip_str => {
                 # 'handshake_time'=>?ms,
                 # 'domain'=>CN,
                 # 'server'=>gws/gvs?,
                 # 'timeout'=>? , continue timeout num, if connect success, reset to 0
                 # history=>[[time,status], []]
                 # }

    gws_ip_list = [] # gererate from ip_dict, sort by handshake_time, when get_batch_ip
    bad_ip_pool = set()
    ip_lock = threading.Lock()
    iplist_need_save = 0
    iplist_saved_time = 0
    last_sort_time_for_gws = 0  # keep status for avoid wast too many cpu
    #ip_connect_interval = config.CONFIG.getint("google_ip", "ip_connect_interval") #5,10
    ip_connect_interval = 0.1

    # algorithm to get ip:
    # scan start from fastest ip
    # always use the fastest ip.
    # if the ip is used in 5 seconds, try next ip;
    # if the ip is fail in 60 seconds, try next ip;
    # reset pointer to front every 3 seconds
    gws_ip_pointer = 0
    gws_ip_pointer_reset_time = 0


    def __init__(self):
        self.load_ip()

        #if not self.is_ip_enough():
        self.search_more_google_ip()

    def load_ip(self):
        if os.path.isfile(self.good_ip_file):
            file_path = self.good_ip_file
        else:
            file_path = self.default_good_ip_file
        with open(file_path, "r") as fd:
            lines = fd.readlines()
        for line in lines:
            try:
                str_l = line.split(' ')
                if len(str_l) != 4:
                    logging.warning("line err: %s", line)
                    continue
                ip_str = str_l[0]
                domain = str_l[1]
                server = str_l[2]
                handshake_time = int(str_l[3])

                #logging.info("load ip: %s time:%d domain:%s server:%s", ip_str, handshake_time, domain, server)
                self.add_ip(ip_str, handshake_time, domain, server)
            except Exception as e:
                logging.exception("load_ip line:%s err:%s", line, e)

        logging.info("load google ip_list num:%d, gws num:%d", len(self.ip_dict), len(self.gws_ip_list))
        self.try_sort_ip_by_handshake_time(force=True)

        if os.path.isfile(self.bad_ip_file):
            with open(self.bad_ip_file, "r") as fd:
                for line in fd.readlines():
                    try:
                        if line == "\n":
                            continue
                        str_l = line.replace('\n', '')
                        ip = str_l[1]
                        self.bad_ip_pool.add(ip)
                    except Exception as e:
                        logging.exception("parse bad_ip.txt err:%r", e)

    def save_ip_list(self, force=False):
        pass

    def try_sort_ip_by_handshake_time(self, force=False):
        pass

    def add_ip(self, ip_str, handshake_time, domain=None, server=None):
        if not isinstance(ip_str, basestring):
            logging.error("add_ip input")

        handshake_time = int(handshake_time)

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['handshake_time'] = handshake_time
                self.ip_dict[ip_str]['timeout'] = 0
                self.ip_dict[ip_str]['history'].append([time.time(), handshake_time])
                return False

            self.iplist_need_save = 1

            self.ip_dict[ip_str] = {'handshake_time':handshake_time, 'domain':domain, 'server':server,
                                    'timeout':0, "history":[[time.time(), handshake_time]], "fail_time":0,
                                    "get_time":0}

            if 'gws' in server:
                self.gws_ip_list.append(ip_str)
            return True
        except Exception as e:
            logging.error("set_ip err:%s", e)
        finally:
            self.ip_lock.release()
        return False

    def get_gws_ip(self):

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            for i in range(ip_num):
                if ip_num == 0:
                    #logging.warning("no gws ip")
                    time.sleep(1)
                    return None


                if self.gws_ip_pointer >= ip_num:
                    if time.time() - self.gws_ip_pointer_reset_time < 1:
                        time.sleep(1)
                        continue
                    else:
                        self.gws_ip_pointer = 0
                        self.gws_ip_pointer_reset_time = time.time()
                elif self.gws_ip_pointer > 0 and time.time() - self.gws_ip_pointer_reset_time > 3:
                    self.gws_ip_pointer = 0
                    self.gws_ip_pointer_reset_time = time.time()

                ip_str = self.gws_ip_list[self.gws_ip_pointer]
                if self.is_bad_ip(ip_str):
                    self.gws_ip_pointer += 1
                    continue
                get_time = self.ip_dict[ip_str]["get_time"]
                if time.time() - get_time < self.ip_connect_interval:
                    self.gws_ip_pointer += 1
                    continue
                handshake_time = self.ip_dict[ip_str]["handshake_time"]
                fail_time = self.ip_dict[ip_str]["fail_time"]
                if time.time() - fail_time < 300:
                    self.gws_ip_pointer += 1
                    continue

                logging.debug("get ip:%s t:%d", ip_str, handshake_time)
                self.ip_dict[ip_str]['history'].append([time.time(), "get"])
                self.ip_dict[ip_str]['get_time'] = time.time()
                self.gws_ip_pointer += 1
                return ip_str
        except Exception as e:
            logging.error("get_gws_ip fail:%s", e)
            traceback.print_exc()
        finally:
            self.ip_lock.release()

    def get_host_ip(self, host):
        self.get_gws_ip()

    def is_bad_ip(self, ip):
        return False

    def update_ip(self, ip_str, handshake_time):
        pass

    def report_bad_ip(self, ip_str):
        pass

    def report_connect_fail(self, ip_str, force_remove=False):
        pass

    def search_more_google_ip(self):
        pass

    def update_scan_thread_num(self, num):
        pass





if __name__ == '__main__':
    pass

# test cast
# 1. good_ip.txt not exist when startup, auto scan good ip, then save
# 2. good_ip.txt exist, load ip list, and check it.
#


# google ip study about gvs
# each xx.googlevideo.com only have one ip
# and there is many many googlevideo ip and many many xx.googlevideo.com domain
# if GFW block some of the ip, direct connect to these domain if fail.test_mask
# There for, gvs can't direct connect if GFW block some some of it.