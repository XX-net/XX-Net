from unittest import TestCase
import os
import sys
from os.path import join
import http.client as httplib
import json
import struct
import zlib
import traceback
import requests
import logging
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

current_path = os.path.dirname(os.path.abspath(__file__))
gae_path = os.path.abspath( os.path.join(current_path, os.pardir))
default_path = os.path.abspath( os.path.join(gae_path, os.pardir))
# local_path = join(gae_path, "local")
# sys.path.append(local_path)
sys.path.append(join(default_path, "lib", "noarch"))
import utils
import xlog


skip_request_headers = frozenset([
                          b'Vary',
                          b'Via',
                          b'Proxy-Authorization',
                          b'Proxy-Connection',
                          b'Upgrade',
                          b'X-Google-Cache-Control',
                          b'X-Forwarded-For',
                          b'X-Chrome-Variations',
                          ])
skip_response_headers = frozenset([
                          # http://en.wikipedia.org/wiki/Chunked_transfer_encoding
                          b'Connection',
                          b'Upgrade',
                          b'Alt-Svc',
                          b'Alternate-Protocol',
                          b'X-Head-Content-Length',
                          b'X-Google-Cache-Control',
                          b'X-Chrome-Variations',
                          ])


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]

class Conf(object):
    GAE_PASSWORD = ""
    GAE_VALIDATE = 0
    JS_MAXSIZE = 10000
    AUTORANGE_MAXSIZE = 256000


config = Conf()


def pack_request(method, url, headers, body, kwargs):
    method = utils.to_bytes(method)
    url = utils.to_bytes(url)
    headers = utils.to_bytes(headers)
    body = utils.to_bytes(body)
    kwargs = utils.to_bytes(kwargs)
    if body:
        if len(body) < 10 * 1024 * 1024 and b'Content-Encoding' not in headers:
            # 可以压缩
            zbody = deflate(body)
            if len(zbody) < len(body):
                body = zbody
                headers[b'Content-Encoding'] = b'deflate'
        if len(body) > 10 * 1024 * 1024:
            xlog.warn("body len:%d %s %s", len(body), utils.to_bytes(method), utils.to_bytes(url))
        headers[b'Content-Length'] = utils.to_bytes(str(len(body)))

    # GAE don't allow set `Host` header
    if b'Host' in headers:
        del headers[b'Host']

    # gae 用的参数
    if config.GAE_PASSWORD:
        kwargs[b'password'] = config.GAE_PASSWORD

    # kwargs['options'] =
    kwargs[b'validate'] = config.GAE_VALIDATE
    if url.endswith(b".js"):
        kwargs[b'maxsize'] = config.JS_MAXSIZE
    else:
        kwargs[b'maxsize'] = config.AUTORANGE_MAXSIZE
    # gae 用的参数　ｅｎｄ

    payload = b'%s %s HTTP/1.1\r\n' % (method, url)
    payload += b''.join(b'%s: %s\r\n' % (k, v)
                       for k, v in list(headers.items()) if k not in skip_request_headers)
    # for k, v in headers.items():
    #    xlog.debug("Send %s: %s", k, v)
    for k, v in kwargs.items():
        if isinstance(v, int):
            payload += b'X-URLFETCH-%s: %d\r\n' % (k, v)
        else:
            payload += b'X-URLFETCH-%s: %s\r\n' % (k, utils.to_bytes(v))

    payload = deflate(payload)

    body = b'%s%s%s' % (struct.pack('!h', len(payload)), payload, body)
    request_headers = {}
    request_headers[b'Content-Length'] = str(len(body))
    # request_headers 只有上面一项

    return request_headers, body


def unpack_request(payload):
    head_len = struct.unpack('!h', payload[0:2])[0]
    print(head_len)
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

    headers = utils.to_bytes(headers)

    data = b'HTTP/1.1 %d %s\r\n%s\r\n\r\n%s' % \
           (status,
            utils.to_bytes(httplib.responses.get(status, 'Unknown')),
            b'\r\n'.join(b'%s: %s' % (k.title(), v) for k, v in headers.items()),
            app_msg)
    data = deflate(data)
    return struct.pack('!h', len(data)) + data + content


