
import os
import sys
import time
from datetime import datetime
import traceback
import threading
import json
import shutil
import types


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0


class Logger():
    def __init__(self, buffer_size=0, file_name=None, roll_num=1):
        self.file_max_size = 1024 * 1024
        self.buffer_lock = threading.Lock()
        self.buffer = {} # id => line
        self.buffer_size = buffer_size
        self.last_no = 0
        self.min_level = NOTSET
        self.log_fd = None
        self.set_color()
        self.roll_num = roll_num
        if file_name:
            self.set_file(file_name)

    def set_buffer(self, buffer_size):
        self.buffer_size = buffer_size
        
    def setLevel(self, level):
        if level == "DEBUG":
            self.min_level = DEBUG
        elif level == "INFO":
            self.min_level = INFO
        elif level == "WARN":
            self.min_level = WARN
        elif level == "ERROR":
            self.min_level = ERROR
        elif level == "FATAL":
            self.min_level = FATAL
        else:
            print("log level not support:%s", level)
    
    def set_color(self):
        self.err_color = None
        self.warn_color = None
        self.debug_color = None
        self.reset_color = None
        self.set_console_color = lambda x: None
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            if os.name == 'nt':
                self.err_color = 0x04
                self.warn_color = 0x06
                self.debug_color = 0x002
                self.reset_color = 0x07
        
                import ctypes
                SetConsoleTextAttribute = ctypes.windll.kernel32.SetConsoleTextAttribute
                GetStdHandle = ctypes.windll.kernel32.GetStdHandle
                self.set_console_color = lambda color: SetConsoleTextAttribute(GetStdHandle(-11), color)
        
            elif os.name == 'posix':
                self.err_color = '\033[31m'
                self.warn_color = '\033[33m'
                self.debug_color = '\033[32m'
                self.reset_color = '\033[0m'
        
                self.set_console_color = lambda color: sys.stderr.write(color)

    def set_file(self, file_name):
        self.log_filename = file_name
        if os.path.isfile(file_name):
            self.file_size = os.path.getsize(file_name)
            if self.file_size > self.file_max_size:
                self.roll_log()
                self.file_size = 0
        else:
            self.file_size = 0

        self.log_fd = open(file_name, "w")

    def roll_log(self):
        for i in range(self.roll_num, 1, -1):
            new_name = "%s.%d" % (self.log_filename, i)
            old_name = "%s.%d" % (self.log_filename, i - 1)
            if not os.path.isfile(old_name):
                continue

            #self.info("roll_log %s -> %s", old_name, new_name)
            shutil.move(old_name, new_name)

        shutil.move(self.log_filename, self.log_filename + ".1")

    def log(self, level, console_color, html_color, fmt, *args, **kwargs):
        now = datetime.now()
        time_str = now.strftime("%b %d %H:%M:%S.%f")[:19]
        string = '%s - [%s] %s\n' % (time_str, level, fmt % args)
        self.buffer_lock.acquire()
        try:
            self.set_console_color(console_color)
            sys.stderr.write(string)
            self.set_console_color(self.reset_color)
    
            if self.log_fd:
                self.log_fd.write(string)
                try:
                    self.log_fd.flush()
                except:
                    pass

                self.file_size += len(string)
                if self.file_size > self.file_max_size:
                    self.log_fd.close()
                    self.log_fd = None
                    self.roll_log()
                    self.log_fd = open(self.log_filename, "w")
                    self.file_size = 0

            if self.buffer_size:
                self.last_no += 1
                self.buffer[self.last_no] = string
                buffer_len = len(self.buffer)
                if buffer_len > self.buffer_size:
                    del self.buffer[self.last_no - self.buffer_size]
        except Exception as e:
            string = '%s - [%s]LOG_EXCEPT: %s, Except:%s<br>' % (time.ctime()[4:-5], level, fmt % args, e)
            self.last_no += 1
            self.buffer[self.last_no] = string
            buffer_len = len(self.buffer)
            if buffer_len > self.buffer_size:
                del self.buffer[self.last_no - self.buffer_size]
        finally:
            self.buffer_lock.release()

    def debug(self, fmt, *args, **kwargs):
        if self.min_level > DEBUG:
            return
        self.log('DEBUG', self.debug_color, '21610b', fmt, *args, **kwargs)
    
    def info(self, fmt, *args, **kwargs):
        if self.min_level > INFO:
            return
        self.log('INFO', self.reset_color, '000000', fmt, *args)
    
    def warning(self, fmt, *args, **kwargs):
        if self.min_level > WARN:
            return
        self.log('WARNING', self.warn_color, 'FF8000', fmt, *args, **kwargs)
    
    def warn(self, fmt, *args, **kwargs):
        self.warning(fmt, *args, **kwargs)
    
    def error(self, fmt, *args, **kwargs):
        if self.min_level > ERROR:
            return
        self.log('ERROR', self.err_color, 'FE2E2E', fmt, *args, **kwargs)
    
    def exception(self, fmt, *args, **kwargs):
        self.error(fmt, *args, **kwargs)
        self.error("Except stack:%s", traceback.format_exc(), **kwargs)
    
    def critical(self, fmt, *args, **kwargs):
        if self.min_level > CRITICAL:
            return
        self.log('CRITICAL', self.err_color, 'D7DF01', fmt, *args, **kwargs)
    
    #=================================================================
    def set_buffer_size(self, set_size):
        self.buffer_lock.acquire()
        self.buffer_size = set_size
        buffer_len = len(buffer)
        if buffer_len > self.buffer_size:
            for i in range(self.last_no - buffer_len, self.last_no - self.buffer_size):
                try:
                    del self.buffer[i]
                except:
                    pass
        self.buffer_lock.release()
    
    def get_last_lines(self, max_lines):
        self.buffer_lock.acquire()
        buffer_len = len(self.buffer)
        if buffer_len > max_lines:
            first_no = self.last_no - max_lines
        else:
            first_no = self.last_no - buffer_len + 1

        jd = {}
        if buffer_len > 0:
            for i in range(first_no, self.last_no + 1):
                jd[i] = self.unicode_line(self.buffer[i])
        self.buffer_lock.release()
        return json.dumps(jd)
    
    def get_new_lines(self, from_no):
        self.buffer_lock.acquire()
        jd = {}
        first_no = self.last_no - len(self.buffer) + 1
        if from_no < first_no:
            from_no = first_no

        if self.last_no >= from_no:
            for i in range(from_no, self.last_no + 1):
                jd[i] = self.unicode_line(self.buffer[i])
        self.buffer_lock.release()
        return json.dumps(jd)

    def unicode_line(self, line):
        try:
            if type(line) is types.UnicodeType:
                return line
            else:
                return unicode(line, errors='ignore')
        except Exception as e:
            print("unicode err:%r" % e)
            print("line can't decode:%s" % line)
            print("Except stack:%s" % traceback.format_exc())
            return ""


loggerDict = {}


def getLogger(name=None, buffer_size=0, file_name=None, roll_num=1):
    global loggerDict

    if not isinstance(name, basestring):
        raise TypeError('A logger name must be string or Unicode')
    if isinstance(name, unicode):
        name = name.encode('utf-8')

    if name in loggerDict:
        return loggerDict[name]
    else:
        logger_instance = Logger(buffer_size, file_name, roll_num)
        loggerDict[name] = logger_instance
        return logger_instance