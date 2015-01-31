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
import math

# const value:
max_check_ip_thread_num = 30
min_good_ip_num = 100
max_good_ip_num = 1000
timeout = 5000 # 5 second


class Check_ip():
    ncount = 0
    ncount_lock = threading.Lock()

    to_remove_ip_list = Queue.Queue()
    remove_ip_thread_num = 0
    remove_ip_thread_lock = threading.Lock()

    ip_dict = {} # ip_str => { 'handshake_time'=>?, 'domain'=>, 'server'=>?, 'timeout'=>}
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
        with open("good_ip.txt", "r") as fd:
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

                logging.info("load ip: %s time:%d domain:%s server:%s", ip_str, handshake_time, domain, server)
                self.add_ip(ip_str, handshake_time, domain, server)
                #logging.debug("load_ip ip:%s time:%d", ip_str, handshake_time)
            except Exception as e:
                logging.warn("load_ip line:%s err:%s", line, e)

        logging.info("load google iplist num: %d, gws num:%d", len(self.ip_dict), len(self.gws_ip_list))
        self.try_sort_ip_by_handshake_time(force=True)

        p = threading.Thread(target = self.check_exist_ip)
        p.daemon = True
        p.start()

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


            #self._clean_bad_ip_if_we_have_too_many_ips
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

            while True:
                fastest_num = min(ip_num-1, 40)
                #index = random.randint(0, fastest_num)
                index = get_random_pr(fastest_num)
                ip_str = self.gws_ip_list[index]
                handshake_time = self.ip_dict[ip_str]["handshake_time"]
                fail_time = self.ip_dict[ip_str]["fail_time"]
                if time.time() - fail_time < 10:
                    continue

                logging.debug("get ip:%s t:%d", ip_str, handshake_time)
                return ip_str
        except Exception as e:
            logging.error("get_gws_ip fail:%s", e)
        finally:
            self.ip_lock.release()

    def add_ip(self, ip_str, handshake_time, domain=None, server=None):
        if not isinstance(ip_str, basestring):
            logging.error("add_ip input")

        handshake_time = int(handshake_time)
        if handshake_time >= timeout:
            return False

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['handshake_time'] = handshake_time
                self.ip_dict[ip_str]['timeout'] = 0
                #logging.debug("add ip:%s duplicated", ip_str)
                return False

            self.iplist_need_save = 1
            self.ip_dict[ip_str] = {'handshake_time':handshake_time, 'domain':domain, 'server':server, 'timeout':0, "history":"%d,"% handshake_time, "fail_time":0}

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

                # Case: some good ip, normal handshake time is 300ms
                # some time ip lost cause handshake time become 2000ms
                # this ip will no return back to first good ip list until all become bad
                # There for, prevent handshake time increase too quickly.
                org_time = self.ip_dict[ip_str]['handshake_time']
                if handshake_time - org_time > 200:
                    self.ip_dict[ip_str]['handshake_time'] = org_time + 200
                else:
                    self.ip_dict[ip_str]['handshake_time'] = handshake_time

                self.ip_dict[ip_str]['timeout'] = 0
                #self.ip_dict[ip_str]['history'] += "%d," % handshake_time
                self.ip_dict[ip_str]["fail_time"] = 0
                return

            #logging.debug("update ip:%s not exist", ip_str)
        except Exception as e:
            logging.error("update_ip err:%s", e)
        finally:
            self.ip_lock.release()


    def report_connect_fail(self, ip_str, force_remove=False):
        if not isinstance(ip_str, basestring):
            logging.error("set_ip input")

        if time.time() - self.network_fail_time < 3:
            return

        ip_removed = False
        self.ip_lock.acquire()
        try:
            if not ip_str in self.ip_dict:
                return

            fail_time = self.ip_dict[ip_str]["fail_time"]
            if time.time() - fail_time < 1:
                return

            # increase handshake_time to make it can be used in lower probability
            self.ip_dict[ip_str]['handshake_time'] += 200
            self.ip_dict[ip_str]['timeout'] += 1
            #self.ip_dict[ip_str]['history'] += "fail,"
            self.ip_dict[ip_str]["fail_time"] = time.time()

            if force_remove or self.ip_dict[ip_str]['timeout'] >= 5:
                ip_removed = True
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

        if ip_removed or True:
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

    def remove_ip_process(self):
        try:
            while True:
                if not self.network_is_ok():
                    logging.warn("network is unreachable. check your network connection.")
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

            #self.check_exist_ip()
        finally:
            self.remove_ip_thread_lock.acquire()
            self.remove_ip_thread_num -= 1
            self.remove_ip_thread_lock.release()

    def network_is_ok(self):
        if time.time() - self.network_fail_time < 3:
            return False

        try:
            conn = httplib.HTTPSConnection("github.com", 443)
            header = {"user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
                      "accept":"application/json, text/javascript, */*; q=0.01",
                      "accept-encoding":"gzip, deflate, sdch",
                      "accept-language":'en-US,en;q=0.8,ja;q=0.6,zh-CN;q=0.4,zh;q=0.2',
                      "connection":"keep-alive"
                      }
            conn.request("HEAD", "/", headers=header)
            response = conn.getresponse()
            if response.status:
                return True
        except:
            pass

        self.network_fail_time = time.time()
        return False

    def _clean_bad_ip_if_we_have_too_many_ips(self):
        ip_num = len(self.gws_ip_list)
        if ip_num < max_good_ip_num:
            return

        for i in range(ip_num-1, min_good_ip_num, -1):
            ip = self.gws_ip_list[i]
            property = self.ip_dict[ip]

            if property['handshake_time'] < 600:
                return

            server = property['server']
            del self.ip_dict[ip]

            if 'gws' in server:
                self.gws_ip_list.remove(ip)



    def check_ip(self, ip_str):
        result = check_ip.test_gws(ip_str)
        if not result:
            return False

        if self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type):
            #logging.info("add  %s  CN:%s  type:%s  time:%d  gws:%d ", ip_str,
            #     result.domain, result.server_type, result.handshake_time, len(self.gws_ip_list))
            logging.info("check_ip add ip:%s time:%d", ip_str, result.handshake_time)

        return True

    def runJob(self):
        while True:# not self.is_ip_enough():
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
        if not self.network_is_ok():
            logging.warn("check_exist_ip network is fail, check your network connection.")
            return

        self.ip_lock.acquire()
        tmp_ip_list = [x for x in self.gws_ip_list]
        self.ip_lock.release()

        for ip_str in tmp_ip_list:

            result = check_ip.test_gws(ip_str)
            if not result:
                logging.info("check_exist_ip fail ip:%s ", ip_str)
                self.report_connect_fail(ip_str, force_remove=True)
            else:
                self.update_ip(ip_str, result.handshake_time)
                logging.info("check_exist_ip update ip:%s server:%s time:%d", ip_str, result.server_type, result.handshake_time)

        self.save_ip_list()

if __name__ != "__main__":
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

def test_network():
    check = Check_ip()
    res = check.network_is_ok()
    print res

def get_random_pr(num):
    n0 = num
    r = 2

    for i in range(r):
        n0 = n0 * n0

    n1 = random.randint(0, n0)
    for i in range(r):
        n1 = math.sqrt(n1)

    n2 = num - n1
    return int(n2 )

def test_random():
    result = {}
    for i in range(300):
        v = get_random_pr(30)
        if not v in result:
            result[v] = 0
        result[v] += 1
    for k in result:
        print k, result[k]

if __name__ == '__main__':
    test_random()
# test cast
# 1. good_ip.txt not exist when startup, auto scan good ip, then save
# 2. good_ip.txt exist, load ip list, and check it.
#


# google ip study about gvs
# each xx.googlevideo.com only have one ip
# and there is many many googlevideo ip and many many xx.googlevideo.com domain
# if GFW block some of the ip, direct connect to these domain if fail.
# There for, gvs can't direct connect if GFW block some some of it.