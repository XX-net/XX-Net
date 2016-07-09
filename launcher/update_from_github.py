
import os
import sys
import urllib2
import time
import subprocess
import threading
import re
import zipfile
import shutil
import stat
import ssl

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
top_path = root_path
data_root = os.path.join(top_path, 'data')
python_path = os.path.join(root_path, 'python27', '1.0')

import config
import update
try:
    from instances import xlog
except:
    import logging
    xlog = logging.getLogger()


if not os.path.isdir(data_root):
    os.mkdir(data_root)


download_path = os.path.join(data_root, 'downloads')
if not os.path.isdir(download_path):
    os.mkdir(download_path)


progress = {} # link => {"size", 'downloaded', status:downloading|canceled|finished:failed}
progress["update_status"] = "Idle"

def get_opener(retry=0):
    if retry == 0:
        opener = urllib2.build_opener()
        return opener
    else:
        return update.get_opener()


def download_file(url, filename):
    if url not in progress:
        progress[url] = {}
        progress[url]["status"] = "downloading"
        progress[url]["size"] = 1
        progress[url]["downloaded"] = 0
    else:
        if progress[url]["status"] == "downloading":
            xlog.warn("url in downloading, %s", url)
            return False

    for i in range(0, 2):
        try:
            xlog.info("download %s to %s, retry:%d", url, filename, i)
            opener = get_opener(i)
            req = opener.open(url, timeout=30)
            progress[url]["size"] = int(req.headers.get('content-length') or 0)

            chunk_len = 65536
            downloaded = 0
            with open(filename, 'wb') as fp:
                while True:
                    chunk = req.read(chunk_len)
                    if not chunk:
                        break
                    fp.write(chunk)
                    downloaded += len(chunk)
                    progress[url]["downloaded"] = downloaded

            if downloaded != progress[url]["size"]:
                xlog.warn("download size:%d, need size:%d, download fail.", downloaded, progress[url]["size"])
                continue
            else:
                progress[url]["status"] = "finished"
                return True
        except (urllib2.URLError, ssl.SSLError) as e:
            xlog.warn("download %s to %s URL fail:%r", url, filename, e)
            continue
        except Exception as e:
            xlog.exception("download %s to %s fail:%r", url, filename, e)
            continue

    progress[url]["status"] = "failed"
    return False


def parse_readme_versions(readme_file):
    versions = []
    try:
        fd = open(readme_file, "r")
        lines = fd.readlines()
        p = re.compile(r'https://codeload.github.com/XX-net/XX-Net/zip/([0-9]+)\.([0-9]+)\.([0-9]+) ([0-9a-f]*)')
        for line in lines:
            m = p.match(line)
            if m:
                version = m.group(1) + "." + m.group(2) + "." + m.group(3)
                hashsum = m.group(4)
                versions.append([m.group(0), version, hashsum])
                if len(versions) == 2:
                    return versions
    except Exception as e:
        xlog.exception("xxnet_version fail:%r", e)

    raise "get_version_fail:" % readme_file


def current_version():
    readme_file = os.path.join(root_path, "version.txt")
    try:
        with open(readme_file) as fd:
            content = fd.read()
            p = re.compile(r'([0-9]+)\.([0-9]+)\.([0-9]+)')
            m = p.match(content)
            if m:
                version = m.group(1) + "." + m.group(2) + "." + m.group(3)
                return version
    except:
        xlog.warn("get_version_fail in update_from_github")

    return "get_version_fail"


def get_github_versions():
    readme_url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/update_version.txt"
    readme_target = os.path.join(download_path, "version.txt")

    if not download_file(readme_url, readme_target):
        raise IOError("get README %s fail:" % readme_url)

    versions = parse_readme_versions(readme_target)
    return versions


def get_hash_sum(version):
    versions = get_github_versions()
    for v in versions:
        if v[1] == version:
            return v[2]


