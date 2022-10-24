# Author:
#    Hubert Kario

"""Handling of Diffie-Hellman parameter files."""

from .utils.asn1parser import ASN1Parser
from .utils.pem import dePem
from .utils.cryptomath import bytesToNumber


def parseBinary(data):
    """
    Parse DH parameters from ASN.1 DER encoded binary string.

    :param bytes data: DH parameters
    :rtype: tuple of int
    """
    parser = ASN1Parser(data)

    prime = parser.getChild(0)
    gen = parser.getChild(1)

    return (bytesToNumber(gen.value), bytesToNumber(prime.value))


def parse(data):
    """
    Parses DH parameters from a binary string.

    The string can either by PEM or DER encoded

    :param bytes data: DH parameters
    :rtype: tuple of int
    :returns: generator and prime
    """
    try:
        return parseBinary(data)
    except (SyntaxError, TypeError):
        pass

    binData = dePem(data, "DH PARAMETERS")
    return parseBinary(binData)
