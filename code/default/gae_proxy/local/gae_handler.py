#!/usr/bin/env python
# coding:utf-8


"""
GoAgent local-server protocol 3.2

request:
  POST /_gh/ HTTP/1.1
  HOST: appid.appspot.com
  content-length: xxx

  http content:
  此为ｂｏｄｙ
  {
    pack_req_head_len: 2 bytes,＃ＰＯＳＴ　时使用
    
    pack_req_head : deflate{
    此为负载
      original request line,
      original request headers,
      X-URLFETCH-kwargs HEADS, {
        password,
        maxsize, defined in config AUTO RANGE MAX SIZE
        timeout, request timeout for GAE urlfetch.
      }
    }
    body
  }

response:
  200 OK
  http-Heads:
    Content-type: image/gif


    headers from real_server
    # real_server 为ｇａｅ让客户端以为的服务器
    #可能被gae改变，但对客户端不可见
    #未分片ｂｏｄｙ也直接发给客户端

    # body 分为下面两部分
  http-content:{
      response_head{
        data_len: 2 bytes,
        data: deflate{
         HTTP/1.1 status, status_code
         headers
         content = error_message, if GAE server fail
        }
      }

      body
  }
"""

import errno
import time
import xstruct as struct
import re
import string
import ssl
import urllib.parse
import threading
import zlib
import traceback
from mimetypes import guess_type

from . import check_local_network
from .front import front
import utils
from xlog import getLogger
xlog = getLogger("gae_proxy")


def inflate(data):
    return zlib.decompress(data, -zlib.MAX_WBITS)


def deflate(data):
    return zlib.compress(data)[2:-4]


class GAE_Exception(Exception):
    def __init__(self, error_code, message):
        xlog.debug("GAE_Exception %r %r", error_code, message)
        self.error_code = error_code
        self.message = "%r:%s" % (error_code, message)

    def __str__(self):
        # for %s
        return repr(self.message)

    def __repr__(self):
        # for %r
        return repr(self.message)


def generate_message_html(title, banner, detail=''):
    MESSAGE_TEMPLATE = '''
    <html><head>
    <meta http-equiv="content-type" content="text/html;charset=utf-8">
    <title>$title</title>
    <style><!--
    body {font-family: arial,sans-serif}
    div.nav {margin-top: 1ex}
    div.nav A {font-size: 10pt; font-family: arial,sans-serif}
    span.nav {font-size: 10pt; font-family: arial,sans-serif; font-weight: bold}
    div.nav A,span.big {font-size: 12pt; color: #0000cc}
    div.nav A {font-size: 10pt; color: black}
    A.l:link {color: #6f6f6f}
    A.u:link {color: green}
    //--></style>
    </head>
    <body text=#000000 bgcolor=#ffffff>
    <table border=0 cellpadding=2 cellspacing=0 width=100%>
    <tr><td bgcolor=#3366cc><font face=arial,sans-serif color=#ffffff><b>Message</b></td></tr>
    <tr><td> </td></tr></table>
    <blockquote>
    <H1>$banner</H1>
    $detail
    <p>
    </blockquote>
    <table width=100% cellpadding=0 cellspacing=0><tr><td bgcolor=#3366cc><img alt="" width=1 height=4></td></tr></table>
    </body></html>
    '''
    return string.Template(MESSAGE_TEMPLATE).substitute(
        title=title, banner=banner, detail=detail)


def spawn_later(seconds, target, *args, **kwargs):
    def wrap(*args, **kwargs):
        __import__('time').sleep(seconds)
        try:
            result = target(*args, **kwargs)
        except BaseException:
            result = None
        return result
    return __import__('thread').start_new_thread(wrap, args, kwargs)


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


