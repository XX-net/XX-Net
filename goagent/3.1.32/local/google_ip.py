#!/usr/bin/env python
# -*- coding: utf-8 -*-
# base on checkgoogleip 'moonshawdo@gmail.com'


import threading
import operator
import time

import ip_utils
import check_ip
from google_ip_range import ip_range
import logging
import httplib
import random
import Queue

# const value:
max_check_ip_thread_num = 10
min_good_ip_num = 95
max_good_ip_num = 100
timeout = 5000 # 5 second


class Check_ip():
    ncount = 0
    ncount_lock = threading.Lock()

    to_remove_ip_list = Queue.Queue()
    remove_ip_thread_num = 0
    remove_ip_thread_lock = threading.Lock()

    ip_dict = {} # ip_str => { 'handshake_time'=>?, 'domain'=>, 'server'=>?}
    gws_ip_list = [] # gererate from ip_dict, sort by handshake_time, when get_batch_ip
    ip_lock = threading.Lock()
    iplist_need_save = 0
    last_sort_time_for_gws = 0

    network_fail_time = 0

    def is_ip_enough(self):
        if len(self.gws_ip_list) >= min_good_ip_num:
            return True
        else:
            return False

    def __init__(self):
        self.load_ip()

        if not self.is_ip_enough():
            self.search_more_google_ip()

    def load_ip(self):
        try:
            fd = open("good_ip.txt", "r")
            for line in fd.readlines():
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
            fd.close()
            logging.info("load google iplist num: %d, gws num:%d", len(self.ip_dict), len(self.gws_ip_list))

            p = threading.Thread(target = self.check_exist_ip)
            p.daemon = True
            p.start()
        except Exception as e:
            logging.warn("load google good ip fail: %s", e)

    def save_ip_list(self):
        if self.iplist_need_save == 0:
            return

        try:
            self.ip_lock.acquire()
            with open("good_ip.txt", "w") as fd:
                for ip_str, property in self.ip_dict.items():
                    fd.write( "%s %s %s %d\n" % (ip_str, property['domain'], property['server'], property['handshake_time']) )
            self.iplist_need_save = 0
        except Exception as e:
            logging.error("save good_ip.txt fail %s", e)
        finally:
            self.ip_lock.release()

    def add_ip(self, ip_str, handshake_time, domain=None, server=None):
        if not isinstance(ip_str, basestring):
            logging.error("set_ip input")

        handshake_time = int(handshake_time)
        if handshake_time >= timeout:
            return False

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['handshake_time'] = handshake_time
                #logging.debug("add ip:%s duplicated", ip_str)
                return False

            self.iplist_need_save = 1
            self.ip_dict[ip_str] = {'handshake_time':handshake_time, 'domain':domain, 'server':server}

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
        if handshake_time >= timeout:
            self.report_connect_fail(ip_str)
            return

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['handshake_time'] = handshake_time
                return

            #logging.debug("update ip:%s not exist", ip_str)
        except Exception as e:
            logging.error("set_ip err:%s", e)
        finally:
            self.ip_lock.release()


    def report_connect_fail(self, ip_str):
        if not isinstance(ip_str, basestring):
            logging.error("set_ip input")

        if time.time() - self.network_fail_time < 3:
            return


        self.ip_lock.acquire()
        try:
            if not ip_str in self.ip_dict:
                return

            handshake_time = self.ip_dict[ip_str]['handshake_time']
            handshake_time += 300
            self.ip_dict[ip_str]['handshake_time'] = handshake_time

            if handshake_time >= timeout:
                property = self.ip_dict[ip_str]
                server = property['server']
                del self.ip_dict[ip_str]

                if 'gws' in server and ip_str in self.gws_ip_list:
                    self.gws_ip_list.remove(ip_str)

                logging.info("remove ip:%s left amount:%d gws_num:%d", ip_str, len(self.ip_dict), len(self.gws_ip_list))

                self.to_remove_ip_list.put(ip_str)
                self.try_remove_thread()


        except Exception as e:
            logging.error("set_ip err:%s", e)
        finally:
            self.ip_lock.release()

        self.try_sort_ip_by_handshake_time(force=True)

        if not self.is_ip_enough():
            self.search_more_google_ip()


    def try_remove_thread(self):
        if self.remove_ip_thread_num > 0:
            return

        self.remove_ip_thread_lock.acquire()
        self.remove_ip_thread_num += 1
        self.remove_ip_thread_lock.release()

        p = threading.Thread(target=self.remove_ip_process)
        p.daemon = True
        p.start()

    def network_is_ok(self):
        try:
            conn = httplib.HTTPConnection("www.baidu.com")
            conn.request("HEAD", "/")
            response = conn.getresponse()
            if response.status == 200:
                return True
            else:
                return False
        except:
            return False

    def remove_ip_process(self):
        try:

            while True:
                if not self.network_is_ok():
                    self.network_fail_time = time.time()
                    return

                try:
                    ip_str = self.to_remove_ip_list.get_nowait()
                except:
                    break

                result = check_ip.test(ip_str)
                if result and result.appspot_ok:
                    self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type)
                    logging.debug("remove ip process, restore ip:%s", ip_str)
                    continue

                logging.info("real remove ip:%s ", ip_str)

        finally:
            self.remove_ip_thread_lock.acquire()
            self.remove_ip_thread_num -= 1
            self.remove_ip_thread_lock.release()


    def try_sort_ip_by_handshake_time(self, force=False):
        self.ip_lock.acquire()
        try:
            if force or time.time() - self.last_sort_time_for_gws > 10:
                ip_dict_handshake_time = {}
                for ip_str in self.ip_dict:
                    if 'gws' not in self.ip_dict[ip_str]['server']:
                        continue
                    ip_dict_handshake_time[ip_str] = self.ip_dict[ip_str]['handshake_time']
                ip_time = sorted(ip_dict_handshake_time.items(), key=operator.itemgetter(1))
                self.gws_ip_list = [ip_str for ip_str,handshake_time in ip_time]
                self.last_sort_time_for_gws = time.time()
        finally:
            self.ip_lock.release()



    def get_gws_ip(self):
        self.try_sort_ip_by_handshake_time()

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            if ip_num == 0:
                #logging.warning("no gws ip")
                time.sleep(1)
                return None

            fastest_num = min(ip_num-1, 5)
            index = random.randint(0, fastest_num)
            ip_str = self.gws_ip_list[index]
            #logging.debug("get ip:%s t:%d", ip_str, handshake_time)
            return ip_str
        except Exception as e:
            logging.error("get_gws_ip fail:%s", e)
        finally:
            self.ip_lock.release()


    def check_ip(self, ip_str):
        result = check_ip.test_gws(ip_str)
        if not result:
            return False

        if self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type):
            logging.info("add  %s  CN:%s  type:%s  time:%d  gws:%d ", ip_str,
                 result.domain, result.server_type, result.handshake_time, len(self.gws_ip_list))

        return True

    def runJob(self):
        while not self.is_ip_enough():
            try:
                time.sleep(1)
                ip_int = ip_range.get_ip()
                ip_str = ip_utils.ip_num_to_string(ip_int)
                if self.check_ip(ip_str):
                    self.save_ip_list()
            except Exception as e:
                logging.warn("google_ip.runJob fail:%s", e)

        self.ncount_lock.acquire()
        self.ncount -= 1
        self.ncount_lock.release()

    def search_more_google_ip(self):
        while self.ncount < max_check_ip_thread_num:
            self.ncount_lock.acquire()
            self.ncount += 1
            self.ncount_lock.release()
            p = threading.Thread(target = self.runJob)
            p.daemon = True
            p.start()

    def check_exist_ip(self):
        self.ip_lock.acquire()
        tmp_ip_list = [x for x in self.gws_ip_list]
        self.ip_lock.release()

        for ip_str in tmp_ip_list:

            result = check_ip.test(ip_str)
            if not result or not result.appspot_ok:
                self.report_connect_fail(ip_str)
            else:
                self.update_ip(ip_str, result.handshake_time)

        self.save_ip_list()

google_ip = Check_ip()

def test():
    check = Check_ip()
    check.search_more_google_ip()
    #check.test_ip("74.125.130.98", print_result=True)
    while not check.is_ip_enough():
        time.sleep(10)

def test_profile():
    do_profile = True
    if do_profile:
        import cProfile, pstats
        pr = cProfile.Profile()
        pr.enable()

    test()

    if do_profile:
        pr.disable()
        pr.print_stats(sort="cum")


if __name__ == '__main__':
    check = Check_ip()
    res = check.network_is_ok()
    print res

# test cast
# 1. good_ip.txt not exist when startup, auto scan good ip, then save
# 2. good_ip.txt exist, load ip list, and check it.
#


# google ip study about gvs
# each xx.googlevideo.com only have one ip
# and there is many many googlevideo ip and many many xx.googlevideo.com domain
# if GFW block some of the ip, direct connect to these domain if fail.
# There for, gvs can't direct connect if GFW block some some of it.