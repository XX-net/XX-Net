
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

#set_console_color
err_color = None
warn_color = None
debug_color = None
reset_color = None
set_console_color = lambda x: None
if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
    if os.name == 'nt':
        err_color = 0x04
        warn_color = 0x06
        debug_color = 0x002
        reset_color = 0x07

        import ctypes
        SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
        GetStdHandle = ctypes.windll.kernel32.GetStdHandle
        set_console_color = lambda color: SetConsoleTextAttribute(GetStdHandle(-11), color)

    elif os.name == 'posix':
        err_color = '\033[31m'
        warn_color = '\033[33m'
        debug_color = '\033[32m'
        reset_color = '\033[0m'

        set_console_color = lambda color: sys.stderr.write(color)

#=================================================================

def getLogger(cls, *args, **kwargs):
    return cls(*args, **kwargs)

def basicConfig(*args, **kwargs):
    level = int(kwargs.get('level', INFO))
    if level > DEBUG:
        debug = dummy

def log(level, console_color, html_color, fmt, *args, **kwargs):
    global last_no, buffer_lock, buffer, buffer_size
    string = '%s - [%s] %s\n' % (time.ctime()[4:-5], level, fmt % args)
    buffer_lock.acquire()
    try:
        set_console_color(console_color)
        sys.stderr.write(string)
        set_console_color(reset_color)

        last_no += 1
        buffer[last_no] = string
        buffer_len = len(buffer)
        if buffer_len > buffer_size:
            del buffer[last_no - buffer_size]
    except Exception as e:
        string = '%s - [%s]LOG_EXCEPT: %s, Except:%s<br>' % (time.ctime()[4:-5], level, fmt % args, e)
        last_no += 1
        buffer[last_no] = string
        buffer_len = len(buffer)
        if buffer_len > buffer_size:
            del buffer[last_no - buffer_size]
    finally:
        buffer_lock.release()

#=================================================================
def dummy(*args, **kwargs):
    pass

def debug(fmt, *args, **kwargs):
    log('DEBUG', debug_color, '21610b', fmt, *args, **kwargs)

def info(fmt, *args, **kwargs):
    log('INFO', reset_color, '000000', fmt, *args)

def warning(fmt, *args, **kwargs):
    log('WARNING', warn_color, 'FF8000', fmt, *args, **kwargs)

def warn(fmt, *args, **kwargs):
    warning(fmt, *args, **kwargs)

def error(fmt, *args, **kwargs):
    log('ERROR', err_color, 'FE2E2E', fmt, *args, **kwargs)

def exception(fmt, *args, **kwargs):
    error(fmt, *args, **kwargs)
    error("Except stack:%s", traceback.format_exc(), **kwargs)


def critical(fmt, *args, **kwargs):
    log('CRITICAL', err_color, 'D7DF01', fmt, *args, **kwargs)

#=================================================================
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

def get_last_lines(max_lines): # Unused?
    global buffer_size, buffer, buffer_lock

    buffer_lock.acquire()
    buffer_len = len(buffer)
    jd = {}
    if buffer_len > 0:
        for i in range(last_no - buffer_len + 1, last_no+1):
            jd[i] = buffer[i]
    buffer_lock.release()
    return json.dumps(jd, sort_keys=True)

def get_new_lines(from_no):
    global buffer_size, buffer, buffer_lock

    buffer_lock.acquire()
    jd = {}
    first_no = last_no - len(buffer) + 1
    if from_no < first_no:
        from_no = first_no
    if last_no > from_no:
        for i in range(from_no, last_no+1):
            line = buffer[i]
            try:
                jd[i] = unicode(line, errors='replace')
            except Exception as e:
                print("unicode err:%r" % e)
                print("line can't decode:%s" % line)
                print("Except stack:%s" % traceback.format_exc())
                jd[i] = ""
    buffer_lock.release()
    return json.dumps(jd, sort_keys=True)

if __name__ == "__main__":
    st = "\xce\xce"
    str = st #unicode(st, errors='replace')
    jd={}
    jd[0]=str
    st2 = json.dumps(jd)
    print st2