def send_header(wfile, keyword, value):
    keyword = keyword.title()
    if keyword == b'Set-Cookie':
        # https://cloud.google.com/appengine/docs/python/urlfetch/responseobjects
        for cookie in re.split(br', (?=[^ =]+(?:=|$))', value):
            wfile.write(b"%s: %s\r\n" % (keyword, cookie))
            #xlog.debug("Head1 %s: %s", keyword, cookie)
    elif keyword == b'Content-Disposition' and b'"' not in value:
        value = re.sub(br'filename=([^"\']+)', b'filename="\\1"', value)
        wfile.write(b"%s: %s\r\n" % (keyword, value))
        #xlog.debug("Head1 %s: %s", keyword, value)
    elif keyword in skip_response_headers:
        return
    else:
        if isinstance(value, int):
            wfile.write(b"%s: %d\r\n" % (keyword, value))
        else:
            wfile.write(b"%s: %s\r\n" % (keyword, value))
        #xlog.debug("Head1 %s: %s", keyword, value)


def send_response(wfile, status=404, headers={}, body=b''):
    body = utils.to_bytes(body)
    headers = dict((k.title(), v) for k, v in list(headers.items()))
    if b'Transfer-Encoding' in headers:
        del headers[b'Transfer-Encoding']
    if b'Content-Length' not in headers:
        headers[b'Content-Length'] = len(body)
    if b'Connection' not in headers:
        headers[b'Connection'] = b'close'

    try:
        wfile.write(b"HTTP/1.1 %d\r\n" % status)
        for key, value in list(headers.items()):
            send_header(wfile, key, value)
        wfile.write(b"\r\n")
        wfile.write(body)
    except ConnectionAbortedError as e:
        xlog.warn("gae send response fail. %r", e)
        return
    except ConnectionResetError as e:
        xlog.warn("gae send response fail: %r", e)
        return
    except BrokenPipeError as e:
        xlog.warn("gae send response fail. %r", e)
        return
    except ssl.SSLError as e:
        xlog.warn("gae send response fail. %r", e)
        return
    except Exception as e:
        xlog.exception("send response fail %r", e)


def return_fail_message(wfile):
    html = generate_message_html(
        '504 GAEProxy Proxy Time out', '连接超时，先休息一会再来！')
    send_response(wfile, 504, body=html.encode('utf-8'))
    return


def pack_request(method, url, headers, body, timeout):
    headers = dict(headers)
    if isinstance(body, bytes) and body:
        if len(body) < 10 * 1024 * 1024 and b'Content-Encoding' not in headers:
            # 可以压缩
            zbody = deflate(body)
            if len(zbody) < len(body):
                body = zbody
                headers[b'Content-Encoding'] = b'deflate'
        if len(body) > 10 * 1024 * 1024:
            xlog.warn("body len:%d %s %s", len(body), method, url)
        headers[b'Content-Length'] = utils.to_bytes(str(len(body)))

    # GAE don't allow set `Host` header
    if b'Host' in headers:
        del headers[b'Host']

    kwargs = {}
    # gae 用的参数
    if front.config.GAE_PASSWORD:
        kwargs[b'password'] = front.config.GAE_PASSWORD

    # kwargs['options'] =
    kwargs[b'validate'] = front.config.GAE_VALIDATE
    if url.endswith(b".js"):
        kwargs[b'maxsize'] = front.config.JS_MAXSIZE
    else:
        kwargs[b'maxsize'] = front.config.AUTORANGE_MAXSIZE
    kwargs[b'timeout'] = str(timeout)
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


def unpack_response(response):
    try:
        data = response.task.read(size=2)
        if not data:
            raise GAE_Exception(600, "get protocol head fail")

        if len(data) !=2:
            raise GAE_Exception(600, "get protocol head fail, data:%s, len:%d" % (data, len(data)))

        headers_length, = struct.unpack('!h', data)
        data = response.task.read(size=headers_length)
        if not data:
            raise GAE_Exception(600,
                "get protocol head fail, len:%d" % headers_length)

        raw_response_line, headers_data = inflate(data).split(b'\r\n', 1)
        rl = raw_response_line.split()
        response.app_status = int(rl[1])
        if len(rl) >=3:
            response.app_reason = rl[2].strip()

        headers_block, app_msg = headers_data.split(b'\r\n\r\n')
        headers_pairs = headers_block.split(b'\r\n')
        response.headers = {}
        for pair in headers_pairs:
            if not pair:
                break
            k, v = pair.split(b': ', 1)
            response.headers[k] = v

        response.app_msg = app_msg

        return response
    except Exception as e:
        response.worker.close("unpack protocol error")
        raise GAE_Exception(600, "unpack protocol:%r at:%s" % (e, traceback.format_exc()))


