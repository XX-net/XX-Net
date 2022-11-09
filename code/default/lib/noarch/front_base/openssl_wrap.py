
# this wrap has a close callback.
# Which is used by  ip manager
#  ip manager keep a connection number counter for every ip.

# the wrap SSL implementation, python 2.7 will use pyOpenSSL, python 3.x will use build in ssl.
# This can also be used to store some attribute like ip_str/appid

import sys

# if sys.version_info[0] == 3:
#     from .ssl_wrap import SSLConnection, SSLContext, SSLCert
# else:
#     from .pyopenssl_wrap import SSLConnection, SSLContext, SSLCert

try:
    from .boringssl_wrap import SSLConnection, SSLContext, SSLCert
    implementation = "BoringSSL"
except Exception as e:
    from .tlslite_wrap import SSLConnection, SSLContext, SSLCert
    implementation = "TLSLite"
