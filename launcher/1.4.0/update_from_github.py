
import os
import sys

current_path = os.path.dirname(os.path.abspath(__file__))
python_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir, 'python27', '1.0'))
noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)
import yaml

import urllib2
import time
import subprocess
import logging
import re
import zipfile
import config
import shutil

autoproxy = '127.0.0.1:8087'
opener = urllib2.build_opener(urllib2.ProxyHandler({'http': autoproxy, 'https': autoproxy}))

root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))

data_root = os.path.join(root_path, 'data')
if not os.path.isdir(data_root):
    os.mkdir(data_root)

download_path = os.path.join(data_root, 'downloads')
if not os.path.isdir(download_path):
    os.mkdir(download_path)

download_progress = {} # link => {"size", 'downloaded', status:downloading|canceled|finished}

def current_version():
    readme_file = os.path.join(root_path, "README.md")
    try:
        fd = open(readme_file, "r")
        lines = fd.readlines()
        import re
        p = re.compile(r'https://codeload.github.com/XX-net/XX-Net/zip/([0-9]+)\.([0-9]+)\.([0-9]+)') #zip/([0-9]+).([0-9]+).([0-9]+)
        #m = p.match(content)
        for line in lines:
            m = p.match(line)
            if m:
                version = m.group(1) + "." + m.group(2) + "." + m.group(3)
                return version
    except Exception as e:
        logging.exception("xxnet_version fail")
    return "get_version_fail"

def download_file(url, file):
    if url not in download_progress:
        download_progress[url] = {}
        download_progress[url]["status"] = "downloading"
    else:
        if download_progress[url]["status"] == "downloading":
            logging.error("url in downloading, %s", url)
            return False

    try:
        logging.info("download %s to %s", url, file)
        req = opener.open(url)
        download_progress[url]["size"] = int(req.headers.get('content-length') or 0)

        CHUNK = 16 * 1024
        downloaded = 0
        with open(file, 'wb') as fp:
            while True:
                chunk = req.read(CHUNK)
                if not chunk: break
                fp.write(chunk)
                downloaded += len(chunk)
                download_progress[url]["downloaded"] = downloaded

        download_progress[url]["status"] = "finished"
        return True
    except Exception as e:
        logging.warn("download %s to %s fail:%r", url, file, e)
        return False

def get_xxnet_url_version(readme_file):
    versions = []
    try:
        fd = open(readme_file, "r")
        lines = fd.readlines()
        p = re.compile(r'https://codeload.github.com/XX-net/XX-Net/zip/([0-9]+)\.([0-9]+)\.([0-9]+)')
        for line in lines:
            m = p.match(line)
            if m:
                version = m.group(1) + "." + m.group(2) + "." + m.group(3)
                versions.append([m.group(0), version])
                if len(versions) == 2:
                    return versions
    except Exception as e:
        logging.exception("xxnet_version fail:%r", e)
        raise "get_version_fail:" % readme_file

def get_github_versions():
    readme_url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/README.md"
    readme_targe = os.path.join(download_path, "README.md")

    if not download_file(readme_url, readme_targe):
        raise IOError("get README %s fail:" % readme_url)

    versions = get_xxnet_url_version(readme_targe)
    return versions

def sha1_file(filename):
    import hashlib

    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    try:
        with open(filename, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()
    except:
        return False

def download_overwrite_new_version(xxnet_version):
    xxnet_url = 'https://codeload.github.com/XX-net/XX-Net/zip/%s' % xxnet_version
    xxnet_zip_file = os.path.join(download_path, "XX-Net-%s.zip" % xxnet_version)
    xxnet_unzip_path = os.path.join(download_path, "XX-Net-%s" % xxnet_version)

    if not download_file(xxnet_url, xxnet_zip_file):
        raise "download xxnet zip fail:" % download_path

    with zipfile.ZipFile(xxnet_zip_file, "r") as dz:
        dz.extractall(download_path)
        dz.close()

    if config.get(["update", "uuid"], '') == 'test':
        return

    for root, subdirs, files in os.walk(xxnet_unzip_path):
        #print "root:", root
        relate_path = root[len(xxnet_unzip_path)+1:]
        for subdir in subdirs:

            target_path = os.path.join(root_path, relate_path, subdir)
            if not os.path.isdir(target_path):
                logging.info("mkdir %s", target_path)
                os.mkdir(target_path)

        for filename in files:
            src_file = os.path.join(root, filename)
            dst_file = os.path.join(root_path, relate_path, filename)
            if not os.path.isfile(dst_file) or sha1_file(src_file) != sha1_file(dst_file):
                shutil.copy(src_file, dst_file)
                logging.info("copy %s => %s", src_file, dst_file)

def update_config(version):
    config.config["modules"]["goagent"]["current_version"] = ""
    config.config["modules"]["launcher"]["current_version"] = ""
    config.save()


def restart_xxnet():
    import module_init
    module_init.stop_all()
    import web_control
    web_control.stop()

    current_path = os.path.dirname(os.path.abspath(__file__))
    start_sript = os.path.abspath( os.path.join(current_path, os.pardir, "start.py"))

    subprocess.Popen([sys.executable, start_sript], shell=False)
    os._exit(0)

def update_version(version):
    try:
        download_overwrite_new_version(version)
        update_config(version)
        restart_xxnet()
    except Exception as e:
        logging.exception("update version %d fail:%r", version, e)