def request_gae_server(headers, body, url, timeout):
    # process on http protocol
    # process status code return by http server
    # raise error, let up layer retry.

    try:
        response = front.request(b"POST", b"", b"/_gh/", headers, body, timeout)
        if not response:
            raise GAE_Exception(600, "fetch gae fail")

        if response.status >= 600:
            raise GAE_Exception(
                response.status, "fetch gae fail:%d" % response.status)

        appid = response.ssl_sock.host.split(".")[0]
        if response.status == 404:
            # xlog.warning('APPID %r not exists, remove it.', response.ssl_sock.appid)
            front.appid_manager.report_not_exist(
                appid, response.ssl_sock.ip_str)
            # google_ip.report_connect_closed(response.ssl_sock.ip_str, "appid not exist")
            response.worker.close("appid not exist:%s" % appid)
            raise GAE_Exception(603, "appid not exist %s" % appid)

        if response.status == 503:
            xlog.warning('APPID %r out of Quota, remove it. %s',
                         appid, response.ssl_sock.ip_str)
            front.appid_manager.report_out_of_quota(appid)
            # google_ip.report_connect_closed(response.ssl_sock.ip_str, "out of quota")
            response.worker.close("appid out of quota:%s" % appid)
            raise GAE_Exception(604, "appid out of quota:%s" % appid)

        server_type = response.getheader(b"Server", b"")
        if (b"gws" not in server_type and b"Google Frontend" not in server_type and b"GFE" not in server_type) or \
                response.status == 403 or response.status == 405:

            # some ip can connect, and server type can be gws
            # but can't use as GAE server
            # so we need remove it immediately

            xlog.warn("IP:%s not support GAE, headers:%s status:%d", response.ssl_sock.ip_str, response.headers,
                      response.status)
            response.worker.close("ip not support GAE")
            raise GAE_Exception(602, "ip not support GAE")

        response.gps = response.getheader(b"x-server", b"")

        if response.status > 300:
            raise GAE_Exception(605, "status:%d" % response.status)

        if response.status != 200:
            xlog.warn("GAE %s appid:%s status:%d", response.ssl_sock.ip_str,
                      appid, response.status)

        return response
    except GAE_Exception as e:
        if e.error_code not in (600, 603, 604) and hasattr(response, "ssl_sock"):
            front.ip_manager.recheck_ip(response.ssl_sock.ip_str, first_report=False)
        raise e


