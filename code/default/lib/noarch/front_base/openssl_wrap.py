
# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap SSL implementation, python 2.7 will use pyOpenSSL, python 3.x will use build in ssl.
# This can also be used to store some attribute like ip_str/appid

import sys

error_str = ""
implementation = None

def init():
    global implementation
    try:
        from .boringssl_wrap import SSLConnection, SSLContext, SSLCert
        implementation = "BoringSSL"
        return SSLConnection, SSLContext, SSLCert
    except Exception as e:
        error_str = "import boringssl except: %r;" % e

    if sys.version_info[0] == 3:
        from .ssl_wrap import SSLConnection, SSLContext, SSLCert

        implementation = "ssl, " + error_str
    else:
        from .pyopenssl_wrap import SSLConnection, SSLContext, SSLCert
        implementation = "OpenSSL, " + error_str

    return SSLConnection, SSLContext, SSLCert


SSLConnection, SSLContext, SSLCert = init()
