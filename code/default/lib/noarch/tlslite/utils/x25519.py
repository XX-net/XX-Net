# Authors:
#   Hubert Kario (2017)
#
# See the LICENSE file for legal information regarding use of this file.

"""Handling X25519 and X448 curve based key agreement protocol."""

from .cryptomath import bytesToNumber, numberToByteArray, divceil
# the names of the variables come directly from RFC 7748 so changing them
# would make the code harder to audit/compare
# pylint: disable=invalid-name


def decodeUCoordinate(u, bits):
    """Function to decode the public U coordinate of X25519-family curves."""
    if bits not in (255, 448):
        raise ValueError("Invalid number of expected bits")
    if bits % 8:
        u[-1] &= (1 << (bits % 8)) - 1
    return bytesToNumber(u, endian="little")


def decodeScalar22519(k):
    """Function to decode the private K parameter of the x25519 function."""
    k[0] &= 248
    k[31] &= 127
    k[31] |= 64
    return bytesToNumber(k, endian="little")


def decodeScalar448(k):
    """Function to decode the private K parameter of the X448 function."""
    k[0] &= 252
    k[55] |= 128
    return bytesToNumber(k, endian="little")


def cswap(swap, x_2, x_3):
    """Conditional swap function."""
    if swap:
        return x_3, x_2
    else:
        return x_2, x_3


X25519_G = numberToByteArray(9, 32, endian="little")


X25519_ORDER_SIZE = 32


def x25519(k, u):
    """
    Perform point multiplication on X25519 curve.

    :type k: bytearray
    :param k: random secret value (multiplier), should be 32 byte long

    :type u: bytearray
    :param u: curve generator or the other party key share

    :rtype: bytearray
    """
    bits = 255
    k = decodeScalar22519(k)
    u = decodeUCoordinate(u, bits)

    a24 = 121665
    p = 2**255 - 19

    return _x25519_generic(k, u, bits, a24, p)


X448_G = numberToByteArray(5, 56, endian="little")


X448_ORDER_SIZE = 56


def x448(k, u):
    """
    Perform point multiplication on X448 curve.

    :type k: bytearray
    :param k: random secret value (multiplier), should be 56 bytes long

    :type u: bytearray
    :param u: curve generator or the other party key share

    :rtype: bytearray
    """
    bits = 448
    k = decodeScalar448(k)
    u = decodeUCoordinate(u, bits)

    a24 = 39081
    p = 2**448 - 2**224 - 1

    return _x25519_generic(k, u, bits, a24, p)


def _x25519_generic(k, u, bits, a24, p):
    """Generic Montgomery ladder implementation of the x25519 algorithm."""
    x_1 = u
    x_2 = 1
    z_2 = 0
    x_3 = u
    z_3 = 1
    swap = 0

    for t in range(bits-1, -1, -1):
        k_t = (k >> t) & 1
        swap ^= k_t
        x_2, x_3 = cswap(swap, x_2, x_3)
        z_2, z_3 = cswap(swap, z_2, z_3)
        swap = k_t

        A = (x_2 + z_2) % p
        AA = pow(A, 2, p)
        B = (x_2 - z_2) % p
        BB = pow(B, 2, p)
        E = (AA - BB) % p
        C = (x_3 + z_3) % p
        D = (x_3 - z_3) % p
        DA = (D * A) % p
        CB = (C * B) % p
        x_3 = pow(DA + CB, 2, p)
        z_3 = (x_1 * pow(DA - CB, 2, p)) % p
        x_2 = (AA * BB) % p
        z_2 = (E * (AA + a24 * E)) % p

    x_2, x_3 = cswap(swap, x_2, x_3)
    z_2, z_3 = cswap(swap, z_2, z_3)
    ret = (x_2 * pow(z_2, p - 2, p)) % p
    return numberToByteArray(ret, divceil(bits, 8), endian="little")
# pylint: enable=invalid-name
