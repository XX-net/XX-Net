import os
import time
from datetime import timedelta, datetime, tzinfo
import struct
import zlib
import logging
from urllib.parse import urlparse
import http.client as httplib
import json
import threading
import re

import psutil
import flask
from flask import Flask, request
import requests

from google.cloud import storage
from google.appengine.api import urlfetch
from google.appengine.runtime import apiproxy_errors
from google.appengine.api.taskqueue.taskqueue import MAX_URL_LENGTH
from google.appengine.api import urlfetch_stub
from google.appengine.api import apiproxy_stub_map

apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
try:
    storage_client = storage.Client()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    bucket_name = f"{project_id}.appspot.com"
    bucket = storage_client.bucket(bucket_name)
    blob_name = "band_usage_info"
except Exception as e:
    logging.warning("init blob fail:%r", e)
    storage_client = None

__password__ = ''

URLFETCH_MAX = 2
URLFETCH_DEFLATE_MAXSIZE = 4 * 1024 * 1024
URLFETCH_TIMEOUT = 30
allowed_traffic = 1024 * 1024 * 1024 * 0.90
gae_support_methods = tuple(["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH"])


def map_with_parameter(function, datas, args):
    plist = []
    for data in datas:
        d_out = function(data, args)
        plist.append(d_out)
    return plist


def to_bytes(data, coding='utf-8'):
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode(coding)
    if isinstance(data, dict):
        return dict(map_with_parameter(to_bytes, data.items(), coding))
    if isinstance(data, tuple):
        return tuple(map_with_parameter(to_bytes, data, coding))
    if isinstance(data, list):
        return list(map_with_parameter(to_bytes, data, coding))
    if isinstance(data, int):
        return to_bytes(str(data))
    if data is None:
        return data
    return bytes(data)


def to_str(data, coding='utf-8'):
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        return data.decode(coding)
    if isinstance(data, bytearray):
        return data.decode(coding)
    if isinstance(data, dict):
        return dict(map_with_parameter(to_str, data.items(), coding))
    if isinstance(data, tuple):
        return tuple(map_with_parameter(to_str, data, coding))
    if isinstance(data, list):
        return list(map_with_parameter(to_str, data, coding))
    if isinstance(data, int):
        return str(data)
    if data is None:
        return data
    return str(data)


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]


def unpack_request(payload):
    head_len = struct.unpack('!h', payload[0:2])[0]
    head = payload[2:2+head_len]
    body = payload[2+head_len:]

    head = inflate(head)
    lines = head.split(b"\r\n")
    method, url = lines[0].split()[:2]
    headers = {}
    kwargs = {}
    for line in lines[1:]:
        ls = line.split(b": ")
        k = ls[0]
        if not k:
            continue

        v = b"".join(ls[1:])
        if k.startswith(b"X-URLFETCH-"):
            k = k[11:]
            kwargs[k] = v
        else:
            headers[k] = v

    if headers.get(b"Content-Encoding") == b"deflate":
        body = inflate(body)
        del headers[b"Content-Encoding"]

    method = to_str(method)
    url = to_str(url)
    headers = to_str(headers)
    kwargs = to_str(kwargs)
    if method == "GET" and "Content-Length" in headers:
        del headers["Content-Length"]

    return method, url, headers, body, kwargs


def pack_response(status, headers, app_msg, content):
    if app_msg:
        headers.pop('content-length', None)
        headers['Content-Length'] = str(len(app_msg))

    headers = to_bytes(headers)

    data = b'HTTP/1.1 %d %s\r\n%s\r\n\r\n%s' % \
           (status,
            to_bytes(httplib.responses.get(status, 'Unknown')),
            b'\r\n'.join(b'%s: %s' % (k.title(), v) for k, v in headers.items()),
            app_msg)

    data = deflate(data)
    head_len_pack = struct.pack('!h', len(data))
    out = head_len_pack + data + to_bytes(content)
    return out


