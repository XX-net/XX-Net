import warnings

from webob.compat import (
    escape,
    string_types,
    text_,
    text_type,
    )

from webob.headers import _trans_key

def html_escape(s):
    """HTML-escape a string or object

    This converts any non-string objects passed into it to strings
    (actually, using ``unicode()``).  All values returned are
    non-unicode strings (using ``&#num;`` entities for all non-ASCII
    characters).

    None is treated specially, and returns the empty string.
    """
    if s is None:
        return ''
    __html__ = getattr(s, '__html__', None)
    if __html__ is not None and callable(__html__):
        return s.__html__()
    if not isinstance(s, string_types):
        __unicode__ = getattr(s, '__unicode__', None)
        if __unicode__ is not None and callable(__unicode__):
            s = s.__unicode__()
        else:
            s = str(s)
    s = escape(s, True)
    if isinstance(s, text_type):
        s = s.encode('ascii', 'xmlcharrefreplace')
    return text_(s)

def header_docstring(header, rfc_section):
    if header.isupper():
        header = _trans_key(header)
    major_section = rfc_section.split('.')[0]
    link = 'http://www.w3.org/Protocols/rfc2616/rfc2616-sec%s.html#sec%s' % (
        major_section, rfc_section)
    return "Gets and sets the ``%s`` header (`HTTP spec section %s <%s>`_)." % (
        header, rfc_section, link)


def warn_deprecation(text, version, stacklevel):
    # version specifies when to start raising exceptions instead of warnings
    if version in ('1.2', '1.3', '1.4'):
        raise DeprecationWarning(text)
    else:
        cls = DeprecationWarning
    warnings.warn(text, cls, stacklevel=stacklevel+1)

status_reasons = {
    # Status Codes
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    308: 'Permanent Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',
    428: 'Precondition Required',
    429: 'Too Many Requests',
    451: 'Unavailable for Legal Reasons',
    431: 'Request Header Fields Too Large',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
    511: 'Network Authentication Required',
}

# generic class responses as per RFC2616
status_generic_reasons = {
    1: 'Continue',
    2: 'Success',
    3: 'Multiple Choices',
    4: 'Unknown Client Error',
    5: 'Unknown Server Error',
}

try:
    # py3.3+ have native comparison support
    from hmac import compare_digest
except ImportError: # pragma: nocover (Python 2.7.7 backported this)
    compare_digest = None

def strings_differ(string1, string2, compare_digest=compare_digest):
    """Check whether two strings differ while avoiding timing attacks.

    This function returns True if the given strings differ and False
    if they are equal.  It's careful not to leak information about *where*
    they differ as a result of its running time, which can be very important
    to avoid certain timing-related crypto attacks:

        http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf

    .. versionchanged:: 1.5
       Support :func:`hmac.compare_digest` if it is available (Python 2.7.7+
       and Python 3.3+).

    """
    len_eq = len(string1) == len(string2)
    if len_eq:
        invalid_bits = 0
        left = string1
    else:
        invalid_bits = 1
        left = string2
    right = string2

    if compare_digest is not None:
        invalid_bits += not compare_digest(left, right)
    else:
        for a, b in zip(left, right):
            invalid_bits += a != b
    return invalid_bits != 0

