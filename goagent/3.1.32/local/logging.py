
import os
import sys
import time
import traceback
import threading
import json


buffer = {} # id => line
buffer_size = 500
last_no = 0
buffer_lock = threading.Lock()

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0


level = INFO
__set_error_color = lambda: None
__set_warning_color = lambda: None
__set_debug_color = lambda: None
__reset_color = lambda: None
if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
    if os.name == 'nt':
        import ctypes
        SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
        GetStdHandle = ctypes.windll.kernel32.GetStdHandle
        __set_error_color = lambda: SetConsoleTextAttribute(GetStdHandle(-11), 0x04)
        __set_warning_color = lambda: SetConsoleTextAttribute(GetStdHandle(-11), 0x06)
        __set_debug_color = lambda: SetConsoleTextAttribute(GetStdHandle(-11), 0x002)
        __reset_color = lambda: SetConsoleTextAttribute(GetStdHandle(-11), 0x07)
    elif os.name == 'posix':
        __set_error_color = lambda: sys.stderr.write('\033[31m')
        __set_warning_color = lambda: sys.stderr.write('\033[33m')
        __set_debug_color = lambda: sys.stderr.write('\033[32m')
        __reset_color = lambda: sys.stderr.write('\033[0m')


def getLogger(cls, *args, **kwargs):
    return cls(*args, **kwargs)

def basicConfig(*args, **kwargs):
    level = int(kwargs.get('level', INFO))
    if level > DEBUG:
        debug = dummy

def log(level, fmt, *args, **kwargs):
    global last_no, buffer_lock, buffer, buffer_size
    string = '%s - [%s] %s\n' % (time.ctime()[4:-5], level, fmt % args)
    sys.stderr.write(string)

    buffer_lock.acquire()
    last_no += 1
    buffer[last_no] = string
    buffer_len = len(buffer)
    if buffer_len > buffer_size:
        del buffer[last_no - buffer_size]
    buffer_lock.release()

def set_buffer_size(set_size):
    global buffer_size, buffer, buffer_lock

    buffer_lock.acquire()
    buffer_size = set_size
    buffer_len = len(buffer)
    if buffer_len > buffer_size:
        for i in range(last_no - buffer_len, last_no - buffer_size):
            try:
                del buffer[i]
            except:
                pass
    buffer_len = len(buffer)
    buffer_lock.release()

def get_last_lines(max_lines):
    global buffer_size, buffer, buffer_lock

    buffer_lock.acquire()
    buffer_len = len(buffer)
    jd = {}
    if buffer_len > 0:
        for i in range(last_no - buffer_len + 1, last_no+1):
            jd[i] = buffer[i]
    buffer_lock.release()
    return json.dumps(jd)

def get_new_lines(from_no):
    global buffer_size, buffer, buffer_lock

    buffer_lock.acquire()
    jd = {}
    first_no = last_no - len(buffer) + 1
    if from_no < first_no:
        from_no = first_no
    if last_no >= from_no:
        for i in range(from_no, last_no+1):
            jd[i] = buffer[i]
    buffer_lock.release()
    return json.dumps(jd)


def dummy(*args, **kwargs):
    pass

def debug(fmt, *args, **kwargs):
    __set_debug_color()
    log('DEBUG', fmt, *args, **kwargs)
    __reset_color()

def info(fmt, *args, **kwargs):
    log('INFO', fmt, *args)

def warning(fmt, *args, **kwargs):
    __set_warning_color()
    log('WARNING', fmt, *args, **kwargs)
    __reset_color()

def warn(fmt, *args, **kwargs):
    warning(fmt, *args, **kwargs)

def error(fmt, *args, **kwargs):
    __set_error_color()
    log('ERROR', fmt, *args, **kwargs)
    __reset_color()

def exception(fmt, *args, **kwargs):
    error(fmt, *args, **kwargs)
    sys.stderr.write(traceback.format_exc() + '\n')

def critical(fmt, *args, **kwargs):
    __set_error_color()
    log('CRITICAL', fmt, *args, **kwargs)
    __reset_color()