class Pacific(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-8) + self.dst(dt)

    def dst(self, dt):
        # DST starts last Sunday in March
        d = datetime(dt.year, 3, 12)   # ends last Sunday in October
        self.dston = d - timedelta(days=d.weekday() + 1)
        d = datetime(dt.year, 11, 6)
        self.dstoff = d - timedelta(days=d.weekday() + 1)
        if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
            return timedelta(hours=1)
        else:
            return timedelta(0)

    def tzname(self,dt):
         return "Pacific"


def get_pacific_date():
    tz = Pacific()
    sa_time = datetime.now(tz)
    return sa_time.strftime('%Y-%m-%d')


def get_store_info():
    if not storage_client:
        return {}

    try:
        blob = bucket.blob(blob_name)
        content = blob.download_as_string()
        info = json.loads(content)
        return info
    except Exception as e:
        logging.exception("get_store_info e:%r", e)
        return {}


store_info = get_store_info()
store_save_time = time.time()
store_change_time = 0
traffic = 0
timer_th = None


def get_store(key, default_value=None):
    global store_info
    return store_info.get(key, default_value)


def set_store(key, value):
    global store_info
    store_info[key] = value


def save_store():
    global store_info, store_save_time, traffic
    if not storage_client:
        return

    store_info = get_store_info()

    try:
        store_info["traffic"] = store_info.get("traffic", 0) + traffic
        traffic = 0
        content = json.dumps(store_info)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(content)

        store_save_time = time.time()
        logging.info("save_store:%s", content)
    except Exception as e:
        logging.exception("save_store e:%r", e)


def timer_worker():
    global store_info, store_save_time, store_change_time, timer_th

    time.sleep(60 * 14)
    if store_change_time > store_save_time and time.time() - store_save_time > 60:
        logging.info("timer save store")
        save_store()
    timer_th = None


@app.route("/reset_traffic", methods=['GET'])
def reset_traffic():
    global traffic
    traffic = 0
    set_store("traffic", 0)
    save_store()
    return 'Traffic reset finished.'


def is_traffic_exceed():
    global traffic
    reset_date = get_store("reset_date", None)

    pacific_date = get_pacific_date()
    if reset_date != pacific_date:
        set_store("reset_date", pacific_date)
        traffic = 0
        set_store("traffic", 0)
        save_store()
        return False

    traffic_sum = get_store("traffic", 0) + traffic

    if traffic_sum > allowed_traffic:
        return True
    else:
        return False


def count_traffic(add_traffic):
    global timer_th, traffic, store_change_time
    traffic += add_traffic
    store_change_time = time.time()

    if not timer_th:
        timer_th = threading.Thread(target=timer_worker)
        timer_th.start()


@app.route("/")
def root():
    out = "GoAgent 服务端已经升级到 python3 版本。 <br>\nVersion: 4.0.0"
    return out


@app.route("/info", methods=['GET'])
def info():
    global store_info, traffic
    save_store()

    out_list = list()
    out_list.append(f"store: <pre>{json.dumps(store_info, indent=2)}</pre>")

    traffic_sum = int(store_info.get("traffic", 0)) + traffic
    out_list.append('Usage: %f %%\r\n' % (traffic_sum * 100 / allowed_traffic))

    tz = Pacific()
    sa_time = datetime.now(tz)
    pacific_time = sa_time.strftime('%Y-%m-%d %H:%M:%S')
    out_list.append("American Pacific time:%s" % pacific_time)

    out_list.append(f"CPU num:{psutil.cpu_count()}")
    out_list.append(f"CPU percent:{psutil.cpu_percent(interval=1)}")
    mem = psutil.virtual_memory()
    out_list.append(f"Mem total:{mem.total}")
    out_list.append(f"Mem used:{mem.used}")
    out_list.append(f"Mem available:{mem.available}")
    out_list.append(f"Mem percent:{mem.percent}")
    net = psutil.net_io_counters()
    out_list.append(f"net sent:{net.bytes_sent}")
    out_list.append(f"net recv:{net.bytes_recv}")

    env = json.dumps(dict(os.environ), indent=2)
    out_list.append(f"<br>env: <pre>{env}</pre>")

    return "<br>\r\n".join(out_list)


