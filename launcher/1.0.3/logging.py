
import os
import sys
import time
import traceback


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

#def __init__(*args, **kwargs):
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


current_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, "data", "launcher", "log.log"))
log_fd = open(log_path, "a")

def getLogger(cls, *args, **kwargs):
    return cls(*args, **kwargs)

def basicConfig(*args, **kwargs):
    level = int(kwargs.get('level', INFO))
    if level > DEBUG:
        debug = dummy

def log(level, fmt, *args, **kwargs):
    string = '%s - [%s] %s\n' % (time.ctime()[4:-5], level, fmt % args)
    #print string
    sys.stderr.write(string)
    log_fd.write(string)
    try:
        log_fd.flush()
    except:
        pass

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
