#!/usr/bin/env python
# -*- coding: utf-8 -*-
# based on checkgoogleip 'moonshawdo@gmail.com'


import threading
import operator
import time
import Queue
import os, sys

current_path = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))

    noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
    sys.path.append(noarch_lib)

    if sys.platform == "win32":
        win32_lib = os.path.abspath( os.path.join(python_path, 'lib', 'win32'))
        sys.path.append(win32_lib)
    elif sys.platform.startswith("linux"):
        linux_lib = os.path.abspath( os.path.join(python_path, 'lib', 'linux'))
        sys.path.append(linux_lib)

import check_local_network
import check_ip
import google_ip_range

from xlog import getLogger
xlog = getLogger("gae_proxy")

from config import config
import connect_control
from scan_ip_log import scan_ip_log


######################################
# about ip connect time and handshake time
# handshake time is double of connect time in common case.
# after connect and handshaked, http get time is like connect time
#
# connect time is zero if you use socks proxy.
#
# most case, connect time is 300ms - 600ms.
# good case is 60ms
# bad case is 1300ms and more.

class IpManager():
    # Functions:
    # 1. Scan ip in back ground
    # 2. sort ip by RTT and fail times
    #     RTT + fail_times * 1000
    # 3. count ip connection number
    #    keep max one link every ip.
    #    more link may be block by GFW if large traffic on some ip.
    # 4. scan all exist ip
    #    stop scan ip thread then start 10 threads to scan all exist ip.
    #    called by web_control.

    def __init__(self):
        self.scan_thread_lock = threading.Lock()
        self.ip_lock = threading.Lock()
        self.ip_range = google_ip_range.ip_range
        self.reset()

        self.check_ip_thread = threading.Thread(target=self.check_ip_process)
        self.check_ip_thread.daemon = True
        self.check_ip_thread.start()

    def reset(self):
        self.ip_lock.acquire()
        self.gws_ip_pointer = 0
        self.gws_ip_pointer_reset_time = 0
        self.scan_thread_count = 0
        self.iplist_need_save = False
        self.iplist_saved_time = 0
        self.last_sort_time_for_gws = 0 # keep status for avoid wast too many cpu
        self.good_ip_num = 0 # only success ip num

        # ip => {
                 # 'handshake_time'=>?ms,
                 # 'links' => current link number, limit max to 1
                 # 'fail_times' => N   continue timeout num, if connect success, reset to 0
                 # 'fail_time' => time.time(),  last fail time, next time retry will need more time.
                 # 'transfered_data' => X bytes
                 # 'down_fail' => times of fails when download content data
                 # 'down_fail_time'
                 # 'data_active' => transfered_data - n second, for select
                 # 'get_time' => ip used time.
                 # 'success_time' => last connect success time.
                 # 'domain'=>CN,
                 # 'server'=>gws/gvs?,
                 # history=>[[time,status], []]
                 # }
        self.ip_dict = {}

        # gererate from ip_dict, sort by handshake_time, when get_batch_ip
        self.gws_ip_list = []
        self.to_check_ip_queue = Queue.Queue()
        self.scan_exist_ip_queue = Queue.Queue()
        self.ip_lock.release()

        self.load_config()
        self.load_ip()

        #if check_local_network.network_stat == "OK" and not config.USE_IPV6:
        #    self.start_scan_all_exist_ip()
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
            self.max_scan_ip_thread_num = 0
            self.auto_adjust_scan_ip_thread_num = 0
        else:
            good_ip_file_name = "good_ip.txt"
            default_good_ip_file_name = "good_ip.txt"
            self.max_scan_ip_thread_num = config.CONFIG.getint("google_ip", "max_scan_ip_thread_num") #50
            self.auto_adjust_scan_ip_thread_num = config.CONFIG.getint("google_ip", "auto_adjust_scan_ip_thread_num")

        self.good_ip_file = os.path.abspath( os.path.join(config.DATA_PATH, good_ip_file_name))
        self.default_good_ip_file = os.path.join(current_path, default_good_ip_file_name)

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
                if line.startswith("#"):
                    continue

                str_l = line.split(' ')

                if len(str_l) < 4:
                    xlog.warning("line err: %s", line)
                    continue
                ip = str_l[0]
                domain = str_l[1]
                server = str_l[2]
                handshake_time = int(str_l[3])
                if len(str_l) > 4:
                    fail_times = int(str_l[4])
                else:
                    fail_times = 0

                if len(str_l) > 5:
                    down_fail = int(str_l[5])
                else:
                    down_fail = 0

                #xlog.info("load ip: %s time:%d domain:%s server:%s", ip, handshake_time, domain, server)
                self.add_ip(ip, handshake_time, domain, server, fail_times, down_fail)
            except Exception as e:
                xlog.exception("load_ip line:%s err:%s", line, e)

        xlog.info("load google ip_list num:%d, gws num:%d", len(self.ip_dict), len(self.gws_ip_list))
        self.try_sort_gws_ip(force=True)

    def save_ip_list(self, force=False):
        if not force:
            if not self.iplist_need_save:
                return
            if time.time() - self.iplist_saved_time < 10:
                return

        self.iplist_saved_time = time.time()

        try:
            self.ip_lock.acquire()
            ip_dict = sorted(self.ip_dict.items(),  key=lambda x: (x[1]['handshake_time'] + x[1]['fail_times'] * 1000))
            with open(self.good_ip_file, "w") as fd:
                for ip, property in ip_dict:
                    fd.write( "%s %s %s %d %d %d\n" %
                        (ip, property['domain'],
                            property['server'],
                            property['handshake_time'],
                            property['fail_times'],
                            property['down_fail']) )
                fd.flush()

            self.iplist_need_save = False
        except Exception as e:
            xlog.error("save good_ip.txt fail %s", e)
        finally:
            self.ip_lock.release()

    def _ip_rate(self, ip_info):
        return ip_info['handshake_time'] + \
                    (ip_info['fail_times'] * 1000 ) + \
                    (ip_info['down_fail'] * 500 )

    def try_sort_gws_ip(self, force=False):
        if time.time() - self.last_sort_time_for_gws < 10 and not force:
            return

        self.ip_lock.acquire()
        self.last_sort_time_for_gws = time.time()
        try:
            self.good_ip_num = 0
            ip_rate = {}
            for ip in self.ip_dict:
                if 'gws' not in self.ip_dict[ip]['server']:
                    continue
                ip_rate[ip] = self._ip_rate(self.ip_dict[ip])
                if self.ip_dict[ip]['fail_times'] == 0:
                    self.good_ip_num += 1

            ip_time = sorted(ip_rate.items(), key=operator.itemgetter(1))
            self.gws_ip_list = [ip for ip,rate in ip_time]

        except Exception as e:
            xlog.error("try_sort_ip_by_handshake_time:%s", e)
        finally:
            self.ip_lock.release()

        time_cost = (( time.time() - self.last_sort_time_for_gws) * 1000)
        if time_cost > 30:
            xlog.debug("sort ip time:%dms", time_cost) # 5ms for 1000 ip. 70~150ms for 30000 ip.

        self.adjust_scan_thread_num()

    def adjust_scan_thread_num(self, max_scan_ip_thread_num=None):
        if max_scan_ip_thread_num!=None:
            self.max_scan_ip_thread_num = max_scan_ip_thread_num

        if not self.auto_adjust_scan_ip_thread_num:
            scan_ip_thread_num = self.max_scan_ip_thread_num
        elif len(self.gws_ip_list) < 100:
            scan_ip_thread_num = self.max_scan_ip_thread_num
        else:
            try:
                the_100th_ip = self.gws_ip_list[99]
                the_100th_handshake_time = self._ip_rate(self.ip_dict[the_100th_ip])
                scan_ip_thread_num = int( (the_100th_handshake_time - 200)/2 * self.max_scan_ip_thread_num/50 )
            except Exception as e:
                xlog.warn("adjust_scan_thread_num fail:%r", e)
                return

            if scan_ip_thread_num > self.max_scan_ip_thread_num:
                scan_ip_thread_num = self.max_scan_ip_thread_num
            elif scan_ip_thread_num < 0:
                scan_ip_thread_num = 0

        if scan_ip_thread_num != self.scan_ip_thread_num:
            xlog.info("Adjust scan thread num from %d to %d", self.scan_ip_thread_num, scan_ip_thread_num)
            self.scan_ip_thread_num = scan_ip_thread_num
            self.search_more_google_ip()

    def ip_quality(self, num=10):
        try:
            iplist_length = len(self.gws_ip_list)
            ip_th = min(num, iplist_length)
            for i in range(ip_th, 0, -1):
                last_ip = self.gws_ip_list[i]
                if self.ip_dict[last_ip]['fail_times'] > 0:
                    continue
                handshake_time = self.ip_dict[last_ip]['handshake_time']
                return handshake_time

            return 9999
        except:
            return 9999

    def append_ip_history(self, ip, info):
        if config.record_ip_history:
            self.ip_dict[ip]['history'].append([time.time(), info])

    # algorithm to get ip:
    # scan start from fastest ip
    # always use the fastest ip.
    # if the ip is used in 5 seconds, try next ip;
    # if the ip is fail in 60 seconds, try next ip;
    # reset pointer to front every 3 seconds
    def get_gws_ip(self):
        self.try_sort_gws_ip()

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            if ip_num == 0:
                #xlog.warning("no gws ip")
                #time.sleep(10)
                return None

            for i in range(ip_num):
                time_now = time.time()
                if self.gws_ip_pointer >= ip_num:
                    if time_now - self.gws_ip_pointer_reset_time < 1:
                        time.sleep(1)
                        continue
                    else:
                        self.gws_ip_pointer = 0
                        self.gws_ip_pointer_reset_time = time_now
                elif self.gws_ip_pointer > 0 and time_now - self.gws_ip_pointer_reset_time > 3:
                    self.gws_ip_pointer = 0
                    self.gws_ip_pointer_reset_time = time_now

                ip = self.gws_ip_list[self.gws_ip_pointer]
                get_time = self.ip_dict[ip]["get_time"]
                if time_now - get_time < self.ip_connect_interval:
                    self.gws_ip_pointer += 1
                    continue

                if time_now - self.ip_dict[ip]['success_time'] > 300: # 5 min
                    fail_connect_interval = 1800 # 30 min
                else:
                    fail_connect_interval = 120 # 2 min
                fail_time = self.ip_dict[ip]["fail_time"]
                if time_now - fail_time < fail_connect_interval:
                    self.gws_ip_pointer += 1
                    continue

                down_fail_connect_interval = 600
                down_fail_time = self.ip_dict[ip]["down_fail_time"]
                if time_now - down_fail_time < down_fail_connect_interval:
                    self.gws_ip_pointer += 1
                    continue

                if self.ip_dict[ip]['links'] >= config.max_links_per_ip:
                    self.gws_ip_pointer += 1
                    continue

                handshake_time = self.ip_dict[ip]["handshake_time"]
                xlog.debug("get ip:%s t:%d", ip, handshake_time)
                self.append_ip_history(ip, "get")
                self.ip_dict[ip]['get_time'] = time_now
                self.ip_dict[ip]['links'] += 1
                self.gws_ip_pointer += 1
                return ip
        except Exception as e:
            xlog.exception("get_gws_ip fail:%r", e)
        finally:
            self.ip_lock.release()

    def add_ip(self, ip, handshake_time, domain=None, server='', fail_times=0, down_fail=0):
        if not isinstance(ip, basestring):
            xlog.error("add_ip input")
            return

        if config.USE_IPV6 and ":" not in ip:
            xlog.warn("add %s but ipv6", ip)
            return

        handshake_time = int(handshake_time)

        self.ip_lock.acquire()
        try:
            if ip in self.ip_dict:
                self.ip_dict[ip]['handshake_time'] = handshake_time
                self.ip_dict[ip]['fail_times'] = fail_times
                if self.ip_dict[ip]['fail_time'] > 0:
                    self.ip_dict[ip]['fail_time'] = 0
                    self.good_ip_num += 1
                self.append_ip_history(ip, handshake_time)
                return False

            self.iplist_need_save = True
            self.good_ip_num += 1

            self.ip_dict[ip] = {'handshake_time':handshake_time, "fail_times":fail_times,
                                    "transfered_data":0, 'data_active':0,
                                    'domain':domain, 'server':server,
                                    "history":[[time.time(), handshake_time]], "fail_time":0,
                                    "success_time":0, "get_time":0, "links":0,
                                    "down_fail":down_fail, "down_fail_time":0}

            if 'gws' in server:
                self.gws_ip_list.append(ip)
            return True
        except Exception as e:
            xlog.exception("add_ip err:%s", e)
        finally:
            self.ip_lock.release()
        return False

    def update_ip(self, ip, handshake_time):
        if not isinstance(ip, basestring):
            xlog.error("set_ip input")
            return

        handshake_time = int(handshake_time)
        if handshake_time < 5: # that's impossible
            xlog.warn("%s handshake:%d impossible", ip, 1000 * handshake_time)
            return

        time_now = time.time()
        check_local_network.report_network_ok()
        check_ip.last_check_time = time_now
        check_ip.continue_fail_count = 0

        self.ip_lock.acquire()
        try:
            if ip in self.ip_dict:


                # Case: some good ip, average handshake time is 300ms
                # some times ip package lost cause handshake time become 2000ms
                # this ip will not return back to good ip front until all become bad
                # There for, prevent handshake time increase too quickly.
                org_time = self.ip_dict[ip]['handshake_time']
                if handshake_time - org_time > 500:
                    self.ip_dict[ip]['handshake_time'] = org_time + 500
                else:
                    self.ip_dict[ip]['handshake_time'] = handshake_time

                self.ip_dict[ip]['success_time'] = time_now
                if self.ip_dict[ip]['fail_times'] > 0:
                    self.good_ip_num += 1
                self.ip_dict[ip]['fail_times'] = 0
                self.append_ip_history(ip, handshake_time)
                self.ip_dict[ip]["fail_time"] = 0

                self.iplist_need_save = True

            #xlog.debug("update ip:%s not exist", ip)
        except Exception as e:
            xlog.error("update_ip err:%s", e)
        finally:
            self.ip_lock.release()

        self.save_ip_list()

    def report_connect_fail(self, ip, force_remove=False):
        self.ip_lock.acquire()
        try:
            time_now = time.time()
            if not ip in self.ip_dict:
                xlog.debug("report_connect_fail %s not exist", ip)
                return

            if force_remove:
                if self.ip_dict[ip]['fail_times'] == 0:
                    self.good_ip_num -= 1
                del self.ip_dict[ip]

                if ip in self.gws_ip_list:
                    self.gws_ip_list.remove(ip)

                xlog.info("remove ip:%s left amount:%d gws_num:%d", ip, len(self.ip_dict), len(self.gws_ip_list))
                return

            self.ip_dict[ip]['links'] -= 1

            # ignore if system network is disconnected.
            if not check_local_network.is_ok():
                xlog.debug("report_connect_fail network fail")
                return

            check_local_network.report_network_fail()
            if not check_local_network.is_ok():
                return

            fail_time = self.ip_dict[ip]["fail_time"]
            if time_now - fail_time < 1:
                xlog.debug("fail time too near %s", ip)
                return

            if self.ip_dict[ip]['fail_times'] == 0:
                self.good_ip_num -= 1
            self.ip_dict[ip]['fail_times'] += 1
            self.append_ip_history(ip, "fail")
            self.ip_dict[ip]["fail_time"] = time_now

            self.to_check_ip_queue.put((ip, time_now + 10))
            xlog.debug("report_connect_fail:%s", ip)

        except Exception as e:
            xlog.exception("report_connect_fail err:%s", e)
        finally:
            self.iplist_need_save = True
            self.ip_lock.release()

        if not self.is_ip_enough():
            self.search_more_google_ip()

    def report_connect_closed(self, ip, reason=""):
        xlog.debug("%s close:%s", ip, reason)
        if reason != "down fail":
            return

        self.ip_lock.acquire()
        try:
            time_now = time.time()
            if not ip in self.ip_dict:
                return

            if self.ip_dict[ip]['down_fail'] == 0:
                self.good_ip_num -= 1

            self.ip_dict[ip]['down_fail'] += 1
            self.append_ip_history(ip, reason)
            self.ip_dict[ip]["down_fail_time"] = time_now
            xlog.debug("ssl_closed %s", ip)
        except Exception as e:
            xlog.error("ssl_closed %s err:%s", ip, e)
        finally:
            self.ip_lock.release()

    def ssl_closed(self, ip, reason=""):
        #xlog.debug("%s ssl_closed:%s", ip, reason)
        self.ip_lock.acquire()
        try:
            if ip in self.ip_dict:
                if self.ip_dict[ip]['links']:
                    self.ip_dict[ip]['links'] -= 1
                    self.append_ip_history(ip, "C[%s]"%reason)
                    xlog.debug("ssl_closed %s", ip)
        except Exception as e:
            xlog.error("ssl_closed %s err:%s", ip, e)
        finally:
            self.ip_lock.release()

    def check_ip_process(self):
        while connect_control.keep_running:
            try:
                ip, test_time = self.to_check_ip_queue.get()
            except:
                continue

            time_wait = test_time - time.time()
            if time_wait > 0:
                time.sleep(time_wait)

            if not check_local_network.is_ok():
                try:
                    if self.ip_dict[ip]['fail_times']:
                        self.ip_dict[ip]['fail_times'] = 0
                        self.good_ip_num += 1
                except:
                    pass
                continue

            result = check_ip.test_gae_ip2(ip)
            if result and result.support_gae:
                self.add_ip(ip, result.handshake_time, result.domain, "gws")
                xlog.debug("restore ip:%s", ip)
                continue

            xlog.debug("ip:%s real fail", ip)

    def remove_slowest_ip(self):
        if len(self.gws_ip_list) <= self.max_good_ip_num:
            return

        self.try_sort_gws_ip(force=True)

        self.ip_lock.acquire()
        try:
            ip_num = len(self.gws_ip_list)
            while ip_num > self.max_good_ip_num:

                ip = self.gws_ip_list[ip_num - 1]

                property = self.ip_dict[ip]
                server = property['server']
                fails = property['fail_times']
                handshake_time = property['handshake_time']
                xlog.info("remove_slowest_ip:%s handshake_time:%d, fails:%d", ip, handshake_time, fails)
                del self.ip_dict[ip]

                if 'gws' in server and ip in self.gws_ip_list:
                    self.gws_ip_list.remove(ip)

                ip_num -= 1

        except Exception as e:
            xlog.exception("remove_slowest_ip err:%s", e)
        finally:
            self.ip_lock.release()

    def recheck_ip(self, ip):
        # recheck ip if not work.
        # can block.
        if not check_local_network.is_ok():
            xlog.debug("recheck_ip:%s network is fail", ip)
            return

        self.report_connect_fail(ip)

        connect_control.start_connect_register()
        result = check_ip.test_gae_ip2(ip)
        connect_control.end_connect_register()
        if not result:
            # connect fail.
            # do nothing
            return

        if not result.support_gae:
            self.report_connect_fail(ip, force_remove=True)
            xlog.debug("recheck_ip:%s real fail, removed.", ip)
        else:
            self.add_ip(ip, result.handshake_time, result.domain, "gws")
            xlog.debug("recheck_ip:%s restore okl", ip)

    def scan_ip_worker(self):
        while self.scan_thread_count <= self.scan_ip_thread_num and connect_control.keep_running:
            if not connect_control.allow_scan():
                time.sleep(10)
                continue

            try:
                time.sleep(1)
                ip = self.ip_range.get_ip()

                if ip in self.ip_dict:
                    continue

                connect_control.start_connect_register()
                result = check_ip.test_gae_ip2(ip)
                connect_control.end_connect_register()
                if not result or not result.support_gae:
                    continue

                if self.add_ip(ip, result.handshake_time, result.domain, "gws"):
                    #xlog.info("add  %s  CN:%s  type:%s  time:%d  gws:%d ", ip,
                    #     result.domain, result.server_type, result.handshake_time, len(self.gws_ip_list))
                    xlog.info("scan_ip add ip:%s time:%d", ip, result.handshake_time)
                    scan_ip_log.info("Add %s time:%d CN:%s ", ip, result.handshake_time, result.domain)
                    self.remove_slowest_ip()
                    self.save_ip_list()
            except Exception as e:
                xlog.exception("google_ip.runJob fail:%r", e)

        self.scan_thread_lock.acquire()
        self.scan_thread_count -= 1
        self.scan_thread_lock.release()
        #xlog.info("scan_ip_worker exit")

    def search_more_google_ip(self):
        if config.USE_IPV6:
            return

        new_thread_num = self.scan_ip_thread_num - self.scan_thread_count
        if new_thread_num < 1:
            return

        for i in range(0, new_thread_num):
            self.scan_thread_lock.acquire()
            self.scan_thread_count += 1
            self.scan_thread_lock.release()

            p = threading.Thread(target = self.scan_ip_worker)
            p.start()

    def scan_all_exist_ip(self):
        max_scan_ip_thread_num = self.max_scan_ip_thread_num
        self.max_scan_ip_thread_num = 0
        self.adjust_scan_thread_num()

        for ip in self.ip_dict:
            self.scan_exist_ip_queue.put(ip)
        xlog.debug("start scan all exist ip, num:%d", self.scan_exist_ip_queue.qsize())

        self.keep_scan_all_exist_ip = True
        scan_threads = []
        for i in range(0, 50):
            th = threading.Thread(target=self.scan_exist_ip_worker, )
            th.start()
            scan_threads.append(th)

        for th in scan_threads:
            th.join()

        self.try_sort_gws_ip()
        xlog.debug("finished scan all exist ip")

        self.max_scan_ip_thread_num = max_scan_ip_thread_num
        self.adjust_scan_thread_num()
        self.scan_all_ip_thread = None

    def start_scan_all_exist_ip(self):
        if hasattr(self, "scan_all_ip_thread") and self.scan_all_ip_thread:
            xlog.warn("scan all exist ip is running")
            return

        self.scan_all_ip_thread = threading.Thread(target=self.scan_all_exist_ip)
        self.scan_all_ip_thread.start()

    def stop_scan_all_exist_ip(self):
        self.keep_scan_all_exist_ip = False
        self.scan_exist_ip_queue = Queue.Queue()

    def scan_exist_ip_worker(self):
        while connect_control.keep_running and self.keep_scan_all_exist_ip:
            try:
                ip = self.scan_exist_ip_queue.get_nowait()
            except:
                break

            connect_control.start_connect_register()
            result = check_ip.test_gae_ip2(ip)
            connect_control.end_connect_register()
            if not result:
                self.ip_lock.acquire()
                try:
                    if ip not in self.ip_dict:
                        continue

                    if self.ip_dict[ip]['fail_times'] == 0:
                        self.good_ip_num -= 1
                    self.ip_dict[ip]['fail_times'] += 1
                    self.ip_dict[ip]["fail_time"] = time.time()
                finally:
                    self.ip_lock.release()
            elif result.support_gae:
                self.add_ip(ip, result.handshake_time, result.domain, "gws")
            else:
                self.report_connect_fail(ip, force_remove=True)

google_ip = IpManager()

if __name__ == "__main__":
    google_ip.scan_all_exist_ip()
    while True:
        time.sleep(1)