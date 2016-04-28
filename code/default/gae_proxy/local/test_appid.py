import httplib

from xlog import getLogger
xlog = getLogger("gae_proxy")

from connect_manager import https_manager


def test_appid_exist(ssl_sock, appid):
    request_data = 'GET /_gh/ HTTP/1.1\r\nHost: %s.appspot.com\r\n\r\n' % appid
    ssl_sock.send(request_data.encode())
    response = httplib.HTTPResponse(ssl_sock, buffering=True)

    response.begin()
    if response.status == 404:
        #xlog.warn("app check %s status:%d", appid, response.status)
        return False

    if response.status == 503:
        # out of quota
        return True

    if response.status != 200:
        xlog.warn("test appid %s status:%d", appid, response.status)

    content = response.read()
    if "GoAgent" not in content:
        #xlog.warn("app check %s content:%s", appid, content)
        return False

    return True

    
def test_appid(appid):
    for i in range(0, 3):
        ssl_sock = https_manager.get_new_ssl()
        if not ssl_sock:
            return True

        try:
            return test_appid_exist(ssl_sock, appid)
        except Exception as e:
            xlog.exception("check_appid %s %r", appid, e)
            continue

    return False


def test_appids(appids):
    appid_list = appids.split("|")
    fail_appid_list = []
    for appid in appid_list:
        if not test_appid(appid):
            fail_appid_list.append(appid)
        else:
            # return success if one appid is work
            # just reduce wait time
            # here can be more ui friendly.
            return []
    return fail_appid_list
