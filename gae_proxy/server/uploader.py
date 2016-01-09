#!/usr/bin/env python
# coding:utf-8

import sys
import os
import re
import socket
import time

#patch for ArchLinux: CERTIFICATE_VERIFY_FAILED
try:
    import ssl
    if hasattr(ssl, "_create_unverified_context") and hasattr(ssl, "_create_default_https_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

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
        if message == '\n':
            time_string = ""
        else:
            time_string = '%s - ' % (time.ctime()[4:-5])
        self.terminal.write(message)
        out_msg = time_string + message
        self.fd.write(out_msg.decode('utf-8').encode('utf-8'))
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


    dirname = os.path.join(code_path, "gae")
    assert isinstance(dirname, basestring) and isinstance(appid, basestring)
    app_yaml_file = os.path.join(dirname, 'app.yaml')
    template_filename = os.path.join(dirname, 'app.template.yaml')
    assert os.path.isfile(template_filename), u'%s not exists!' % template_filename

    with open(template_filename, 'rb') as fp:
        yaml = fp.read()
    with open(app_yaml_file, 'wb') as fp:
        fp.write(re.sub(r'application:\s*\S+', 'application: '+appid, yaml))

    try:
        for i in range(3):
            try:
                result = appcfg.AppCfgApp(['appcfg', 'rollback', dirname], password_input_fn=getpass_getpass, raw_input_fn = my_input, error_fh = my_stdout).Run()
                if result != 0:
                    continue
                result = appcfg.AppCfgApp(['appcfg', 'update', dirname], password_input_fn=getpass_getpass, raw_input_fn = my_input, error_fh = my_stdout).Run()
                if result != 0:
                    continue
                return True
            except appengine_rpc.ClientLoginError as e:
                my_stdout.write("upload  fail: %s\n\n" % e)
                raise e
            except Exception as e:
                my_stdout.write("upload  fail: %s\n\n" % e)
                if i < 99:
                    my_stdout.write("Retry %d time...\n\n" % (i + 1))
                    time.sleep(i)
                else:
                    my_stdout.write("Retry max time, failed.\n\n" )

        return False

    finally:
        try:
            os.remove(app_yaml_file)
        except OSError:
            pass



def println(s, file=sys.stderr):
    assert type(s) is type(u'')
    file.write(s.encode(sys.getfilesystemencoding(), 'replace') + os.linesep)

def appid_is_valid(appid):
    if len(appid) < 6:
        my_stdout.write("appid wrong:%s\n" % appid)
        return False
    if not re.match(r'[0-9a-zA-Z\-|]+', appid):
        my_stdout.write(u'appid:%s format err, check http://appengine.google.com !' % appid)
        return False
    if any(x in appid.lower() for x in ('ios', 'android', 'mobile')):
        my_stdout.write(u'appid:%s format err, check http://appengine.google.com !' % appid)
        my_stdout.write(u'appid 不能包含 ios/android/mobile 等字样。')
        return False
    return True

def clean_cookie_file():
    try:
        os.remove(appengine_rpc.HttpRpcServer.DEFAULT_COOKIE_FILE_PATH)
    except OSError:
        pass

def update_rc4_password(rc4_password):
    global code_path
    file_names = ["gae.py", "wsgi.py"]
    for file_name in file_names:
        filename = os.path.join(code_path, "gae", file_name)
        try:
            with open(filename, 'rb') as fp:
                file_data = fp.read()
            with open(filename, 'wb') as fp:
                fp.write(re.sub(r"__password__ = '.*?'", "__password__ = '%s'" % rc4_password, file_data))

        except IOError as e:
            my_stdout.write('Setting in the %s password failed!\n' % file_name)

def uploads(appids, email, password, rc4_password):
    update_rc4_password(rc4_password)

    clean_cookie_file()

    success_appid_list = []
    fail_appid_list = []
    try:
        for appid in appids.split('|'):
            if appid == "":
                continue
            if not appid_is_valid(appid):
                continue
            if upload(appid, email, password):
                success_appid_list.append(appid)
            else:
                fail_appid_list.append(appid)

    except appengine_rpc.ClientLoginError as e:
        my_stdout.write("Auth fail. Please check you password.\n")
        my_stdout.write("登录失败，请检查你的帐号密码。\n")
        my_stdout.write("如果启用两阶段登录，请申请应用专用密码: https://security.google.com/settings/security/apppasswords\n")
        my_stdout.write("如果没有启用两阶段登录，请允许弱安全应用: https://www.google.com/settings/security/lesssecureapps\n")

        fail_appid_list = appids.split('|')

    clean_cookie_file()
    my_stdout.write("=======================\n")

    if len(success_appid_list) > 0:
        my_stdout.write("Deploy %d appid successed.\n" % len(success_appid_list))

    if len(fail_appid_list) > 0:
        my_stdout.write("Deploy failed appid list:\n")
        for appid in fail_appid_list:
            my_stdout.write("- %s\n" % appid)


    my_stdout.write("== END ==\n\n")

    do_clean_up()

    update_rc4_password('')

def main():
    if len(sys.argv) < 3:
        my_stdout.write("Usage: uploader.py <appids> <email> [password] [rc4_password]\r\n")
        input_line = " ".join(sys.argv)
        my_stdout.write("input err: %s \r\n" % input_line)
        my_stdout.write("== END ==\n")
        exit()

    appids = sys.argv[1]
    email = sys.argv[2]

    if len(sys.argv) >= 4:
        password = sys.argv[3]
    else:
        import getpass
        password = getpass.getpass("password:")

    if len(sys.argv) >= 5:
        rc4_password = sys.argv[4]
    else:
        rc4_password = ''

    uploads(appids, email, password, rc4_password)

if __name__ == '__main__':
    main()