def request_gae_proxy(method, url, headers, body, timeout=None):
    headers = dict(headers)
    # make retry and time out
    time_request = time.time()

    # GAE urlfetch will not decode br if Accept-Encoding include gzip
    accept_encoding = headers.get(b"Accept-Encoding", b"")
    if b"br" in accept_encoding:
        accept_br_encoding = True
        # xlog.debug("accept_br_encoding for %s", url)
    else:
        accept_br_encoding = False

    host = headers.get(b"Host", b"")
    if not host:
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.hostname

    accept_codes = accept_encoding.replace(b" ", b"").split(b",")
    try:
        accept_codes.remove(b"")
    except:
        pass

    if not accept_br_encoding:
        if b"gzip" in accept_encoding:
            if host in front.config.br_sites or host.endswith(front.config.br_endswith):
                accept_codes.remove(b"gzip")

    if b"br" not in accept_codes:
        accept_codes.append(b"br")

    accept_code_str = b",".join(accept_codes)
    if accept_code_str:
        headers[b"Accept-Encoding"] = accept_code_str
    else:
        del headers[b"Accept-Encoding"]

    error_msg = []

    if not timeout:
        timeouts = [15, 20, 30]
    else:
        timeouts = [timeout]

    if body:
        timeouts = [timeout + 10 for timeout in timeouts]

    for timeout in timeouts:
        request_headers, request_body = pack_request(method, url, headers, body, timeout)
        try:
            response = request_gae_server(request_headers, request_body, url, timeout)

            response = unpack_response(response)

            # xlog.debug("accept:%s content-encoding:%s url:%s", accept_encoding,
            #           response.headers.get("Content-Encoding", ""), url)
            if not accept_br_encoding:
                # if gzip in Accept-Encoding, br will not decode in urlfetch
                # else, urlfetch in GAE will auto decode br, but return br in Content-Encoding
                if response.headers.get(b"Content-Encoding", b"") == b"br":
                    # GAE urlfetch always return br in content-encoding even have decoded it.
                    del response.headers[b"Content-Encoding"]
                    # xlog.debug("remove br from Content-Encoding, %s", url)
                    if host not in front.config.br_sites:
                        front.config.BR_SITES.append(host)
                        front.config.save()
                        front.config.load()
                        xlog.warn("Add %s to br_sites", host)

            if response.app_msg:
                xlog.warn("server app return fail, status:%d",
                          response.app_status)
                # if len(response.app_msg) < 2048:
                # xlog.warn('app_msg:%s', cgi.escape(response.app_msg))

                if response.app_status == 510:
                    # reach 80% of traffic today
                    # disable for get big file.
                    appid = response.ssl_sock.host.split(b".")[0]
                    front.appid_manager.report_out_of_quota(appid)
                    response.worker.close(
                        "appid out of quota:%s" % appid)
                    continue

            return response
        except GAE_Exception as e:
            err_msg = "gae_exception:%r %s" % (e, url)
            error_msg.append(err_msg)
            xlog.warn("gae_exception:%r %s", e, url)
            if e.message == '605:status:500':
                raise e
        except Exception as e:
            err_msg = 'gae_handler.handler %r %s , retry...' % (e, url)
            error_msg.append(err_msg)
            xlog.exception('gae_handler.handler %r %s , retry...', e, url)

    raise GAE_Exception(600, "".join(error_msg))


