
import os
import sys
import urllib2
import time
import subprocess
import threading
import re
import zipfile
import shutil
import ssl

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
python_path = os.path.join(root_path, 'python27', '1.0')
noarch_lib = os.path.join(python_path, 'lib', 'noarch')
sys.path.append(noarch_lib)

from instances import xlog
import config
import update


data_root = os.path.join(root_path, 'data')
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
        p = re.compile(r'https://codeload.github.com/XX-net/XX-Net/zip/([0-9]+)\.([0-9]+)\.([0-9]+)')
        for line in lines:
            m = p.match(line)
            if m:
                version = m.group(1) + "." + m.group(2) + "." + m.group(3)
                versions.append([m.group(0), version])
                if len(versions) == 2:
                    return versions
    except Exception as e:
        xlog.exception("xxnet_version fail:%r", e)
        raise "get_version_fail:" % readme_file


def current_version():
    readme_file = os.path.join(root_path, "README.md")
    try:
        versions = parse_readme_versions(readme_file)
        return versions[0][1]
    except:
        return "get_version_fail"


def get_github_versions():
    readme_url = "https://raw.githubusercontent.com/XX-net/XX-Net/master/README.md"
    readme_target = os.path.join(download_path, "README.md")

    if not download_file(readme_url, readme_target):
        raise IOError("get README %s fail:" % readme_url)

    versions = parse_readme_versions(readme_target)
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
    global update_progress

    xxnet_url = 'https://codeload.github.com/XX-net/XX-Net/zip/%s' % xxnet_version
    xxnet_zip_file = os.path.join(download_path, "XX-Net-%s.zip" % xxnet_version)
    xxnet_unzip_path = os.path.join(download_path, "XX-Net-%s" % xxnet_version)

    progress["update_status"] = "Downloading %s" % xxnet_url
    if not download_file(xxnet_url, xxnet_zip_file):
        progress["update_status"] = "Download Fail."
        raise Exception("download xxnet zip fail:%s" % download_path)
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
        raise
    xlog.info("update finished unzip")

    progress["update_status"] = "Over writing"
    try:
        for root, subdirs, files in os.walk(xxnet_unzip_path):
            relate_path = root[len(xxnet_unzip_path)+1:]
            for subdir in subdirs:

                target_path = os.path.join(root_path, relate_path, subdir)
                if not os.path.isdir(target_path):
                    xlog.info("mkdir %s", target_path)
                    os.mkdir(target_path)

            if config.get(["update", "uuid"], '') == 'test' and "launcher" in relate_path:
                # for debug
                # don't over write launcher dir
                continue

            for filename in files:
                src_file = os.path.join(root, filename)
                dst_file = os.path.join(root_path, relate_path, filename)
                if not os.path.isfile(dst_file) or sha1_file(src_file) != sha1_file(dst_file):
                    xlog.info("copy %s => %s", src_file, dst_file)
                    shutil.copy(src_file, dst_file)

    except Exception as e:
        xlog.warn("update over write fail:%r", e)
        progress["update_status"] = "Over write Fail:%r" % e
        raise
    xlog.info("update file finished.")

    os.remove(xxnet_zip_file)
    shutil.rmtree(xxnet_unzip_path, ignore_errors=True)


def restart_xxnet():
    import module_init
    module_init.stop_all()
    import web_control
    web_control.stop()

    current_path = os.path.dirname(os.path.abspath(__file__))
    start_script = os.path.join(current_path, "start.py")

    subprocess.Popen([sys.executable, start_script])
    time.sleep(10)
    os._exit(0)


def update_version(version):
    global update_progress
    try:
        download_overwrite_new_version(version)

        progress["update_status"] = "Restarting"
        xlog.info("update try restart xxnet")
        restart_xxnet()
    except Exception as e:
        xlog.warn("update version %s fail:%r", version, e)



def start_update_version(version):
    if progress["update_status"] != "Idle" and "Fail" not in progress["update_status"]:
        return progress["update_status"]

    progress["update_status"] = "Start update"
    th = threading.Thread(target=update_version, args=(version,))
    th.start()
    return True


def clean_old_file():
    # These files moved to lib path
    # old file need remove if exist.

    def delete_file(file):
        try:
            os.remove(file)
        except:
            pass

    delete_file(os.path.join(root_path, "gae_proxy", "local", "simple_http_server.py"))
    delete_file(os.path.join(root_path, "gae_proxy", "local", "simple_http_server.pyc"))
    delete_file(os.path.join(root_path, "gae_proxy", "local", "xlog.py"))
    delete_file(os.path.join(root_path, "gae_proxy", "local", "xlog.pyc"))

clean_old_file()