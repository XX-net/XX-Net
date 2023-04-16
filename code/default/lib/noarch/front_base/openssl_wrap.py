
# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap SSL implementation, python 2.7 will use pyOpenSSL, python 3.x will use build in ssl.
# This can also be used to store some attribute like ip_str/appid

import sys

error_str = ""

try:
    from .pyutls_wrap import SSLConnection, SSLContext, SSLCert
    implementation = "UTLS"
except Exception as e:
    try:
        from .boringssl_wrap import SSLConnection, SSLContext, SSLCert
        implementation = "BoringSSL"
    except Exception as e:
        error_str = "import boringssl except: %r;" % e

        try:
            from .tlslite_wrap import SSLConnection, SSLContext, SSLCert
            implementation = "TLSLite, import boringssl except:" + error_str
        except Exception as e:
            error_str += "import tlslite except: %r;" % e

            if sys.version_info[0] == 3:
                from .ssl_wrap import SSLConnection, SSLContext, SSLCert

                implementation = "ssl, import tlslite except:" + error_str
            else:
                from .pyopenssl_wrap import SSLConnection, SSLContext, SSLCert
                implementation = "OpenSSL, import tlslite except:" + error_str