@app.route("/_gh/", methods=['GET'])
def check():
    logging.debug("req headers:%s", request.headers)
    return "GoAgent works"


def req_by_requests(method, url, req_headers, req_body, kwargs):
    timeout = int(kwargs.get('timeout', URLFETCH_TIMEOUT))
    verify = bool(int(kwargs.get('validate', 0)))

    errors = []
    for i in range(int(kwargs.get('fetchmax', URLFETCH_MAX))):
        try:
            # t0 = time.time()
            res = requests.request(method, url, headers=req_headers, data=req_body, timeout=timeout, verify=verify,
                                   stream=True, allow_redirects=False)
            # t1 = time.time()
            # logging.info(f"cost:{t1-t0} {method} {url} res:{res.status_code}")
            break
        except Exception as e:
            logging.warning("request %s %s %s %s %s e:%r", method, url, req_headers, timeout, verify, e)
            errors.append(str(e))
            if i == 0 and method == 'GET':
                timeout *= 2
    else:
        error_string = '<br />\n'.join(errors)
        logging.info('%s %s error:%s', method, url, error_string)
        return 502, {}, "502 Urlfetch Error: " + error_string

    res_code = res.status_code
    res_headers = dict(res.headers)
    content_length = int(res_headers.get("Content-Length", 0))

    maxsize = int(kwargs.get('maxsize', URLFETCH_DEFLATE_MAXSIZE))
    if (method == "GET" and res_code == 200 and content_length and maxsize and content_length > maxsize and
            "Range" not in req_headers and
            res_headers.get('Accept-Ranges', '').lower() == 'bytes'):

        res_code = 206
        res_headers['Content-Range'] = 'bytes 0-%d/%d' % (maxsize - 1, content_length)
        res_content = res.raw.read(maxsize)
        logging.info("get %s data len:%d max:%d", url, content_length, maxsize)
    else:
        res_content = res.raw.read()

    if "Transfer-Encoding" in res_headers:
        del res_headers["Transfer-Encoding"]

    res_headers["X-Head-Content-Length"] = res_headers["Content-Length"] = len(res_content)
    return res_code, res_headers, res_content


