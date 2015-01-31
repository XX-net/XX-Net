#!/usr/bin/env python
# coding:utf-8

import sys
import os
import re
import socket

code_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(code_path)


sys.modules.pop('google', None)
lib_path = os.path.join(code_path, "lib")
sys.path.insert(0, lib_path)

import mimetypes
mimetypes._winreg = None

import urllib2
import fancy_urllib
fancy_urllib.FancyHTTPSHandler = urllib2.HTTPSHandler


from google.appengine.tools import appengine_rpc, appcfg
appengine_rpc.HttpRpcServer.DEFAULT_COOKIE_FILE_PATH = './.appcfg_cookies'



defined_password = ''
def getpass_getpass(prompt='Password:', stream=None):
    global defined_password
    return defined_password

defined_input = ''
def my_input(prompt):
    global defined_input
    return defined_input



class Logger(object):
    def __init__(self, log_file_name):
        self.terminal = sys.stdout
        self.fd = open(log_file_name, "w")
    def write(self, message):
        self.terminal.write(message)
        self.fd.write(message)
        self.fd.flush()
    def flush(self):
        pass
    def encoding(self, input):
        return input

my_stdout = Logger("upload.log")
org_stderr = sys.stderr
org_stdout = sys.stdout
sys.stderr = my_stdout
sys.stdout = my_stdout

def do_clean_up():
    sys.stderr = org_stderr
    sys.stdout = org_stdout

try:
    socket.create_connection(('127.0.0.1', 8087), timeout=1).close()
    os.environ['HTTPS_PROXY'] = '127.0.0.1:8087'
except:
    pass

def upload(appid, email, password):
    global defined_input
    global defined_password
    global code_path
    defined_input = email
    defined_password = password

    my_stdout.write("============  Begin upload  ============\r\nappid:%s \r\n\r\n" % (appid))

    try:
        os.remove(appengine_rpc.HttpRpcServer.DEFAULT_COOKIE_FILE_PATH)
    except OSError:
        pass

    dirname = os.path.join(code_path, "gae")
    assert isinstance(dirname, basestring) and isinstance(appid, basestring)
    filename = os.path.join(dirname, 'app.yaml')
    template_filename = os.path.join(dirname, 'app.template.yaml')
    assert os.path.isfile(template_filename), u'%s not exists!' % template_filename

    with open(template_filename, 'rb') as fp:
        yaml = fp.read()
    with open(filename, 'wb') as fp:
        fp.write(re.sub(r'application:\s*\S+', 'application: '+appid, yaml))

    for i in range(3):
        try:
            result =  appcfg.AppCfgApp(['appcfg', 'rollback', dirname], password_input_fn=getpass_getpass, raw_input_fn=my_input, error_fh=my_stdout).Run()
            result =  appcfg.AppCfgApp(['appcfg', 'update', dirname], password_input_fn=getpass_getpass, raw_input_fn=my_input, error_fh=my_stdout).Run()
            break
        except Exception as e:
            my_stdout.write("upload  fail: %s\n\n" % e)
            if i < 2:
                my_stdout.write("Retry again.\n\n")

    os.remove(filename)

    try:
        os.remove(appengine_rpc.HttpRpcServer.DEFAULT_COOKIE_FILE_PATH)
    except OSError:
        pass



def println(s, file=sys.stderr):
    assert type(s) is type(u'')
    file.write(s.encode(sys.getfilesystemencoding(), 'replace') + os.linesep)

def uploads(appids, email, password):
    if not re.match(r'[0-9a-zA-Z\-|]+', appids):
        my_stdout.write(u'appid format err, check http://appengine.google.com !')
        my_stdout.write("== END ==\n\n")
        sys.exit(-1)
    if any(x in appids.lower() for x in ('ios', 'android', 'mobile')):
        println(u'appid 不能包含 ios/android/mobile 等字样。')
        my_stdout.write("appid wrong!!!\n")
        my_stdout.write("Don't include ios/android/mobile in appid !\n")
        my_stdout.write("== END ==\n\n")
        sys.exit(-1)

    for appid in appids.split('|'):
        upload(appid, email, password)

    my_stdout.write("== END ==\n\n")
    do_clean_up()

def main():
    if len(sys.argv) <3:
        my_stdout.write("Usage: uploader.py <appids> <email> [password]\r\n")
        input_line = " ".join(sys.argv)
        my_stdout.write("input err: %s \r\n" % input_line)
        my_stdout.write("== END ==\n")
        exit()

    appids = sys.argv[1]
    email = sys.argv[2]
    if len(sys.argv) == 4:
        password = sys.argv[3]
    else:
        import getpass
        password = getpass.getpass("password:")

    uploads(appids, email, password)

if __name__ == '__main__':
    main()
