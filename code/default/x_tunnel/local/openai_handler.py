import random
import json
import base64
import time
import zlib

import utils

from . import global_var as g
from . import front_dispatcher
from . import proxy_session

from xlog import getLogger
xlog = getLogger("x_tunnel")

openai_chat_token_price = 0.000002
host = None

gzip_decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)


def get_auth_str():
    info = {
        "login_account": g.config.login_account,
        "login_password": g.config.login_password
    }
    json_str = utils.to_bytes(json.dumps(info))
    token = base64.b64encode(json_str)
    return "Bearer " + utils.to_str(token)


auth_str = None


def get_openai_proxy(get_next_one=False):
    global host
    if get_next_one or not host:

        if not (g.config.login_account and g.config.login_password):
            return False

        for _ in range(0, 3):
            res, reason = proxy_session.request_balance(g.config.login_account, g.config.login_password)
            if not res:
                xlog.warn("x-tunnel request_balance fail when create_conn:%s", reason)
                time.sleep(1)

        if not g.openai_proxies:
            return None

        host = random.choice(g.openai_proxies)
    return host


def handle_openai(method, path, headers, req_body, sock):
    global auth_str
    if not auth_str:
        auth_str = get_auth_str()

    host = get_openai_proxy()
    if not host:
        # return sock.send(b'HTTP/1.1 401 Fail\r\n\r\n')
        return 401, {}, "Service not available at current status."

    path = utils.to_str(path[7:])
    headers = utils.to_str(headers)
    headers["Authorization"] = auth_str
    del headers["Host"]
    try:
        del headers["Accept-Encoding"]
    except:
        pass
    content, status, response = front_dispatcher.request(method, host, path=path, headers=headers, data=req_body)

    if status == 200:
        try:
            if response.headers.get(b"Content-Encoding") == b"gzip":
                data = gzip_decompressor.decompress(content)
            else:
                data = content

            dat = json.loads(data)
            consumed_balance = dat["usage"]["consumed_balance"]
            g.openai_balance -= consumed_balance
        except Exception as e1:
            xlog.exception("cal tokens err:%r", e1)

    res_headers = {
        "Content-Type": "application/json"
    }
    for key, value in response.headers.items():
        if key.startswith(b"Openai"):
            res_headers[key] = value

    return status, res_headers, content
