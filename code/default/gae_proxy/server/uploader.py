#!/usr/bin/env python
# coding:utf-8

import sys
import os
import re
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

import logging
#logging.basicConfig(filename='upload1.log',level=logging.DEBUG)
fh = logging.FileHandler('upload.log')
# create console handler with a higher log level
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(fh)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

sys.modules.pop('google', None)
lib_path = os.path.join(code_path, "lib")
sys.path.insert(0, lib_path)

noarch_path = os.path.abspath(os.path.join(code_path, os.path.pardir, os.path.pardir, "python27", "1.0", "lib", "noarch"))
sys.path.append(noarch_path)

import mimetypes
mimetypes._winreg = None


from google.appengine.tools import appengine_rpc, appcfg



def upload(appid):
    global code_path

    logging.info("============  Begin upload  ============")
    logging.info("appid:%s", appid)

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
                #"--noauth_local_webserver"
                result = appcfg.AppCfgApp(['appcfg', 'rollback', dirname ]).Run()
                if result != 0:
                    continue
                result = appcfg.AppCfgApp(['appcfg', 'update', dirname]).Run()
                if result != 0:
                    continue
                return True
            except appengine_rpc.ClientLoginError as e:
                logging.info("upload  fail: %s" % e)
                raise e
            except Exception as e:
                logging.exception("upload fail:%r", e)
                if i < 99:
                    logging.info("Retry %d time..." % (i + 1))
                    time.sleep(i)
                else:
                    logging.info("Retry max time, failed." )

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
        logging.info("appid wrong:%s" % appid)
        return False
    if not re.match(r'[0-9a-zA-Z\-|]+', appid):
        logging.info(u'appid:%s format err, check http://appengine.google.com !' % appid)
        return False
    if any(x in appid.lower() for x in ('ios', 'android', 'mobile')):
        logging.info(u'appid:%s format err, check http://appengine.google.com !' % appid)
        logging.info(u'appid 不能包含 ios/android/mobile 等字样。')
        return False
    return True


def clean_cookie_file():
    cookie_file = "~/.appcfg_oauth2_tokens"
    cookie_file = os.path.expanduser(cookie_file)
    try:
        os.remove(cookie_file)
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
            logging.info('Setting in the %s password failed!' % file_name)


def uploads(appids, rc4_password):
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
            if upload(appid):
                success_appid_list.append(appid)
            else:
                fail_appid_list.append(appid)

    except appengine_rpc.ClientLoginError as e:
        logging.info("Auth fail. Please check you password.")
        logging.info("If you've enabled the 2-Step-Verification, please sign in using App Passwords: https://security.google.com/settings/security/apppasswords")
        logging.info("If you are not enabled the 2-Step-Verification, please allowing less secure apps to access: https://www.google.com/settings/security/lesssecureapps")
        logging.info("登录失败，请检查你的帐号密码。")
        logging.info("如果已启用两步验证，请申请应用专用密码: https://security.google.com/settings/security/apppasswords")
        logging.info("如果没有启用两步验证，请允许弱安全应用: https://www.google.com/settings/security/lesssecureapps")

        fail_appid_list = appids.split('|')

    clean_cookie_file()
    logging.info("=======================")

    if len(success_appid_list) > 0:
        logging.info("Deploy %d appid successed." % len(success_appid_list))

    if len(fail_appid_list) > 0:
        logging.info("Deploy failed appid list:")
        for appid in fail_appid_list:
            logging.info("- %s" % appid)

    logging.info("== END ==")

    update_rc4_password('')


def main():
    if len(sys.argv) < 2:
        logging.info("Usage: uploader.py <appids> [-debug] [-password rc4_password]")
        input_line = " ".join(sys.argv)
        logging.info("input err: %s " % input_line)
        logging.info("== END ==")
        exit()

    appids = sys.argv[1]
    rc4_password = "";

    if len(sys.argv) > 2:
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "-debug":
                logger.setLevel(logging.DEBUG)
                logging.info("enable debug logging")
            elif sys.argv[i] == "-password":
                i += 1
                if i < len(sys.argv):
                    rc4_password = sys.argv[i]
                logging.info("use rc4_password: %s" % rc4_password)
            else:
                logging.info("unknow argv: %s" % sys.argv[i])

            i += 1

    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8087'
    logging.info("set proxy to http://127.0.0.1:8087")

    uploads(appids, rc4_password)


if __name__ == '__main__':
    main()