def hash_file_sum(filename):
    import hashlib

    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    try:
        with open(filename, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        return hasher.hexdigest()
    except:
        return False


def overwrite(xxnet_version, xxnet_unzip_path):
    progress["update_status"] = "Over writing"
    try:
        for root, subdirs, files in os.walk(xxnet_unzip_path):
            relate_path = root[len(xxnet_unzip_path)+1:]
            target_relate_path = relate_path
            if sys.platform == 'win32':
                if target_relate_path.startswith("code\\default"):
                    target_relate_path = "code\\" + xxnet_version + relate_path[12:]
            else:
                if target_relate_path.startswith("code/default"):
                    target_relate_path = "code/" + xxnet_version + relate_path[12:]

            for subdir in subdirs:
                if relate_path == "code" and subdir == "default":
                    subdir = xxnet_version

                target_path = os.path.join(top_path, target_relate_path, subdir)
                if not os.path.isdir(target_path):
                    xlog.info("mkdir %s", target_path)
                    os.mkdir(target_path)

            for filename in files:
                src_file = os.path.join(root, filename)
                dst_file = os.path.join(top_path, target_relate_path, filename)
                if not os.path.isfile(dst_file) or hash_file_sum(src_file) != hash_file_sum(dst_file):
                    xlog.info("copy %s => %s", src_file, dst_file)
                    if sys.platform != 'win32' and os.path.isfile(dst_file):
                        st = os.stat(dst_file)
                        shutil.copy(src_file, dst_file)
                        if st.st_mode & stat.S_IEXEC:
                            os.chmod(dst_file, st.st_mode)
                    else:
                        shutil.copy(src_file, dst_file)

    except Exception as e:
        xlog.warn("update over write fail:%r", e)
        progress["update_status"] = "Over write Fail:%r" % e
        raise e
    xlog.info("update file finished.")


def download_overwrite_new_version(xxnet_version):
    global update_progress

    xxnet_url = 'https://codeload.github.com/XX-net/XX-Net/zip/%s' % xxnet_version
    xxnet_zip_file = os.path.join(download_path, "XX-Net-%s.zip" % xxnet_version)
    xxnet_unzip_path = os.path.join(download_path, "XX-Net-%s" % xxnet_version)

    progress["update_status"] = "Downloading %s" % xxnet_url
    if not download_file(xxnet_url, xxnet_zip_file):
        progress["update_status"] = "Download Fail."
        raise Exception("download xxnet zip fail:%s" % xxnet_zip_file)

    hash_sum = get_hash_sum(xxnet_version)
    if len(hash_sum) and hash_file_sum(xxnet_zip_file) != hash_sum:
        progress["update_status"] = "Download Checksum Fail."
        raise Exception("download xxnet zip checksum fail:%s" % xxnet_zip_file)

    xlog.info("update download %s finished.", download_path)

    xlog.info("update start unzip")
    progress["update_status"] = "Unziping"
    try:
        with zipfile.ZipFile(xxnet_zip_file, "r") as dz:
            dz.extractall(download_path)
            dz.close()
    except Exception as e:
        xlog.warn("unzip %s fail:%r", xxnet_zip_file, e)
        progress["update_status"] = "Unzip Fail:%s" % e
        raise e
    xlog.info("update finished unzip")

    overwrite(xxnet_version, xxnet_unzip_path)

    os.remove(xxnet_zip_file)
    shutil.rmtree(xxnet_unzip_path, ignore_errors=True)


def update_current_version(xxnet_version):
    current_version_file = os.path.join(top_path, "code", "version.txt")
    with open(current_version_file, "w") as fd:
        fd.write(xxnet_version)


def restart_xxnet(version):
    import module_init
    module_init.stop_all()
    import web_control
    web_control.stop()

    start_script = os.path.join(top_path, "code", version, "launcher", "start.py")

    subprocess.Popen([sys.executable, start_script])
    time.sleep(20)
    #os._exit(0)


def update_version(version):
    global update_progress
    try:
        download_overwrite_new_version(version)

        update_current_version(version)

        progress["update_status"] = "Restarting"
        xlog.info("update try restart xxnet")
        restart_xxnet(version)
    except Exception as e:
        xlog.warn("update version %s fail:%r", version, e)


def start_update_version(version):
    if progress["update_status"] != "Idle" and "Fail" not in progress["update_status"]:
        return progress["update_status"]

    progress["update_status"] = "Start update"
    th = threading.Thread(target=update_version, args=(version,))
    th.start()
    return True

