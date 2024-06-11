import os
import sys
import time
from datetime import datetime
import traceback
import threading
import json
import shutil
from os.path import join

from six import string_types

import utils

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

# full_log set by server, upload full log for debug (maybe next time start session), remove old log file on reset log
full_log = False

# keep log set by UI, keep all logs, never delete old log, also upload log to server.


class Logger():
    def __init__(self, name, buffer_size=0, file_name=None, roll_num=1,
                 log_path=None, save_start_log=0, save_warning_log=False):
        self.name = str(name)
        self.file_max_size = 1024 * 1024
        self.buffer_lock = threading.RLock()
        self.buffer = {}  # id => line
        self.buffer_size = buffer_size
        self.last_no = 0
        self.min_level = NOTSET
        self.log_fd = None
        self.set_color()
        self.roll_num = roll_num
        if file_name:
            self.set_file(file_name)

        self.log_path = log_path
        self.save_start_log = save_start_log
        self.save_warning_log = save_warning_log
        self.start_log_num = 0
        if log_path and save_start_log:
            now = datetime.now()
            time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
            self.log_fn = os.path.join(log_path, "start_log_%s_%s.log" % (name, time_str))
            self.start_log = open(self.log_fn, "w")
        else:
            self.start_log = None

        if log_path and os.path.exists(join(log_path, "keep_log.txt")):
            self.info("keep log")
            self.keep_log = True
        else:
            self.keep_log = False

        if log_path and save_warning_log:
            self.warning_log_fn = os.path.join(log_path, "%s_warning.log" % (name))
            self.warning_log = open(self.warning_log_fn, "a")
        else:
            self.warning_log_fn = None
            self.warning_log = None

    def set_buffer(self, buffer_size):
        with self.buffer_lock:
            self.buffer_size = buffer_size
            buffer_len = len(self.buffer)
            if buffer_len > self.buffer_size:
                for i in range(self.last_no - buffer_len, self.last_no - self.buffer_size):
                    try:
                        del self.buffer[i]
                    except:
                        pass

    def reset_log_files(self):
        if not (self.keep_log or full_log):
            if self.start_log:
                self.start_log.close()
                self.start_log = None

            if self.warning_log:
                self.warning_log.close()
                self.warning_log = None

        if self.log_path and not self.keep_log:
            for filename in os.listdir(self.log_path):
                fp = os.path.join(self.log_path, filename)
                if not filename.endswith(".log") or fp == self.log_fn or not filename.startswith("start_log_%s" % self.name):
                    continue

                try:
                    os.remove(fp)
                except:
                    pass

        if self.warning_log_fn and not self.keep_log:
            self.warning_log = open(self.warning_log_fn, "a")

    def keep_logs(self):
        self.keep_log = True
        # self.debug("keep log for %s", self.name)
        if not self.log_path:
            return

        with open(join(self.log_path, "keep_log.txt"), "w") as fd:
            fd.write(" ")

        if not self.start_log:
            now = datetime.now()
            time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
            log_fn = os.path.join(self.log_path, "start_log_%s_%s.log" % (self.name, time_str))
            self.start_log = open(log_fn, "w")

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
            print(("log level not support:%s", level))

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

        self.log_fd = open(file_name, "a+")

    def roll_log(self):
        for i in range(self.roll_num, 1, -1):
            new_name = "%s.%d" % (self.log_filename, i)
            old_name = "%s.%d" % (self.log_filename, i - 1)
            if not os.path.isfile(old_name):
                continue

            # self.info("roll_log %s -> %s", old_name, new_name)
            shutil.move(old_name, new_name)

        shutil.move(self.log_filename, self.log_filename + ".1")

    def log(self, level, console_color, html_color, fmt, *args, **kwargs):
        args = utils.bytes2str_only(args)
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]
        string = '%s - [%s] %s\n' % (time_str, level, fmt % args)
        self.buffer_lock.acquire()
        try:
            try:
                console_string = '%s [%s][%s] %s\n' % (time_str, self.name, level, fmt % args)

                self.set_console_color(console_color)
                sys.stderr.write(console_string)
                self.set_console_color(self.reset_color)
            except:
                pass

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

            if self.start_log:
                self.start_log.write(string)
                try:
                    self.start_log.flush()
                except:
                    pass
                self.start_log_num += 1

                if self.start_log_num > self.save_start_log and not self.keep_log and not full_log:
                    self.start_log.close()
                    self.start_log = None

            if self.warning_log and level in ["WARN", "WARNING", "ERROR", "CRITICAL"]:
                self.warning_log.write(string)
                try:
                    self.warning_log.flush()
                except:
                    pass

            if self.buffer_size:
                self.last_no += 1
                self.buffer[self.last_no] = string
                buffer_len = len(self.buffer)
                if buffer_len > self.buffer_size:
                    del self.buffer[self.last_no - self.buffer_size]
        except Exception as e:
            string = '%s - [%s]LOG_EXCEPT: %s, Except:%s<br> %s' % \
                     (time.ctime()[4:-5], level, fmt % args, e, traceback.format_exc())
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

    # =================================================================
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
                jd[i] = utils.to_str(self.buffer[i])
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
                jd[i] = utils.to_str(self.buffer[i])
        self.buffer_lock.release()
        return json.dumps(jd)


class null():
    @staticmethod
    def debug(fmt, *args, **kwargs):
        pass

    @staticmethod
    def info(fmt, *args, **kwargs):
        pass

    @staticmethod
    def warn(fmt, *args, **kwargs):
        pass

    @staticmethod
    def exception(fmt, *args, **kwargs):
        pass


loggerDict = {}


def getLogger(name=None, buffer_size=0, file_name=None, roll_num=1,
              log_path=None, save_start_log=0, save_warning_log=False):
    global loggerDict, default_log
    if name is None:
        for n in loggerDict:
            name = n
            break
    if name is None:
        name = u"default"

    if not isinstance(name, string_types):
        raise TypeError('A logger name must be string or Unicode')
    if isinstance(name, bytes):
        name = name.decode('utf-8')

    if name in loggerDict:
        return loggerDict[name]
    else:
        logger_instance = Logger(name, buffer_size, file_name, roll_num, log_path, save_start_log, save_warning_log)
        loggerDict[name] = logger_instance
        default_log = logger_instance
        return logger_instance


def reset_log_files():
    for name, log in loggerDict.items():
        log.reset_log_files()


def keep_log(temp=False):
    global full_log
    if temp:
        full_log = True
    else:
        for name, log in loggerDict.items():
            log.keep_logs()


default_log = getLogger()


def debug(fmt, *args, **kwargs):
    default_log.debug(fmt, *args, **kwargs)


def info(fmt, *args, **kwargs):
    default_log.info(fmt, *args, **kwargs)


def warning(fmt, *args, **kwargs):
    default_log.warnin(fmt, *args, **kwargs)


def warn(fmt, *args, **kwargs):
    default_log.warn(fmt, *args, **kwargs)


def error(fmt, *args, **kwargs):
    default_log.error(fmt, *args, **kwargs)


def exception(fmt, *args, **kwargs):
    error(fmt, *args, **kwargs)
    error("Except stack:%s", traceback.format_exc(), **kwargs)


def critical(fmt, *args, **kwargs):
    default_log.critical(fmt, *args, **kwargs)
