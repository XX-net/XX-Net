# Copyright (c) 2017 Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.

"""Utilities for handling DNS hostnames"""

import re


def is_valid_hostname(hostname):
    """
    Check if the parameter is a valid hostname.

    :type hostname: str or bytearray
    :param hostname: string to check
    :rtype: boolean
    """
    try:
        if not isinstance(hostname, str):
            hostname = hostname.decode('ascii', 'strict')
    except UnicodeDecodeError:
        return False
    if hostname[-1] == ".":
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]
    # the maximum length of the domain name is 255 bytes, but because they
    # are encoded as labels (which is a length byte and an up to 63 character
    # ascii string), you change the dots to the length bytes, but the
    # host element of the FQDN doesn't start with a dot and the name doesn't
    # end with a dot (specification of a root label), we need to subtract 2
    # bytes from the 255 byte maximum when looking at dot-deliminated FQDN
    # with the trailing dot removed
    # see RFC 1035
    if len(hostname) > 253:
        return False

    # must not be all-numeric, so that it can't be confused with an ip-address
    if re.match(r"[\d.]+$", hostname):
        return False

    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))
