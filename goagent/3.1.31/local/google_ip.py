#!/usr/bin/env python
# -*- coding: utf-8 -*-
# base on checkgoogleip 'moonshawdo@gmail.com'

# Note: domain ip list is still not used now.
#  not known how to use them now.

import threading
import operator
import time

import ip_utils
import ssl_wrap
import google_ip_range
import logging



# const value:
max_check_ip_thread_num = 10
min_good_ip_num = 40
max_good_ip_num = 50
timeout = 5000 # 5 second


class Check_ip():
    ncount = 0
    ncount_lock = threading.Lock()

    ip_range_manager = google_ip_range.ip_range()
    ssl_check = ssl_wrap.ssl_check()

    ip_dict = {} # ip_str => { 'conn_time'=>?, 'domain'=>, 'server'=>?}
    domain_ip_list = {} # domain => [ip, ...]
    gws_ip_list = [] # gererate from ip_dict, sort by conn_time, when get_batch_ip
    ip_lock = threading.Lock()
    iplist_need_save = 0
    last_sort_time = 0
    last_sort_time_for_domain = {}

    def __init__(self):
        self.load_ip()

        if len(self.gws_ip_list) < min_good_ip_num:
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
                conn_time = int(str_l[3])

                #logging.info("load ip: %s time:%d domain:%s server:%s", ip_str, conn_time, domain, server)
                self.set_ip(ip_str, conn_time, domain, server)
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
                    fd.write( "%s %s %s %d\n" % (ip_str, property['domain'], property['server'], property['conn_time']) )
            self.iplist_need_save = 0
        except Exception as e:
            logging.error("save good_ip.txt fail %s", e)
        finally:
            self.ip_lock.release()

    def set_ip(self, ip_str, conn_time, domain=None, server=None):
        conn_time = int(conn_time)
        if conn_time >= timeout:
            self.remove_ip(ip_str)
            return

        self.iplist_need_save = 1
        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['conn_time'] = conn_time
                return

            else:
                if domain==None or server==None:
                    # update connect time only
                    return

                self.ip_dict[ip_str] = {'conn_time':conn_time, 'domain':domain, 'server':server}

                if domain not in self.domain_ip_list:
                    self.domain_ip_list[domain] = []
                self.domain_ip_list[domain].append(ip_str)
                if 'gws' in server:
                    self.gws_ip_list.append(ip_str)

        except Exception as e:
            logging.error("set_ip err:%s", e)
        finally:
            self.ip_lock.release()

    def remove_ip(self, ip_str):
        self.ip_lock.acquire()

        if ip_str not in self.ip_dict:
            self.ip_lock.release()
            return


        try:
            property = self.ip_dict[ip_str]
            domain = property['domain']
            server = property['server']
            del self.ip_dict[ip_str]
            self.domain_ip_list[domain].remove(ip_str)

            if 'gws' in server and ip_str in self.gws_ip_list:
                self.gws_ip_list.remove(ip_str)

        except Exception as e:
            logging.warn("remove_ip fail %s", e)
        finally:
            self.ip_lock.release()

        logging.info("remove gae ip:%s left amount:%d gws_num:%d", ip_str, len(self.ip_dict), len(self.gws_ip_list))

        if len(self.gws_ip_list) < min_good_ip_num:
            self.search_more_google_ip()

    def get_batch_ip(self, num = 1):
        self.ip_lock.acquire()
        ret_list = []
        try:
            if time.time() - self.last_sort_time > 10:
                ip_dict_conn_time = {}
                for ip_str in self.ip_dict:
                    if 'gws' not in self.ip_dict[ip_str]['server']:
                        continue
                    ip_dict_conn_time[ip_str] = self.ip_dict[ip_str]['conn_time']
                self.gws_ip_list = sorted(ip_dict_conn_time.items(), key=operator.itemgetter(1))
                self.last_sort_time = time.time()

            if len(self.gws_ip_list) == 0:
                logging.warning("no gws ip")
                return []

            i = 0
            for (ip_str, _) in self.gws_ip_list:
                ret_list.append( ip_str)
                i += 1
                if i >= num:
                    break
        except Exception as e:
            logging.error("get_batch_ip fail:%s", e)
        finally:
            self.ip_lock.release()
        return ret_list

    def get_domain_batch_ip(self, domain, num = 1):

        self.ip_lock.acquire()
        try:
            if domain not in self.last_sort_time_for_domain or time.time() - self.last_sort_time_for_domain[domain] > 10:
                ip_dict_conn_time = {}
                for ip_str in self.ip_dict:
                    if domain != self.ip_dict[ip_str]['domain']:
                        continue
                    ip_dict_conn_time[ip_str] = self.ip_dict[ip_str]['conn_time']
                self.domain_ip_list[domain] = sorted(ip_dict_conn_time.items(), key=operator.itemgetter(1))
                self.last_sort_time_for_domain[domain] = time.time()

            if domain not in self.domain_ip_list or len(self.domain_ip_list[domain]) == 0:
                ret_list = []
                logging.warn("no domain ip for %s", domain)
                return []

            i = 0
            ret_list = []
            for (ip_str, _) in self.domain_ip_list[domain]:
                ret_list.append( ip_str)
                i += 1
                if i >= num:
                    break
        except Exception as e:
            logging.warn("get_domain_batch_ip %s fail:%s", domain, e)
        finally:
            self.ip_lock.release()
        return ret_list

    def runJob(self):
        while len(self.gws_ip_list) < max_good_ip_num:
            try:
                time.sleep(1)
                ip_int = self.ip_range_manager.get_ip()
                ip_str = ip_utils.ip_num_to_string(ip_int)

                (domain, conn_time, timeout, server) = self.ssl_check.get_ssl_domain(ip_str)
                if timeout == 1 or domain == None:
                    continue
                server = server.replace(" ", "_")
                if server == '':
                    server = '_'
                if not "gws" in server:
                    continue

                logging.info("add ip:%s domain:%s server:%s conn_time:%d", ip_str, domain, server, conn_time)
                self.set_ip(ip_str, conn_time, domain, server)
                self.save_ip_list()
            except Exception as e:
                logging.warn("google_ip.runJum fail:%s", e)

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
            (domain, conn_time, timeout, server) = self.ssl_check.get_ssl_domain(ip_str)
            if timeout == 1 or domain == None:
                self.remove_ip(ip_str)
            else:
                self.set_ip(ip_str, conn_time)
            self.save_ip_list()


def test():
    check = Check_ip()
    check.search_more_google_ip()
    #check.test_ip("74.125.130.98", print_result=True)
    while True:
        time.sleep(10)

if __name__ == '__main__':
    test()

# test cast
# 1. good_ip.txt not exist when startup, auto scan good ip, then save
# 2. good_ip.txt exist, load ip list, and check it.
# 3. get_batch_ip(num)
# 4. set_ip(ip, conn_time), try remove ip
