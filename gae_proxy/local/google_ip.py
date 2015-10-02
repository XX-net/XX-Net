#!/usr/bin/env python
# -*- coding: utf-8 -*-
# based on checkgoogleip 'moonshawdo@gmail.com'

import threading
import operator
import time
import Queue
import os, sys
import traceback

current_path = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform == "linux" or sys.platform == "linux2":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(win32_lib)

import ip_utils
import check_ip
from google_ip_range import ip_range
import xlog
from config import config
import connect_control
from scan_ip_log import scan_ip_log


class Check_ip():
    searching_thread_count = 0
    ncount_lock = threading.Lock()

    to_remove_ip_list = Queue.Queue()
    remove_ip_thread_num = 0
    remove_ip_thread_num_lock = threading.Lock()

    ip_dict = {} # ip_str => {
                 # 'handshake_time'=>?ms,
                 # 'fail_times' => N   continue timeout num, if connect success, reset to 0
                 # 'fail_time' => time.time(),  last fail time, next time retry will need more time.
                 # 'transfered_data' => X bytes
                 # 'data_active' => transfered_data - n second, for select
                 # 'get_time' => ip used time.
                 # 'success_time' => last connect success time.
                 # 'domain'=>CN,
                 # 'server'=>gws/gvs?,
                 # history=>[[time,status], []]
                 # }

    gws_ip_list = [] # gererate from ip_dict, sort by handshake_time, when get_batch_ip
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


    def __init__(self):
        self.load_config()
        self.load_ip()

        self.search_more_google_ip()

    def is_ip_enough(self):
        if len(self.gws_ip_list) >= self.max_good_ip_num:
            return True
        else:
            return False

    def load_config(self):
        if config.USE_IPV6:
            good_ip_file_name = "good_ipv6.txt"
            default_good_ip_file_name = "good_ipv6.txt"
        else:
            good_ip_file_name = "good_ip.txt"
            default_good_ip_file_name = "good_ip.txt"

        self.good_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, good_ip_file_name))
        self.default_good_ip_file = os.path.join(current_path, default_good_ip_file_name)

        self.auto_adjust_scan_ip_thread_num = config.CONFIG.getint("google_ip", "auto_adjust_scan_ip_thread_num")
        self.max_scan_ip_thread_num = config.CONFIG.getint("google_ip", "max_scan_ip_thread_num") #50
        self.scan_ip_thread_num = self.max_scan_ip_thread_num
        self.max_good_ip_num = config.CONFIG.getint("google_ip", "max_good_ip_num") #3000  # stop scan ip when enough
        self.ip_connect_interval = config.CONFIG.getint("google_ip", "ip_connect_interval") #5,10

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
                if len(str_l) < 4:
                    xlog.warning("line err: %s", line)
                    continue
                ip_str = str_l[0]
                domain = str_l[1]
                server = str_l[2]
                handshake_time = int(str_l[3])
                if len(str_l) > 4:
                    fail_times = int(str_l[4])
                else:
                    fail_times = 0

                #logging.info("load ip: %s time:%d domain:%s server:%s", ip_str, handshake_time, domain, server)
                self.add_ip(ip_str, handshake_time, domain, server, fail_times)
            except Exception as e:
                xlog.exception("load_ip line:%s err:%s", line, e)

        xlog.info("load google ip_list num:%d, gws num:%d", len(self.ip_dict), len(self.gws_ip_list))
        self.try_sort_gws_ip(force=True)

    def save_ip_list(self, force=False):
        if not force:
            if self.iplist_need_save == 0:
                return
            if time.time() - self.iplist_saved_time < 10:
                return

        self.iplist_saved_time = time.time()

        try:
            self.ip_lock.acquire()
            ip_dict = sorted(self.ip_dict.items(),  key=lambda x: x[1]['handshake_time'])
            with open(self.good_ip_file, "w") as fd:
                for ip_str, property in ip_dict:
                    fd.write( "%s %s %s %d %d\n" %
                        (ip_str, property['domain'], property['server'], property['handshake_time'], property['fail_times']) )

            self.iplist_need_save = 0
        except Exception as e:
            xlog.error("save good_ip.txt fail %s", e)
        finally:
            self.ip_lock.release()

    def try_sort_gws_ip(self, force=False):
        if time.time() - self.last_sort_time_for_gws < 10 and not force:
            return
        self.last_sort_time_for_gws = time.time()

        self.ip_lock.acquire()
        try:
            ip_rate = {}
            for ip_str in self.ip_dict:
                if 'gws' not in self.ip_dict[ip_str]['server']:
                    continue
                ip_rate[ip_str] = self.ip_dict[ip_str]['handshake_time']

            ip_time = sorted(ip_rate.items(), key=operator.itemgetter(1))
            self.gws_ip_list = [ip_str for ip_str,rate in ip_time]

        except Exception as e:
            xlog.error("try_sort_ip_by_handshake_time:%s", e)
        finally:
            self.ip_lock.release()

        time_cost = (( time.time() - self.last_sort_time_for_gws) * 1000)
        if time_cost > 30:
            xlog.debug("sort ip time:%dms", time_cost) # 5ms for 1000 ip. 70~150ms for 30000 ip.

        self.adjust_scan_thread_num()

    def adjust_scan_thread_num(self):
        if not self.auto_adjust_scan_ip_thread_num:
            scan_ip_thread_num = self.max_scan_ip_thread_num
        elif len(self.gws_ip_list) < 100:
            scan_ip_thread_num = self.max_scan_ip_thread_num
        else:
            try:
                the_100th_ip = self.gws_ip_list[99]
                the_100th_handshake_time = self.ip_dict[the_100th_ip]['handshake_time']
                scan_ip_thread_num = int( (the_100th_handshake_time - 200)/2 * self.max_scan_ip_thread_num/50 )
            except Exception as e:
                xlog.warn("adjust_scan_thread_num fail:%r", e)
                return

            if scan_ip_thread_num > self.max_scan_ip_thread_num:
                scan_ip_thread_num = self.max_scan_ip_thread_num

        if scan_ip_thread_num != self.scan_ip_thread_num:
            xlog.info("Adjust scan thread num from %d to %d", self.scan_ip_thread_num, scan_ip_thread_num)
            self.scan_ip_thread_num = scan_ip_thread_num
            self.search_more_google_ip()

    def ip_handshake_th(self, num):
        try:
            iplist_length = len(self.gws_ip_list)
            ip_index = iplist_length if iplist_length < num else num
            last_ip = self.gws_ip_list[ip_index]
            handshake_time = self.ip_dict[last_ip]['handshake_time']
            return handshake_time
        except:
            return -1

    def get_gws_ip(self):
        self.try_sort_gws_ip()

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            if ip_num == 0:
                #logging.warning("no gws ip")
                time.sleep(10)
                return None

            for i in range(ip_num):

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
                get_time = self.ip_dict[ip_str]["get_time"]
                if time.time() - get_time < self.ip_connect_interval:
                    self.gws_ip_pointer += 1
                    continue

                if time.time() - self.ip_dict[ip_str]['success_time'] > 300: # 5 min
                    fail_connect_interval = 1800 # 30 min
                else:
                    fail_connect_interval = 120 # 2 min
                fail_time = self.ip_dict[ip_str]["fail_time"]
                if time.time() - fail_time < fail_connect_interval:
                    self.gws_ip_pointer += 1
                    continue

                time_now = time.time()
                active_time = self.ip_dict[ip_str]['data_active']
                transfered_data = self.ip_dict[ip_str]['transfered_data'] - ((time_now - active_time) * config.ip_traffic_quota)
                if transfered_data > config.ip_traffic_quota_base:
                    self.gws_ip_pointer += 1
                    continue

                handshake_time = self.ip_dict[ip_str]["handshake_time"]
                xlog.debug("get ip:%s t:%d", ip_str, handshake_time)
                self.ip_dict[ip_str]['history'].append([time.time(), "get"])
                self.ip_dict[ip_str]['get_time'] = time.time()
                self.gws_ip_pointer += 1
                return ip_str
        except Exception as e:
            xlog.error("get_gws_ip fail:%s", e)
            traceback.print_exc()
        finally:
            self.ip_lock.release()

    def get_host_ip(self, host):
        self.try_sort_gws_ip()

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

                xlog.debug("get host:%s ip:%s t:%d", host, ip_str, handshake_time)
                self.ip_dict[ip_str]['history'].append([time.time(), "get"])
                self.ip_dict[ip_str]['get_time'] = time.time()
                return ip_str
        except Exception as e:
            xlog.error("get_gws_ip fail:%s", e)
            traceback.print_exc()
        finally:
            self.ip_lock.release()

    def add_ip(self, ip_str, handshake_time, domain=None, server='', fail_times=0):
        if not isinstance(ip_str, basestring):
            xlog.error("add_ip input")

        handshake_time = int(handshake_time)

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                self.ip_dict[ip_str]['handshake_time'] = handshake_time
                self.ip_dict[ip_str]['fail_times'] = fail_times
                self.ip_dict[ip_str]['fail_time'] = 0
                self.ip_dict[ip_str]['history'].append([time.time(), handshake_time])
                return False

            self.iplist_need_save = 1

            self.ip_dict[ip_str] = {'handshake_time':handshake_time, "fail_times":fail_times,
                                    "transfered_data":0, 'data_active':0,
                                    'domain':domain, 'server':server,
                                    "history":[[time.time(), handshake_time]], "fail_time":0,
                                    "success_time":0, "get_time":0}

            if 'gws' in server:
                self.gws_ip_list.append(ip_str)
            return True
        except Exception as e:
            xlog.exception("add_ip err:%s", e)
        finally:
            self.ip_lock.release()
        return False

    def update_ip(self, ip_str, handshake_time):
        if not isinstance(ip_str, basestring):
            xlog.error("set_ip input")

        handshake_time = int(handshake_time)
        if handshake_time < 5: # that's impossible
            xlog.warn("%s handshake:%d impossible", ip_str, 1000 * handshake_time)
            return

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:

                # Case: some good ip, average handshake time is 300ms
                # some times ip package lost cause handshake time become 2000ms
                # this ip will not return back to good ip front until all become bad
                # There for, prevent handshake time increase too quickly.
                org_time = self.ip_dict[ip_str]['handshake_time']
                if handshake_time - org_time > 500:
                    self.ip_dict[ip_str]['handshake_time'] = org_time + 500
                else:
                    self.ip_dict[ip_str]['handshake_time'] = handshake_time

                self.ip_dict[ip_str]['success_time'] = time.time()
                self.ip_dict[ip_str]['fail_times'] = 0
                self.ip_dict[ip_str]['history'].append([time.time(), handshake_time])
                self.ip_dict[ip_str]["fail_time"] = 0
                self.iplist_need_save = 1

            #logging.debug("update ip:%s not exist", ip_str)
        except Exception as e:
            xlog.error("update_ip err:%s", e)
        finally:
            self.ip_lock.release()

        self.save_ip_list()

    def is_traffic_quota_allow(self, ip_str):
        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                transfered_data = self.ip_dict[ip_str]['transfered_data']
                if transfered_data == 0:
                    return True

                active_time = self.ip_dict[ip_str]['data_active']
                transfered_data = transfered_data - ((time.time() - active_time) * config.ip_traffic_quota)
                if transfered_data <= 0:
                    self.ip_dict[ip_str]['transfered_data'] = 0
                if transfered_data < config.ip_traffic_quota_base:
                    return True
        except Exception as e:
            xlog.exception("is_traffic_quota_exceed err:%s", e)
        finally:
            self.ip_lock.release()
        return False

    def report_ip_traffic(self, ip_str, bytes):
        if bytes == 0:
            return

        self.ip_lock.acquire()
        try:
            if ip_str in self.ip_dict:
                time_now = time.time()

                active_time = self.ip_dict[ip_str]['data_active']
                transfered_data = self.ip_dict[ip_str]['transfered_data'] - ((time_now - active_time) * config.ip_traffic_quota)
                if transfered_data < 0:
                    transfered_data = 0

                transfered_data += bytes
                self.ip_dict[ip_str]['transfered_data'] = transfered_data
                self.ip_dict[ip_str]['data_active'] = time_now
                self.ip_dict[ip_str]['history'].append([time.time(), "%d_B" % bytes])
        except Exception as e:
            xlog.error("report_ip_trafic err:%s", e)
        finally:
            self.ip_lock.release()

    def report_connect_fail(self, ip_str, force_remove=False):
        # ignore if system network is disconnected.
        if not force_remove:
            if not check_ip.network_is_ok():
                xlog.debug("report_connect_fail network fail")
                #connect_control.fall_into_honeypot()
                return

        self.ip_lock.acquire()
        try:
            if not ip_str in self.ip_dict:
                return

            fail_time = self.ip_dict[ip_str]["fail_time"]
            if not force_remove and time.time() - fail_time < 1:
                xlog.debug("fail time too near")
                return

            # increase handshake_time to make it can be used in lower probability
            self.ip_dict[ip_str]['handshake_time'] += 300
            self.ip_dict[ip_str]['fail_times'] += 1
            self.ip_dict[ip_str]['history'].append([time.time(), "fail"])
            self.ip_dict[ip_str]["fail_time"] = time.time()

            if force_remove or self.ip_dict[ip_str]['fail_times'] >= 50:
                property = self.ip_dict[ip_str]
                server = property['server']
                del self.ip_dict[ip_str]

                if 'gws' in server and ip_str in self.gws_ip_list:
                    self.gws_ip_list.remove(ip_str)

                xlog.info("remove ip:%s left amount:%d gws_num:%d", ip_str, len(self.ip_dict), len(self.gws_ip_list))

                if not force_remove:
                    self.to_remove_ip_list.put(ip_str)
                    self.try_remove_thread()

            self.iplist_need_save = 1
        except Exception as e:
            xlog.exception("set_ip err:%s", e)
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
        p.start()

    def remove_ip_process(self):
        try:
            while connect_control.keep_running:

                try:
                    ip_str = self.to_remove_ip_list.get_nowait()
                except:
                    break

                result = check_ip.test(ip_str)
                if result and result.appspot_ok:
                    self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type)
                    xlog.debug("remove ip process, restore ip:%s", ip_str)
                    continue

                if not check_ip.network_is_ok():
                    self.to_remove_ip_list.put(ip_str)
                    xlog.warn("network is unreachable. check your network connection.")
                    return

                xlog.info("real remove ip:%s ", ip_str)
                self.iplist_need_save = 1
        finally:
            self.remove_ip_thread_num_lock.acquire()
            self.remove_ip_thread_num -= 1
            self.remove_ip_thread_num_lock.release()

    def remove_slowest_ip(self):
        if len(self.gws_ip_list) <= self.max_good_ip_num:
            return

        self.try_sort_gws_ip(force=True)

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            while ip_num > self.max_good_ip_num:

                ip_str = self.gws_ip_list[ip_num - 1]

                property = self.ip_dict[ip_str]
                server = property['server']
                handshake_time = property['handshake_time']
                xlog.info("remove_slowest_ip:%s handshake_time:%d", ip_str, handshake_time)
                del self.ip_dict[ip_str]

                if 'gws' in server and ip_str in self.gws_ip_list:
                    self.gws_ip_list.remove(ip_str)

                ip_num -= 1

        except Exception as e:
            xlog.exception("remove_slowest_ip err:%s", e)
        finally:
            self.ip_lock.release()

    def scan_ip_worker(self):
        while self.searching_thread_count <= self.scan_ip_thread_num and connect_control.keep_running:
            if not connect_control.allow_scan():
                time.sleep(10)
                continue

            try:
                time.sleep(1)
                ip_int = ip_range.get_ip()
                ip_str = ip_utils.ip_num_to_string(ip_int)

                if ip_str in self.ip_dict:
                    continue

                connect_control.start_connect_register()
                result = check_ip.test_gae(ip_str)
                connect_control.end_connect_register()
                if not result:
                    continue

                if self.add_ip(ip_str, result.handshake_time, result.domain, result.server_type):
                    #logging.info("add  %s  CN:%s  type:%s  time:%d  gws:%d ", ip_str,
                    #     result.domain, result.server_type, result.handshake_time, len(self.gws_ip_list))
                    xlog.info("scan_ip add ip:%s time:%d", ip_str, result.handshake_time)
                    scan_ip_log.info("Add %s time:%d CN:%s type:%s", ip_str, result.handshake_time, result.domain, result.server_type)
                    self.remove_slowest_ip()
                    self.save_ip_list()
            except Exception as e:
                xlog.exception("google_ip.runJob fail:%s", e)

        self.ncount_lock.acquire()
        self.searching_thread_count -= 1
        self.ncount_lock.release()
        xlog.info("scan_ip_worker exit")

    def search_more_google_ip(self):
        if config.USE_IPV6:
            return

        new_thread_num = self.scan_ip_thread_num - self.searching_thread_count
        if new_thread_num < 1:
            return

        for i in range(0, new_thread_num):
            self.ncount_lock.acquire()
            self.searching_thread_count += 1
            self.ncount_lock.release()

            p = threading.Thread(target = self.scan_ip_worker)
            p.start()

    def update_scan_thread_num(self, num):
        self.max_scan_ip_thread_num = num
        self.adjust_scan_thread_num()

def test():
    google_ip.search_more_google_ip()
    #check.test_ip("74.125.130.98", print_result=True)
    while not google_ip.is_ip_enough():
        time.sleep(10)

google_ip = Check_ip()
if __name__ == '__main__':
    google_ip.save_ip_list(force=True)