def unpack_response(body):
    try:
        data = body[:2]
        if not data:
            raise Exception(600, "get protocol head fail")

        if len(data) !=2:
            raise Exception(600, "get protocol head fail, data:%s, len:%d" % (data, len(data)))

        headers_length, = struct.unpack('!h', data)
        data = body[2:2+headers_length]
        if not data:
            raise Exception(600,
                "get protocol head fail, len:%d" % headers_length)

        raw_response_line, headers_data = inflate(data).split(b'\r\n', 1)
        rl = raw_response_line.split()
        status_code = int(rl[1])
        if len(rl) >=3:
            reason = rl[2].strip()
        else:
            reason = b""

        headers_block, app_msg = headers_data.split(b'\r\n\r\n', 1)
        headers_pairs = headers_block.split(b'\r\n')
        headers = {}
        for pair in headers_pairs:
            if not pair:
                break
            k, v = pair.split(b': ', 1)
            headers[k] = v

        content = body[2+headers_length:]
        return status_code, reason, headers, app_msg, content
    except Exception as e:
        raise Exception(600, "unpack protocol:%r at:%s" % (e, traceback.format_exc()))


class TestProtocol(TestCase):
    def test_req(self):
        method = b"POST"
        url = b"https://cloud.google.com/"
        info = {
            "req": "a",
            "type": "b"
        }
        body = utils.to_bytes(json.dumps(info))
        headers = {
            "Content-Length": str(len(body)),
            "Content-Type": "application/json"
        }
        headers = utils.to_bytes(headers)
        timeout = 30

        request_headers, payload = pack_request(method, url, headers, body, timeout)

        method1, url1, headers1, body1, timeout1, kwargs = unpack_request(payload)
        print(f"method:{method1}")
        print(f"url1:{url1}")
        print(f"headers1:{headers1}")
        print(f"body1:{body1}")
        print(f"timeout1:{timeout1}")
        print(f"kwargs:{kwargs}")

    def test_response(self):
        status = 200
        headers = {
            b"Cookie": b"abc"
        }
        content = b"ABC"
        payload = pack_response(status, headers, b"", content)

        status_code, reason, res_headers, app_msg, body = unpack_response(payload)
        self.assertEqual(status, status_code)
        # self.assertEqual(headers, res_headers)
        self.assertEqual(content, body)
        print(f"status:{status_code}")
        print(f"reason:{reason}")
        logging.debug(f"res_headers:{res_headers}")
        logger.debug(f"body:{body}")

    def test_pack_real_response(self):
        res = requests.get("https://github.com")
        status = res.status_code
        headers = dict(res.headers)
        content = res.content
        payload = pack_response(status, headers, b"", content)

        status_code, reason, res_headers, app_msg, body = unpack_response(payload)
        self.assertEqual(status, status_code)
        # self.assertEqual(headers, res_headers)
        self.assertEqual(content, body)
        print(f"status:{status_code}")
        print(f"reason:{reason}")
        print(f"res_headers:{res_headers}")
        logging.debug(f"body:{body}")

    def test_req_local(self, url="http://speedtest.ftp.otenet.gr/files/test10Mb.db"):
        method = "GET"
        body = ""
        headers = {
            # "Content-Length": str(len(body)),
            # "Content-Type": "application/json"
            "Accept-Encoding": "gzip, br"
        }
        kwargs = {
            "timeout": "30"
        }

        request_headers, payload = pack_request(method, url, headers, body, kwargs)

        res = requests.post("http://localhost:8080/_gh/", data=payload)

        status_code, reason, res_headers, app_msg, body = unpack_response(res.content)
        logging.debug(f"status:{status_code}")
        logging.debug(f"reason:{reason}")
        res_headers = utils.to_str(res_headers)
        logging.debug(f"res_headers:{json.dumps(res_headers, indent=2)}")
        logging.debug(f"body_len:{len(body)}")
        logging.debug(f"body_100:{body[:100]}")

    def test_local_req(self):
        url = "http://github.com"
        self.test_req_local(url)