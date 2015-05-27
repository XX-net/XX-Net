#!/usr/bin/env python
# -*- coding: utf-8 -*-
# based on checkgoogleip 'moonshawdo@gmail.com'


import threading
import operator
import time
import ip_utils
import check_ip
from google_ip_range import ip_range
import logging
import Queue
import os
from config import config
import traceback
import connect_control
from scan_ip_log import scan_ip_log

current_path = os.path.dirname(os.path.abspath(__file__))

class Check_ip():

    good_ip_file_name = "good_ip.txt"
    good_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, good_ip_file_name))
    bad_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, "bad_ip2.txt"))
    default_good_ip_file = os.path.join(current_path, "good_ip.txt")

    # get value from config:
    max_check_ip_thread_num = config.CONFIG.getint("google_ip", "max_check_ip_thread_num") #20
    max_good_ip_num = config.CONFIG.getint("google_ip", "max_good_ip_num") #3000  # stop scan ip when enough
    ip_connect_interval = config.CONFIG.getint("google_ip", "ip_connect_interval") #5,10

    searching_thread_count = 0
    ncount_lock = threading.Lock()

    to_remove_ip_list = Queue.Queue()
    remove_ip_thread_num = 0
    remove_ip_thread_num_lock = threading.Lock()

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

    # algorithm to get ip:
    # scan start from fastest ip
    # always use the fastest ip.
    # if the ip is used in 5 seconds, try next ip;
    # if the ip is fail in 60 seconds, try next ip;
    # reset pointer to front every 3 seconds
    gws_ip_pointer = 0
    gws_ip_pointer_reset_time = 0

    def is_ip_enough(self):
        if len(self.gws_ip_list) >= self.max_good_ip_num:
            return True
        else:
            return False

    def __init__(self):
        self.load_ip()

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
                        if not ip_utils.check_ip_valid(str_l):
                            logging.warning("bad_ip line err: %s", line)
                            continue
                        ip = str_l[1]
                        self.bad_ip_pool.add(ip)
                    except Exception as e:
                        logging.exception("parse bad_ip.txt err:%r", e)

    def save_ip_list(self, force=False):
        if not force:
            if self.iplist_need_save == 0:
                return
            if time.time() - self.iplist_saved_time < 10:
                return

        self.iplist_saved_time = time.time()

        try:
            self.ip_lock.acquire()
            with open(self.good_ip_file, "w") as fd:
                for ip_str, property in self.ip_dict.items():
                    fd.write( "%s %s %s %d\n" % (ip_str, property['domain'], property['server'], property['handshake_time']) )

            with open(self.bad_ip_file, "w") as fd:
                for ip in self.bad_ip_pool:
                    logging.debug("save bad ip:%s", ip)
                    fd.write("%s\n" % (ip))

            self.iplist_need_save = 0
        except Exception as e:
            logging.error("save good_ip.txt fail %s", e)
        finally:
            self.ip_lock.release()

    def try_sort_ip_by_handshake_time(self, force=False):
        if time.time() - self.last_sort_time_for_gws < 10 and not force:
            return
        self.last_sort_time_for_gws = time.time()

        self.ip_lock.acquire()
        try:
            ip_dict_handshake_time = {}
            for ip_str in self.ip_dict:
                if 'gws' not in self.ip_dict[ip_str]['server']:
                    continue
                ip_dict_handshake_time[ip_str] = self.ip_dict[ip_str]['handshake_time']

            ip_time = sorted(ip_dict_handshake_time.items(), key=operator.itemgetter(1))
            self.gws_ip_list = [ip_str for ip_str,handshake_time in ip_time]

        except Exception as e:
            logging.error("try_sort_ip_by_handshake_time:%s", e)
        finally:
            self.ip_lock.release()

        time_cost = (( time.time() - self.last_sort_time_for_gws) * 1000)
        logging.debug("sort ip time:%d", time_cost) # 5ms for 1000 ip.

    def get_gws_ip(self):
        self.try_sort_ip_by_handshake_time()

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
        self.try_sort_ip_by_handshake_time()

        self.ip_lock.acquire()
        try:
            ip_num = len(self.ip_dict)
            if ip_num == 0:
                #logging.warning("no gws ip")
                time.sleep(1)
                return None

            for ip_str in self.ip_dict:
                domain = self.ip_dict[ip_str]["domain"]
                if domain != host:
                    continue

                get_time = self.ip_dict[ip_str]["get_time"]
                if time.time() - get_time < 10:
                    continue
                handshake_time = self.ip_dict[ip_str]["handshake_time"]
                fail_time = self.ip_dict[ip_str]["fail_time"]
                if time.time() - fail_time < 300:
                    continue

                logging.debug("get host:%s ip:%s t:%d", host, ip_str, handshake_time)
                self.ip_dict[ip_str]['history'].append([time.time(), "get"])
                self.ip_dict[ip_str]['get_time'] = time.time()
                return ip_str
        except Exception as e:
            logging.error("get_gws_ip fail:%s", e)
            traceback.print_exc()
        finally:
            self.ip_lock.release()

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

    def update_ip(self, ip_str, handshake_time):
        if not isinstance(ip_str, basestring):
            logging.error("set_ip input")

        handshake_time = int(handshake_time)
        if handshake_time < 5: # this is impossible
            return

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:

                # Case: some good ip, average handshake time is 300ms
                # some times ip package lost cause handshake time become 2000ms
                # this ip will not return back to good ip front until all become bad
                # There for, prevent handshake time increase too quickly.
                org_time = self.ip_dict[ip_str]['handshake_time']
                if handshake_time - org_time > 100:
                    self.ip_dict[ip_str]['handshake_time'] = org_time + 100
                else:
                    self.ip_dict[ip_str]['handshake_time'] = handshake_time

                self.ip_dict[ip_str]['timeout'] = 0
                self.ip_dict[ip_str]['history'].append([time.time(), handshake_time])
                self.ip_dict[ip_str]["fail_time"] = 0
                self.iplist_need_save = 1
                return

            #logging.debug("update ip:%s not exist", ip_str)
        except Exception as e:
            logging.error("update_ip err:%s", e)
        finally:
            self.ip_lock.release()

    def report_bad_ip(self, ip_str):
        logging.debug("report_bad_ip %s", ip_str)
        if not ip_utils.check_ip_valid(ip_str):

            return
        self.bad_ip_pool.add(ip_str)
        self.save_ip_list(force=True)

    def is_bad_ip(self, ip_str):
        if ip_str in self.bad_ip_pool:
            return True
        return False

    def report_connect_fail(self, ip_str, force_remove=False):
        # ignore if system network is disconnected.
        if not force_remove:
            if not check_ip.network_is_ok():
                logging.debug("report_connect_fail network fail")
                return

        self.ip_lock.acquire()
        try:
            if not ip_str in self.ip_dict:
                return

            fail_time = self.ip_dict[ip_str]["fail_time"]
            if not force_remove and time.time() - fail_time < 1:
                return

            # increase handshake_time to make it can be used in lower probability
            self.ip_dict[ip_str]['handshake_time'] += 200
            self.ip_dict[ip_str]['timeout'] += 1
            self.ip_dict[ip_str]['history'].append([time.time(), "fail"])
            self.ip_dict[ip_str]["fail_time"] = time.time()

            if force_remove or self.ip_dict[ip_str]['timeout'] >= 50:
                property = self.ip_dict[ip_str]
                server = property['server']
                del self.ip_dict[ip_str]

                if 'gws' in server and ip_str in self.gws_ip_list:
                    self.gws_ip_list.remove(ip_str)

                logging.info("remove ip:%s left amount:%d gws_num:%d", ip_str, len(self.ip_dict), len(self.gws_ip_list))

                if not force_remove:
                    self.to_remove_ip_list.put(ip_str)
                    self.try_remove_thread()

            self.iplist_need_save = 1
        except Exception as e:
            logging.exception("set_ip err:%s", e)
        finally:
            self.ip_lock.release()


        if not self.is_ip_enough():
            self.search_more_google_ip()


    def try_remove_thread(self):
        if self.remove_ip_thread_num > 0:
            return

        self.remove_ip_thread_num_lock.acquire()
        self.remove_ip_thread_num += 1
        self.remove_ip_thread_num_lock.release()

        p = threading.Thread(target=self.remove_ip_process)
        p.daemon = True
        p.start()

    def remove_ip_process(self):
        try:
            while True:

                try:
                    ip_str = self.to_remove_ip_list.get_nowait()
                except:
                    break

                result = check_ip.test(ip_str)
                if result and result.appspot_ok:
                    self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type)
                    logging.debug("remove ip process, restore ip:%s", ip_str)
                    continue

                if not check_ip.network_is_ok():
                    self.to_remove_ip_list.put(ip_str)
                    logging.warn("network is unreachable. check your network connection.")
                    return

                logging.info("real remove ip:%s ", ip_str)
                self.iplist_need_save = 1
        finally:
            self.remove_ip_thread_num_lock.acquire()
            self.remove_ip_thread_num -= 1
            self.remove_ip_thread_num_lock.release()

    def remove_slowest_ip(self):
        if len(self.gws_ip_list) <= self.max_good_ip_num:
            return

        self.try_sort_ip_by_handshake_time(force=True)

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            while ip_num > self.max_good_ip_num:

                ip_str = self.gws_ip_list[ip_num - 1]

                property = self.ip_dict[ip_str]
                server = property['server']
                handshake_time = property['handshake_time']
                logging.info("remove_slowest_ip:%s handshake_time:%d", ip_str, handshake_time)
                del self.ip_dict[ip_str]

                if 'gws' in server and ip_str in self.gws_ip_list:
                    self.gws_ip_list.remove(ip_str)

                ip_num -= 1

        except Exception as e:
            logging.exception("remove_slowest_ip err:%s", e)
        finally:
            self.ip_lock.release()

    def scan_ip_worker(self):
        while self.searching_thread_count <= self.max_check_ip_thread_num:
            if not connect_control.allow_connect():
                time.sleep(10)
                continue

            try:
                time.sleep(1)
                ip_int = ip_range.get_ip()
                ip_str = ip_utils.ip_num_to_string(ip_int)
                if self.is_bad_ip(ip_str):
                    continue

                result = check_ip.test_gws(ip_str)
                if not result:
                    continue

                if self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type):
                    #logging.info("add  %s  CN:%s  type:%s  time:%d  gws:%d ", ip_str,
                    #     result.domain, result.server_type, result.handshake_time, len(self.gws_ip_list))
                    logging.info("scan_ip add ip:%s time:%d", ip_str, result.handshake_time)
                    scan_ip_log.info("Add %s time:%d CN:%s type:%s", ip_str, result.handshake_time, result.domain, result.server_type)
                    self.remove_slowest_ip()
                    self.save_ip_list()
            except check_ip.HoneypotError as e:
                self.report_bad_ip(ip_str)
                connect_control.fall_into_honeypot()
                continue
            except Exception as e:
                logging.exception("google_ip.runJob fail:%s", e)

        self.ncount_lock.acquire()
        self.searching_thread_count -= 1
        self.ncount_lock.release()
        logging.info("scan_ip_worker exit")

    def search_more_google_ip(self):
        while self.searching_thread_count < self.max_check_ip_thread_num:
            self.ncount_lock.acquire()
            self.searching_thread_count += 1
            self.ncount_lock.release()

            p = threading.Thread(target = self.scan_ip_worker)
            p.daemon = True
            p.start()

    def update_scan_thread_num(self, num):
        self.max_check_ip_thread_num = num
        self.search_more_google_ip()

if config.USE_IPV6:
    from google_ipv6 import Check_ipv6
    google_ip = Check_ipv6()
else:
    google_ip = Check_ip()


def test():
    google_ip.search_more_google_ip()
    #check.test_ip("74.125.130.98", print_result=True)
    while not google_ip.is_ip_enough():
        time.sleep(10)


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