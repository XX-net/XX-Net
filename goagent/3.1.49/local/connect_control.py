
import time

connect_allow_time = 0
connect_fail_time = 0

def allow_connect():
    global connect_allow_time
    if time.time() < connect_allow_time:
        return False
    else:
        return True

def fall_into_honeypot():
    global connect_allow_time
    connect_allow_time = time.time() + (60 * 5)


def report_connect_fail():
    global connect_allow_time, connect_fail_time
    if connect_fail_time == 0:
        connect_fail_time = time.time()
    else:
        if time.time() - connect_fail_time > 30:
            connect_allow_time = time.time() + (60 * 5)

def report_connect_success():
    global connect_fail_time
    connect_fail_time = 0

def block_stat():
    global connect_allow_time
    wait_time = connect_allow_time - time.time()
    if wait_time < 0:
        return "OK"
    else:
        return "Blocked, %d seconds to wait." % wait_time
