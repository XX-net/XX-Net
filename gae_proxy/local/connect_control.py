
import time

import xlog

connect_allow_time = 0
connect_fail_time = 0
scan_allow_time = 0

block_delay = 10 # (60 * 5)
scan_sleep_time = 600 # Need examination


def allow_connect():
    global connect_allow_time
    if time.time() < connect_allow_time:
        return False
    else:
        return True

def allow_scan():
    global scan_allow_time
    if not allow_connect:
        return False
    if time.time() < scan_allow_time:
        return False
    else:
        return True

def fall_into_honeypot():
    xlog.warn("fall_into_honeypot.")
    global connect_allow_time
    #connect_allow_time = time.time() + block_delay

def scan_sleep():
    xlog.warn("Scan Blocked, due to exceeds Google's frequency limit. Please reduce the number of scan threads.")
    global scan_allow_time
    scan_allow_time = time.time() + scan_sleep_time
    # DOTO: Auto-reduce the setting?

def report_connect_fail():
    global connect_allow_time, connect_fail_time
    if connect_fail_time == 0:
        connect_fail_time = time.time()
    else:
        if time.time() - connect_fail_time > 60:
            connect_allow_time = time.time() + block_delay
            connect_fail_time = 0

def report_connect_success():
    global connect_fail_time
    connect_fail_time = 0

def block_stat():
    global connect_allow_time, scan_allow_time
    wait_time = connect_allow_time - time.time()
    scan_time = scan_allow_time - time.time()
    if wait_time < 0 and scan_time < 0:
        return "OK"
    elif wait_time > 0:
        return "Connect Blocked, %d seconds to wait." % wait_time
    elif scan_time > 0:
        return "Scan Blocked, %d seconds to wait." % scan_time

