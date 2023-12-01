
import time
from datetime import timedelta, datetime, tzinfo
import struct
import zlib
import logging
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import http.client as httplib

import flask
from flask import Flask, request
import requests


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)


__password__ = ''

URLFETCH_MAX = 2
# URLFETCH_MAXSIZE = 4 * 1024 * 1024
# URLFETCH_DEFLATE_MAXSIZE = 4 * 1024 * 1024
URLFETCH_TIMEOUT = 30
allowed_traffic = 1024 * 1024 * 1024 * 0.9


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

    timeout = int(kwargs.get(b"timeout", 30))
    if headers.get(b"Content-Encoding") == b"deflate":
        body = inflate(body)
        del headers[b"Content-Encoding"]

    return method, url, headers, body, timeout, kwargs


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


# def traffic(environ, start_response):
#     try:
#         # reset_date = memcache.get(key="reset_date")
#         reset_date = blobstore.get("reset_date")
#     except:
#         reset_date = None
#
#     try:
#         # traffic_sum = memcache.get(key="traffic")
#         traffic_sum = blobstore.get("traffic")
#         if not traffic_sum:
#             traffic_sum = "0"
#     except Exception as e:
#         traffic_sum = "0"
#
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     yield 'traffic:%s\r\n' % traffic_sum
#     yield 'Reset date:%s\r\n' % reset_date
#     yield 'Usage: %f %%\r\n' % int(int(traffic_sum) * 100 / allowed_traffic)
#
#     tz = Pacific()
#     sa_time = datetime.now(tz)
#     pacific_time = sa_time.strftime('%Y-%m-%d %H:%M:%S')
#     yield "American Pacific time:%s" % pacific_time
#
#     raise StopIteration


# def reset(environ, start_response):
#     try:
#         # memcache.set(key="traffic", value="0")
#         blobstore.set("traffic", "0")
#     except:
#         pass
#
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     yield 'traffic reset finished.'
#     raise StopIteration


def is_traffic_exceed():
    return False
#     try:
#         # reset_date = memcache.get(key="reset_date")
#         reset_date = blobstore.get("reset_date")
#     except:
#         reset_date = None
#
#     pacific_date = get_pacific_date()
#     if reset_date != pacific_date:
#         # memcache.set(key="reset_date", value=pacific_date)
#         # memcache.set(key="traffic", value="0")
#         blobstore.set("reset_date", pacific_date)
#         blobstore.set("traffic", "0")
#         return False
#
#     try:
#         # traffic_sum = int(memcache.get(key="traffic"))
#         traffic_sum = int(blobstore.get("traffic"))
#     except:
#         traffic_sum = 0
#
#     if traffic_sum > allowed_traffic:
#         return True
#     else:
#         return False


def count_traffic(add_traffic):
    pass
#     try:
#         # traffic_sum = int(memcache.get(key="traffic"))
#         traffic_sum = int(blobstore.get("traffic"))
#     except:
#         traffic_sum = 0
#
#     try:
#         v = str(traffic_sum + add_traffic)
#         # memcache.set(key="traffic", value=v)
#         blobstore.set("traffic", v)
#     except Exception as e:
#         logging.exception('memcache.set fail:%r', e)


@app.route("/")
def root():
    out = "GoAgent 服务端已经升级到 python3 版本。 <br>\nVersion: 4.0.0"
    return out


@app.route("/_gh/", methods=['GET'])
def check():
    logging.debug("req headers:%s", request.headers)
    return "GoAgent works"


def req_by_requests(method, url, req_headers, req_body, timeout, verify, kwargs):
    # maxsize = int(kwargs.get('maxsize', 0))
    # accept_encoding = headers.get('Accept-Encoding', '')

    errors = []
    for i in range(int(kwargs.get('fetchmax', URLFETCH_MAX))):
        try:
            res = requests.request(method, url, headers=req_headers, data=req_body, timeout=timeout, verify=verify,
                                   stream=True, allow_redirects=False)
            break
        except Exception as e:
            logging.warning("request %s %s %s %s %s e:%r", method, url, req_headers, timeout, verify, e)
            errors.append(str(e))
            if i == 0 and method == 'GET':
                timeout *= 2
    else:
        error_string = '<br />\n'.join(errors)
        logging.info('%s "%s %s" error:%s', request.remote_addr, method, url, error_string)
        return 502, {}, "502 Urlfetch Error: " + error_string

    res_headers = dict(res.headers)
    res_content = res.raw.read()
    # logging.debug(f'url={url} status_code={res.status_code} headers={res_headers} content={len(res_content)}')

    if "Transfer-Encoding" in res_headers:
        del res_headers["Transfer-Encoding"]

    res_headers["X-Head-Content-Length"] = res_headers["Content-Length"] = len(res_content)
    return res.status_code, res_headers, res_content


@app.route("/_gh/", methods=['POST'])
def proxy():
    t0 = time.time()
    try:
        method, url, req_headers, req_body, timeout, kwargs = unpack_request(request.data)
        method = to_str(method)
        url = to_str(url)
        req_headers = to_str(req_headers)
        kwargs = to_str(kwargs)
    except Exception as e:
        logging.exception("unpack request:%r", e)
        return "500 Bad Request", 500

    # logging.info('from:%s method:%s url:%s kwargs:%s -', request.remote_addr, method, url, kwargs)

    # 参数使用
    if __password__ != kwargs.get('password', ''):
        logging.info('wrong password')
        return "401 Wrong password", 401

    if is_traffic_exceed():
        logging.info('Traffic exceed')
        return "510 Traffic exceed", 510

    netloc = urlparse(url).netloc
    if netloc.startswith(('127.0.0.', '::1', 'localhost')):
        return "GoAgent is Running", 400

    timeout = int(kwargs.get('timeout', URLFETCH_TIMEOUT))
    verify = bool(int(kwargs.get('validate', 0)))

    res_code, res_headers, res_body = req_by_requests(method, url, req_headers, req_body, timeout, verify, kwargs, )
    # res_code, res_headers, res_body = req_by_urlopen(method, url, req_headers, req_body, timeout, verify, kwargs, )

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
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
