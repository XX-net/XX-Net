import os
import time
import io
import json
import zipfile
import operator

import simple_http_client
import env_info
import utils
from xlog import getLogger, reset_log_files
xlog = getLogger("x_tunnel")

from x_tunnel.local import global_var as g

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))
data_path = env_info.data_path
data_xtunnel_path = os.path.join(data_path, 'x_tunnel')


def sleep(t):
    end_time = time.time() + t
    while g.running:
        if time.time() > end_time:
            return

        sleep_time = min(10, end_time - time.time())
        if sleep_time < 0:
            break

        time.sleep(sleep_time)


def mask_x_tunnel_password(fp):
    with open(fp, "r") as fd:
        dat = json.load(fd)
        del dat["login_password"]
        dat_str = json.dumps(dat)
        return dat_str


def get_launcher_port():
    launcher_config_fn = os.path.join(data_path, "launcher", "config.json")
    try:
        with open(launcher_config_fn, "r", encoding='utf-8') as fd:
            info = json.load(fd)
            return info.get("control_port", 8085)
    except Exception as e:
        xlog.exception("get_launcher_port except:%r", e)
        return 8085


def collect_debug_and_log():
    port = get_launcher_port()

    # collect debug info and save to folders
    debug_infos = {
        "system_info": f"http://127.0.0.1:{port}/debug",
        "gae_info": f"http://127.0.0.1:{port}/module/gae_proxy/control/debug",
        "gae_log": f"http://127.0.0.1:{port}/module/gae_proxy/control/log?cmd=get_new&last_no=1",
        "xtunnel_info": f"http://127.0.0.1:{port}/module/x_tunnel/control/debug",
        "xtunnel_status": f"http://127.0.0.1:{port}/module/x_tunnel/control/status",
        "cloudflare_info": f"http://127.0.0.1:{port}/module/x_tunnel/control/cloudflare_front/debug",
        "tls_info": f"http://127.0.0.1:{port}/module/x_tunnel/control/tls_relay_front/debug",
        "seley_info": f"http://127.0.0.1:{port}/module/x_tunnel/control/seley_front/debug",
        "cloudflare_log": f"http://127.0.0.1:{port}/module/x_tunnel/control/cloudflare_front/log?cmd=get_new&last_no=1",
        "tls_log": f"http://127.0.0.1:{port}/module/x_tunnel/control/tls_relay_front/log?cmd=get_new&last_no=1",
        "seley_log": f"http://127.0.0.1:{port}/module/x_tunnel/control/seley_front/log?cmd=get_new&last_no=1",
        "xtunnel_log": f"http://127.0.0.1:{port}/module/x_tunnel/control/log?cmd=get_new&last_no=1",
        "smartroute_log": f"http://127.0.0.1:{port}/module/smart_router/control/log?cmd=get_new&last_no=1",
        "launcher_log": f"http://127.0.0.1:{port}/log?cmd=get_new&last_no=1"
    }

    download_path = os.path.join(env_info.data_path, "downloads")
    if not os.path.isdir(download_path):
        os.mkdir(download_path)

    for name, url in debug_infos.items():
        # xlog.debug("fetch %s %s", name, url)
        try:
            res = simple_http_client.request("GET", url, timeout=1)
            if name.endswith("log"):
                dat = json.loads(res.text)
                no_line = list(dat.items())
                no_line = [[int(line[0]), line[1]] for line in no_line]
                no_line = sorted(no_line, key=operator.itemgetter(0))
                lines = [line[1] for line in no_line]
                data = "".join(lines)
                data = utils.to_bytes(data)
            else:
                data = res.text

            fn = os.path.join(download_path, name + ".txt")
            with open(fn, "wb") as fd:
                fd.write(data)
        except Exception as e:
            xlog.warn("fetch info %s fail:%r", url, e)


def list_files():
    log_files = {}
    other_files = []
    for root, subdirs, files in os.walk(data_path):
        for filename in files:
            src_file = os.path.join(root, filename)

            extension = filename.split(".")[-1]
            if extension in ["json", "txt"]:
                other_files.append(src_file)

            if extension not in ["log",]:
                continue

            mtime = os.path.getmtime(src_file)
            log_files[src_file] = mtime

    # pack new log first, skip old log if size exceed.
    files = sorted(list(log_files.items()), key=operator.itemgetter(1), reverse=True)
    log_files_list = [src_file for src_file, mtime in files]

    # always pack other files(.json and .txt).
    return other_files + log_files_list


def pack_logs(max_size=10 * 1024 * 1024):
    content_size = 0

    collect_debug_and_log()

    try:
        files = list_files()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zfd:
            for src_file in files:
                file_size = os.path.getsize(src_file)
                if content_size + file_size > max_size:
                    break

                relate_path = src_file[len(data_path) + 1:]
                # xlog.debug("Add file:%s size:%d", relate_path, file_size)

                if relate_path.endswith("client.json"):
                    content = mask_x_tunnel_password(src_file)
                    zfd.writestr(relate_path, content)
                else:
                    zfd.write(src_file, arcname=relate_path)
                content_size += file_size

        compressed_data = zip_buffer.getvalue()
        xlog.debug("compress log size:%d to %d", content_size, len(compressed_data))
        return compressed_data
    except Exception as e:
        xlog.exception("packing logs except:%r", e)
        return None


def upload_logs_thread():
    sleep(g.config.delay_collect_log)
    while g.running:
        if not g.running or not g.server_host or not g.session or g.session.last_receive_time == 0:
            time.sleep(10)
        else:
            break

    sleep(g.config.delay_collect_log2)
    if not g.running:
        return

    session_id = utils.to_str(g.session.session_id)
    data = pack_logs()
    if data:
        upload(session_id, data)


def upload(session_id, data):
    try:
        content, status, response = g.http_client.request(method="POST", host=g.server_host,
                                                          path="/upload_logs?session_id=%s" % session_id,
                                                          data=data,
                                                          headers={"Content-Length": str(len(data))})

    except Exception as e:
        xlog.exception("upload logs:%r ", e)
        return

    if status != 200:
        xlog.warn("upload logs status:%r ", status)
        return

    # xlog.info("upload logs successful")
    reset_log_files()
