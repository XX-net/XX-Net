import os
import threading
import time
import zipfile
import shutil

from update_from_github import request, xlog, hash_file_sum

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir))
top_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir))


def download_file(url, filename, sha256=None):
    org_url = url
    if os.path.isfile(filename):
        return True

    for i in range(0, 4):
        try:
            xlog.info("download %s to %s, retry:%d", url, filename, i)
            req = request(url, i, timeout=120)
            if not req:
                time.sleep(60)
                continue

            if req.status == 302:
                url = req.headers[b"Location"]
                continue

            start_time = time.time()
            timeout = 300

            if req.chunked:

                downloaded = 0
                with open(filename, 'wb') as fp:
                    while True:
                        time_left = timeout - (time.time() - start_time)
                        if time_left < 0:
                            raise Exception("time out")

                        dat = req.read(timeout=time_left)
                        if not dat:
                            break

                        fp.write(dat)
                        downloaded += len(dat)

                return True
            else:
                file_size = int(req.getheader(b'Content-Length', 0))

                left = file_size
                downloaded = 0
                with open(filename, 'wb') as fp:
                    while True:
                        chunk_len = min(65536, left)
                        if not chunk_len:
                            break

                        chunk = req.read(chunk_len)
                        if not chunk:
                            break
                        fp.write(chunk)
                        downloaded += len(chunk)
                        left -= len(chunk)

            if downloaded != file_size:
                xlog.warn("download size:%d, need size:%d, download fail.", downloaded, file_size)
                os.remove(filename)
                continue
            else:
                if sha256 and sha256 != hash_file_sum(filename):
                    xlog.warn("donwload %s checksum fail.", filename)
                    return False
                else:
                    xlog.info("download %s to %s success.", org_url, filename)
                    return True
        except Exception as e:
            xlog.exception("download %s to %s fail:%r", org_url, filename, e)
            continue
    xlog.warn("download %s fail", org_url)


def download_unzip(url, extract_path):
    if os.path.isdir(extract_path):
        return True

    data_root = os.path.join(top_path, 'data')
    download_path = os.path.join(data_root, 'downloads')
    if not os.path.isdir(download_path):
        os.mkdir(download_path)

    fn = url.split("/")[-1]
    dfn = os.path.join(download_path, fn)

    if not download_file(url, dfn):
        xlog.warn("download file %s fail.", url)
        return

    try:
        os.mkdir(extract_path)
        with zipfile.ZipFile(dfn, "r") as dz:
            dz.extractall(extract_path)
            dz.close()
        xlog.info("Extract %s to %s success.", fn, extract_path)
    except Exception as e:
        xlog.warn("unzip %s fail:%r", dfn, e)
        shutil.rmtree(extract_path)
        raise e
    os.remove(dfn)


def get_sha256(fn):
    sha256_dict = {}
    with open(fn, "r") as fd:
        for line in fd.readlines():
            if not line:
                break
            n, sha256 = line.split()[:2]
            sha256_dict[n] = sha256
        return sha256_dict


def download_worker():
    switchyomega_path = os.path.join(top_path, "SwitchyOmega")
    if not os.path.isdir(switchyomega_path):
        return

    time.sleep(150)
    sha256_fn = os.path.join(switchyomega_path, "Sha256.txt")
    download_file("https://raw.githubusercontent.com/XX-net/XX-Net/master/SwitchyOmega/Sha256.txt", sha256_fn)
    sha256_dict = get_sha256(sha256_fn)
    download_file("https://github.com/XX-net/XX-Net/releases/download/5.1.1/SwitchyOmega.zip",
                  os.path.join(switchyomega_path, "SwitchyOmega.zip"), sha256_dict.get("SwitchyOmega.zip", None))
    download_file("https://github.com/XX-net/XX-Net/releases/download/3.15.0/AutoProxy.xpi",
                  os.path.join(switchyomega_path, "AutoProxy.xpi"), sha256_dict.get("AutoProxy.xpi", None))


def start_download():
    th = threading.Thread(target=download_worker)
    th.start()
    return True