def req_by_urlfetch(method, url, req_headers, req_body, kwargs):
    timeout = int(kwargs.get('timeout', URLFETCH_TIMEOUT))
    maxsize = int(kwargs.get('maxsize', URLFETCH_DEFLATE_MAXSIZE))
    verify = bool(int(kwargs.get('validate', 0)))

    errors = []
    allow_truncated = False
    for i in range(int(kwargs.get('fetchmax', URLFETCH_MAX))):
        try:
            t0 = time.time()

            res = urlfetch.fetch(url, req_body, method, req_headers,
                allow_truncated=allow_truncated,
                follow_redirects=False,
                deadline=timeout,
                validate_certificate=False)
            # res = requests.request(method, url, headers=req_headers, data=req_body, timeout=timeout, verify=verify,
            #                        stream=True, allow_redirects=False)
            t1 = time.time()
            logging.info(f"cost:{t1-t0} {method} {url} res:{res.status_code}")
            break

        except apiproxy_errors.OverQuotaError as e:
            logging.info('%s %s OverQuotaError:%r', method, url, e)
            return 510, {}, "510 Traffic exceed"
        except urlfetch.SSLCertificateError as e:
            errors.append('%r, should validate=0 ?' % e)
            logging.warning('%r, timeout=%s', e, timeout)

            return 502, {}, "502 SSLCertificateError"
        except urlfetch.DeadlineExceededError as e:
            errors.append('%r, timeout=%s' % (e, timeout))
            logging.warning('DeadlineExceededError(timeout=%s, url=%r)', timeout, url)
            time.sleep(1)

            allow_truncated = True
            m = re.search(r'=\s*(\d+)-', req_headers.get('Range') or req_headers.get('range') or '')
            if m is None:
                req_headers['Range'] = 'bytes=0-%d' % (maxsize)
            else:
                req_headers.pop('Range', '')
                req_headers.pop('range', '')
                start = int(m.group(1))
                req_headers['Range'] = 'bytes=%s-%d' % (start, start + maxsize)

            timeout *= 2
        except urlfetch.DownloadError as e:
            errors.append('%r, timeout=%s' % (e, timeout))
            logging.warning('DownloadError(timeout=%s, url=%r)', timeout, url)
            time.sleep(1)
            timeout *= 2
        except urlfetch.ResponseTooLargeError as e:
            errors.append('%r, timeout=%s' % (e, timeout))
            response = e.response
            logging.warning('ResponseTooLargeError(timeout=%s, url=%r) response(%r)',
                timeout, url, response)

            m = re.search(r'=\s*(\d+)-', req_headers.get('Range') or req_headers.get('range') or '')
            if m is None:
                req_headers['Range'] = 'bytes=0-%d' % (maxsize)
            else:
                req_headers.pop('Range', '')
                req_headers.pop('range', '')
                start = int(m.group(1))
                req_headers['Range'] = 'bytes=%s-%d' % (start, start + (maxsize))
            timeout *= 2
        except Exception as e:
            logging.warning("request %s %s %s %s %s e:%r", method, url, req_headers, timeout, verify, e)
            errors.append(str(e))
            if i == 0 and method == 'GET':
                timeout *= 2
    else:
        error_string = '<br />\n'.join(errors)
        logging.warning('%s %s error:%s', method, url, error_string)
        return 502, {}, "502 Urlfetch Error: " + error_string

    res_code = res.status_code
    res_headers = dict(res.headers)
    content_length = int(res_headers.get("Content-Length", 0))

    if (method == "GET" and res_code == 200 and content_length and maxsize and content_length > maxsize and
            "Range" not in req_headers and res_headers.get('Accept-Ranges', '').lower() == 'bytes'):

        res_code = 206
        res_headers['Content-Range'] = 'bytes 0-%d/%d' % (maxsize - 1, content_length)
        res_content = res.content[:maxsize]
        logging.info("get %s data len:%d max:%d", url, content_length, maxsize)
    else:
        res_content = res.content

    if "Transfer-Encoding" in res_headers:
        del res_headers["Transfer-Encoding"]

    res_headers["X-Head-Content-Length"] = res_headers["Content-Length"] = len(res_content)
    return res_code, res_headers, res_content


@app.route("/_gh/", methods=['POST'])
def proxy():
    if is_traffic_exceed():
        logging.info('Traffic exceed')
        return "510 Traffic exceed", 510

    t0 = time.time()
    try:
        method, url, req_headers, req_body, kwargs = unpack_request(request.data)
    except Exception as e:
        logging.exception("unpack request:%r", e)
        return "500 Bad Request", 500

    # logging.info('from:%s method:%s url:%s kwargs:%s -', request.remote_addr, method, url, kwargs)

    # 参数使用
    if __password__ != kwargs.get('password', ''):
        logging.info('wrong password')
        return "401 Wrong password", 401

    netloc = urlparse(url).netloc
    if netloc.startswith(('127.0.0.', '::1', 'localhost')):
        return "GoAgent is Running", 400

    if len(url) > MAX_URL_LENGTH or method not in gae_support_methods:
        res_code, res_headers, res_body = req_by_requests(method, url, req_headers, req_body, kwargs)
    else:
        res_code, res_headers, res_body = req_by_urlfetch(method, url, req_headers, req_body, kwargs)

    res_data = pack_response(res_code, res_headers, b"", res_body)
    t1 = time.time()
    cost = t1 - t0

    logging.info("cost:%f %s %s res_len:%d", cost, method, url, len(res_body))

    count_traffic(len(request.data) + len(res_data))

    resp = flask.Response(res_data)
    resp.headers['Content-Type'] = 'image/gif'
    return resp


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app.
    app.run(host="127.0.0.1", port=8080, debug=True)