def handler(method, host, url, headers, body, wfile, fallback=None):
    if not url.startswith(b"http") and not url.startswith(b"HTTP"):
        xlog.error("gae:%s", url)
        return

    request_time = time.time()

    org_headers = dict(headers)
    remove_list = []
    req_range_begin = b""
    req_range_end = b""
    req_range = b""
    for k, v in list(headers.items()):
        if v == "":
            remove_list.append(k)
            continue
        if k.lower() == b"range":
            req_range = v
            req_range_begin, req_range_end = tuple(
                x for x in re.search(br'bytes=(\d*)-(\d*)', v).group(1, 2))

    # fix bug for android market app: Mobogenie
    # GAE url_fetch refuse empty value in header.
    for key in remove_list:
        del headers[key]

    # force to get content range
    # reduce wait time
    if method == b"GET":
        if req_range_begin and not req_range_end:
            # don't known how many bytes to get, but get from begin position
            req_range_begin = int(req_range_begin)
            headers[b"Range"] = b"bytes=%d-%d" % (
                req_range_begin, req_range_begin + front.config.AUTORANGE_MAXSIZE - 1)
            xlog.debug("change Range %s => %s %s",
                       req_range, headers[b"Range"], url)
        elif req_range_begin and req_range_end:
            req_range_begin = int(req_range_begin)
            req_range_end = int(req_range_end)
            if req_range_end - req_range_begin + 1 > front.config.AUTORANGE_MAXSIZE:
                headers[b"Range"] = b"bytes=%d-%d" % (
                    req_range_begin, req_range_begin + front.config.AUTORANGE_MAXSIZE - 1)
                # remove wait time for GAE server to get knowledge that content
                # size exceed the max size per fetch
                xlog.debug("change Range %s => %s %s",
                           req_range, headers[b"Range"], url)
        elif not req_range_begin and req_range_end:
            # get the last n bytes of content
            pass
        else:
            # no begin and no end
            # don't add range, some host like github don't support Range.
            # headers["Range"] = "bytes=0-%d" % config.AUTORANGE_MAXSIZE
            pass

    try:
        response = request_gae_proxy(method, url, headers, body)
        # http://en.wikipedia.org/wiki/Chunked_transfer_encoding
        response.headers.pop(b"Transfer-Encoding", None)
        # gae代理请求
    except GAE_Exception as e:
        xlog.warn("GAE %s %s request fail:%r", method, url, e)

        if fallback and host.endswith(front.config.GOOGLE_ENDSWITH):
            return fallback()

        send_response(wfile, e.error_code, body=e.message)
        return_fail_message(wfile)
        return "ok"
    except Exception as e:
        xlog.exception("request_gae except:%r", e)
        send_response(wfile, 502, body=e.args[1]) # 502 means Gateway error.
        return_fail_message(wfile)
        return "ok"

    if response.app_msg:
        # XX-net 自己数据包
        send_response(wfile, response.app_status, body=response.app_msg)
        return "ok"
    else:
        response.status = response.app_status

    if response.status == 206:
        # use org_headers
        # RangeFetch need to known the real range end
        # 需要分片
        return RangeFetch2(method, url, org_headers,
                           body, response, wfile).run()

    response_headers = {}
    #　初始化给客户端的headers
    for key, value in list(response.headers.items()):
        key = key.title()
        if key in skip_response_headers:
            continue
        response_headers[key] = value

    response_headers[b"Persist"] = b""
    response_headers[b"Connection"] = b"Persist"

    if b'X-Head-Content-Length' in response_headers:
        if method == b"HEAD":
            response_headers[b'Content-Length'] = response_headers[b'X-Head-Content-Length']
        del response_headers[b'X-Head-Content-Length']
        # 只是获取头

    content_length = int(response.headers.get(b'Content-Length', 0))
    content_range = response.headers.get(b'Content-Range', '')
    # content_range 分片时合并用到
    if content_range and b'bytes */' not in content_range:
        start, end, length = tuple(int(x) for x in re.search(
            br'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))
    else:
        start, end, length = 0, content_length - 1, content_length
        # 未分片

    if method == b"HEAD":
        body_length = 0
    else:
        body_length = end - start + 1

    def send_response_headers():
        wfile.write(b"HTTP/1.1 %d %s\r\n" % (response.status, utils.to_bytes(response.reason)))
        for key, value in list(response_headers.items()):
            send_header(wfile, key, value)
            # xlog.debug("Head- %s: %s", key, value)
        wfile.write(b"\r\n")
        # 写入除body外内容

    def is_text_content_type(content_type):
        content_type = utils.to_bytes(content_type)
        mct, _, sct = content_type.partition(b'/')
        if mct == b'text':
            return True
        if mct == b'application':
            sct = sct.split(b';', 1)[0]
            if (sct in (b'json', b'javascript', b'x-www-form-urlencoded') or
                    sct.endswith((b'xml', b'script')) or
                    sct.startswith((b'xml', b'rss', b'atom'))):
                return True
        return False

    data0 = b""
    content_type = response_headers.get(b"Content-Type", b"")
    content_encoding = response_headers.get(b"Content-Encoding", b"")
    if body_length and \
            content_encoding == b"gzip" and \
            response.gps < b"GPS 3.3.2" and \
            is_text_content_type(content_type):
        url_guess_type = guess_type(utils.to_str(url))[0]
        if url_guess_type is None or is_text_content_type(url_guess_type):
            # try decode and detect type

            min_block = min(1024, body_length)
            data0 = response.task.read(min_block)
            if not data0 or len(data0) == 0:
                xlog.warn("recv body fail:%s", url)
                return

            gzip_decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            decoded_data0 = gzip_decompressor.decompress(data0)

            deflate_decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
            decoded_data1 = None

            if len(decoded_data0) > 1:
                CMF, FLG = bytearray(decoded_data0[:2])
                if CMF & 0x0F == 8 and CMF & 0x80 == 0 and ((CMF << 8) + FLG) % 31 == 0:
                    decoded_data1 = deflate_decompressor.decompress(decoded_data0[2:])

            if decoded_data1 is None and len(decoded_data0) > 0:
                try:
                    decoded_data1 = deflate_decompressor.decompress(decoded_data0)
                    if deflate_decompressor.unused_data != '':
                        decoded_data1 = None
                except:
                    pass

            if decoded_data1:
                try:
                    response_headers.pop(b"Content-Length", None)

                    if b"deflate" in headers.get(b"Accept-Encoding", b""):
                        # return deflate data if accept deflate
                        response_headers[b"Content-Encoding"] = b"deflate"

                        send_response_headers()
                        while True:
                            wfile.write(decoded_data0)
                            if response.task.body_readed >= body_length:
                                break
                            data = response.task.read()
                            decoded_data0 = gzip_decompressor.decompress(data)
                        xlog.info("GAE send ungziped deflate data to browser t:%d s:%d %s %s %s", (time.time() - request_time) * 1000, content_length, method,
                                  url, response.task.get_trace())

                    else:
                        # inflate data and send
                        del response_headers[b"Content-Encoding"]

                        send_response_headers()
                        while True:
                            wfile.write(decoded_data1)
                            if response.task.body_readed >= body_length:
                                break
                            data = response.task.read()
                            decoded_data0 = gzip_decompressor.decompress(data)
                            decoded_data1 = deflate_decompressor.decompress(decoded_data0)
                        xlog.info("GAE send ungziped data to browser t:%d s:%d %s %s %s", (time.time() - request_time) * 1000, content_length, method,
                                  url, response.task.get_trace())

                    return
                except Exception as e:
                    xlog.exception("gae_handler.handler try decode and send response fail. e:%r %s", e, url)
                    return

    try:
        send_response_headers()

        if data0:
            wfile.write(data0)
            body_sended = len(data0)
        else:
            body_sended = 0
    except (BrokenPipeError, ConnectionAbortedError) as e:
        return
    except Exception as e:
        xlog.exception("gae_handler.handler send response fail. e:%r %s", e, url)
        return

    while True:
        # 可能分片发给客户端
        if body_sended >= body_length:
            break

        data = response.task.read()
        if not data:
            xlog.warn("get body fail, until:%d %s",
                      body_length - body_sended, url)
            break

        body_sended += len(data)
        try:
            # https 包装
            ret = wfile.write(data)
            if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
                #xlog.debug("send to browser wfile.write ret:%d", ret)
                #ret = wfile.write(data)
                wfile.write(data)
        except BrokenPipeError as e:
            return
        except ConnectionAbortedError as e:
            return
        except Exception as e_b:
            if e_b.args[0] in (errno.ECONNABORTED, errno.EPIPE,
                          errno.ECONNRESET) or 'bad write retry' in repr(e_b):
                xlog.info('gae_handler send to browser return %r %r, len:%d, sended:%d', e_b, url, body_length, body_sended)
            else:
                xlog.info('gae_handler send to browser return %r %r', e_b, url)
            return

    # 完整一次https请求
    appid = response.ssl_sock.host.split(".")[0]
    xlog.info("GAE t:%d s:%d %s %s %s appid:%s", (time.time() - request_time) * 1000, content_length, method, url,
              response.task.get_trace(), appid)
    return "ok"


class RangeFetch2(object):

    all_data_size = {}

    def __init__(self, method, url, headers, body, response, wfile):
        self.method = method
        self.wfile = wfile
        self.url = url
        self.headers = headers
        self.body = body
        self.response = response

        self.keep_running = True
        self.blocked = False

        self.lock = threading.Lock()
        self.waiter = threading.Condition(self.lock)

        self.data_list = {}
        # begin => payload
        self.data_size = 0

        self.req_begin = 0
        self.req_end = 0
        self.wait_begin = 0

    def get_all_buffer_size(self):
        return sum(v for k, v in list(self.all_data_size.items()))

    def put_data(self, range_begin, payload):
        with self.lock:
            if range_begin < self.wait_begin:
                raise Exception("range_begin:%d expect:%d" %
                                (range_begin, self.wait_begin))

            self.data_list[range_begin] = payload
            self.data_size += len(payload)
            self.all_data_size[self] = self.data_size

            if self.wait_begin in self.data_list:
                self.waiter.notify()

    def run(self):
        req_range_begin = None
        req_range_end = None
        for k, v in list(self.headers.items()):
            # xlog.debug("range req head:%s => %s", k, v)
            if k.lower() == b"range":
                req_range_begin, req_range_end = tuple(
                    x for x in re.search(br'bytes=(\d*)-(\d*)', v).group(1, 2))
                # break

        response_headers = dict((k.title(), v)
                                for k, v in list(self.response.headers.items()))
        content_range = response_headers[b'Content-Range']
        res_begin, res_end, res_length = tuple(int(x) for x in re.search(
            br'bytes (\d+)-(\d+)/(\d+)', content_range).group(1, 2, 3))

        self.req_begin = res_end + 1
        if req_range_begin and req_range_end:
            self.req_end = int(req_range_end)
        else:
            self.req_end = res_length - 1
        self.wait_begin = res_begin

        if self.wait_begin == 0 and self.req_end == res_length - 1:
            response_headers[b'Content-Length'] = bytes(str(res_length), encoding='ascii')
            del response_headers[b'Content-Range']
            state_code = 200
        else:
            response_headers[b'Content-Range'] = b'bytes %d-%d/%d' % (
                res_begin, self.req_end, res_length)
            response_headers[b'Content-Length'] = bytes(str(
                self.req_end - res_begin + 1), encoding='ascii')
            state_code = 206

        response_headers[b"Persist"] = b""
        response_headers[b"Connection"] = b"Persist"

        xlog.info('RangeFetch %d-%d started(%r) ',
                  res_begin, self.req_end, self.url)

        try:
            self.wfile.write(b"HTTP/1.1 %d OK\r\n" % state_code)
            for key in response_headers:
                if key in skip_response_headers:
                    continue
                value = response_headers[key]
                #xlog.debug("Head %s: %s", key.title(), value)
                send_header(self.wfile, key, value)
            self.wfile.write(b"\r\n")
        except (ConnectionAbortedError, BrokenPipeError) as e:
            self.keep_running = False
            xlog.warn("RangeFetch send response fail:%r %s", e, self.url)
            return
        except Exception as e:
            self.keep_running = False
            xlog.exception("RangeFetch send response fail:%r %s", e, self.url)
            return

        data_left_to_fetch = self.req_end - self.req_begin + 1
        fetch_times = int(
            (data_left_to_fetch + front.config.AUTORANGE_MAXSIZE - 1) / front.config.AUTORANGE_MAXSIZE)
        thread_num = min(front.config.AUTORANGE_THREADS, fetch_times)
        for i in range(0, thread_num):
            threading.Thread(target=self.fetch_worker).start()

        threading.Thread(target=self.fetch, args=(
            res_begin, res_end, self.response)).start()

        ok = "ok"
        while self.keep_running and \
                (front.config.use_ipv6 == "force_ipv6" and
                check_local_network.IPv6.is_ok() or
                front.config.use_ipv6 != "force_ipv6" and
                check_local_network.is_ok()) and \
                self.wait_begin < self.req_end + 1:
            with self.lock:
                if self.wait_begin not in self.data_list:
                    self.waiter.wait()

                if self.wait_begin not in self.data_list:
                    xlog.error("get notify but no data")
                    continue
                else:
                    data = self.data_list[self.wait_begin]
                    del self.data_list[self.wait_begin]
                    self.wait_begin += len(data)
                    self.data_size -= len(data)
                    self.all_data_size[self] = self.data_size

            try:
                ret = self.wfile.write(data)
                if ret == ssl.SSL_ERROR_WANT_WRITE or ret == ssl.SSL_ERROR_WANT_READ:
                    xlog.debug(
                        "send to browser wfile.write ret:%d, retry", ret)
                    ret = self.wfile.write(data)
                    xlog.debug("send to browser wfile.write ret:%d", ret)
                del data
            except Exception as e:
                xlog.info('RangeFetch client closed(%s). %s', e, self.url)
                ok = None
                break
        self.keep_running = False
        self.all_data_size.pop(self, None)
        return ok

    def fetch_worker(self):
        blocked = False
        while self.keep_running:
            if blocked:
                time.sleep(0.5)

            with self.lock:
                # at least 2 wait workers keep running
                if self.req_begin > self.wait_begin + front.config.AUTORANGE_MAXSIZE:
                    if self.get_all_buffer_size() > front.config.AUTORANGE_MAXBUFFERSIZE * (0.8 + len(self.all_data_size) * 0.2):
                        if not self.blocked:
                            xlog.debug("fetch_worker blocked, buffer:%d %s",
                                       self.data_size, self.url)
                        self.blocked = blocked = True
                        continue
                    self.blocked = blocked = False

                if self.req_begin >= self.req_end + 1:
                    break

                begin = self.req_begin
                end = min(begin + front.config.AUTORANGE_MAXSIZE - 1, self.req_end)
                self.req_begin = end + 1

            self.fetch(begin, end, None)

    def fetch(self, begin, end, first_response):
        headers = dict((k.title(), v) for k, v in list(self.headers.items()))
        retry_num = 0
        while self.keep_running:
            retry_num += 1
            if retry_num > 20:
                xlog.warn("RangeFetch try max times, exit. %s", self.url)
                self.close()
                break

            expect_len = end - begin + 1
            headers[b'Range'] = b'bytes=%d-%d' % (begin, end)

            if first_response:
                response = first_response
            else:
                try:
                    response = request_gae_proxy(
                        self.method, self.url, headers, self.body)
                except GAE_Exception as e:
                    xlog.warning('RangeFetch %s request fail:%r',
                                 headers[b'Range'], e)
                    continue

            if response.app_msg:
                response.worker.close(
                    "range get gae status:%d" % response.app_status)
                continue

            response.status = response.app_status
            if response.headers.get(b'Location', None):
                self.url = urllib.parse.urljoin(
                    self.url, response.headers.get(b'Location'))
                xlog.warn('RangeFetch Redirect(%r) status:%s',
                          self.url, response.status)
                continue

            if response.status >= 300:
                #xlog.error('RangeFetch %r return %s :%s', self.url, response.status, cgi.escape(response.body))
                response.worker.close("range status:%s" % response.status)
                continue

            content_range = response.headers.get(b'Content-Range', b"")
            if not content_range:
                xlog.warning('RangeFetch "%s %s" return headers=%r, retry %s-%s',
                             self.method, self.url, response.headers, begin, end)
                # if len(response.body) < 2048:
                #xlog.warn('body:%s', cgi.escape(response.body))
                # response.worker.close("no range")
                continue

            content_length = int(response.headers.get(b'Content-Length', 0))

            data_readed = 0
            while True:
                if data_readed >= content_length:
                    percent = begin * 100 / self.req_end

                    xlog.debug('RangeFetch [%s] %d%% length:%s range:%s %s %s',
                               response.ssl_sock.ip_str, percent,
                               content_length, content_range, self.url, response.task.get_trace())
                    break

                data = response.task.read()
                if not data:
                    xlog.warn("RangeFetch [%s] get body fail, begin:%d %s",
                              response.ssl_sock.ip_str, begin, self.url)
                    break

                data_len = len(data)
                data_readed += data_len
                if data_len > expect_len:
                    xlog.warn("RangeFetch expect:%d, get:%d",
                              expect_len, data_len)
                    data = data[:expect_len]
                    data_len = expect_len

                self.put_data(begin, data)

                expect_len -= data_len
                begin += data_len

            if begin >= end + 1:
                break

            xlog.warn("RangeFetch get left, begin:%d end:%d", begin, end)

    def close(self):
        self.keep_running = False
        with self.lock:
            self.waiter.notify()
