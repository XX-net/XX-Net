
import time
import threading
import xlog
import sys
from config import config

# change to False when exit: system tray exit menu, or Ctrl+C in console
# then GoAgent will quit
# Every long running thread should check it and exit when False
keep_running = True

#=============================================
# concurrent connect control
# Windows10 will block sound when too many concurrent connect out in the same time.
# so when user request web, scan thread will stop to reduce concurrent action.
def check_win10():
    if sys.platform != "win32":
        return False

    import ctypes
    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [('dwOSVersionInfoSize', ctypes.c_ulong),
                    ('dwMajorVersion', ctypes.c_ulong),
                    ('dwMinorVersion', ctypes.c_ulong),
                    ('dwBuildNumber', ctypes.c_ulong),
                    ('dwPlatformId', ctypes.c_ulong),
                    ('szCSDVersion', ctypes.c_wchar*128),
                    ('wServicePackMajor', ctypes.c_ushort),
                    ('wServicePackMinor', ctypes.c_ushort),
                    ('wSuiteMask', ctypes.c_ushort),
                    ('wProductType', ctypes.c_byte),
                    ('wReserved', ctypes.c_byte)]

    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        xlog.warn("Failed to get win32 OS version")
        return False

    if os_version.dwMajorVersion == 10:
        xlog.info("detect Win10, enable connect concurent control.")
        return True

    return False

is_win10 = check_win10()

ccc_lock = threading.Lock()
high_prior_lock = []
low_prior_lock = []
high_prior_connecting_num = 0
low_prior_connecting_num = 0
last_connect_time = 0

min_connect_interval = 0.03

def start_connect_register(high_prior=False):
    global high_prior_connecting_num, low_prior_connecting_num, last_connect_time
    if not is_win10:
        return

    ccc_lock.acquire()
    try:
        if high_prior_connecting_num + low_prior_connecting_num > config.https_max_connect_thread:
            atom_lock = threading.Lock()
            atom_lock.acquire()
            if high_prior:
                high_prior_lock.append(atom_lock)
            else:
                low_prior_lock.append(atom_lock)
            ccc_lock.release()
            atom_lock.acquire()

            ccc_lock.acquire()

        last_connect_interval = time.time() - last_connect_time
        if last_connect_interval < 0:
            xlog.error("last_connect_interval:%f", last_connect_interval)
            return

        if last_connect_interval < min_connect_interval:
            wait_time = min_connect_interval - last_connect_interval
            time.sleep(wait_time)

        if high_prior:
            high_prior_connecting_num += 1
        else:
            low_prior_connecting_num += 1
    finally:
        last_connect_time = time.time()
        ccc_lock.release()


def end_connect_register(high_prior=False):
    global high_prior_connecting_num, low_prior_connecting_num
    if not is_win10:
        return

    ccc_lock.acquire()
    try:
        if high_prior:
            high_prior_connecting_num -= 1
        else:
            low_prior_connecting_num -= 1

        if high_prior_connecting_num + low_prior_connecting_num < config.https_max_connect_thread:
            if len(high_prior_lock):
                atom_lock = high_prior_lock.pop()
                atom_lock.release()
                return

            if len(low_prior_lock):
                atom_lock = low_prior_lock.pop()
                atom_lock.release()
                return
    finally:
        ccc_lock.release()

#=============================================
# this design is for save resource when browser have no request for long time.
# when idle, connect pool will not maintain the connect ready link to save resources.

last_request_time = 0

def touch_active():
    global last_request_time
    last_request_time = time.time()

def inactive_time():
    global last_request_time
    return time.time() - last_request_time

def is_active(timeout=60):
    if inactive_time() < timeout:
        return True
    else:
        return False
#==============================================
# honey pot is out of date, setup in 2015-05
# The code may be deleted in the future
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
#=============================================
