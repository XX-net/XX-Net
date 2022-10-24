# Copyright (c) 2015, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.
"""Various constant time functions for processing sensitive data"""

from __future__ import division

from .compat import compatHMAC
import hmac

def ct_lt_u32(val_a, val_b):
    """
    Returns 1 if val_a < val_b, 0 otherwise. Constant time.

    :type val_a: int
    :type val_b: int
    :param val_a: an unsigned integer representable as a 32 bit value
    :param val_b: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    val_a &= 0xffffffff
    val_b &= 0xffffffff

    return (val_a^((val_a^val_b)|(((val_a-val_b)&0xffffffff)^val_b)))>>31


def ct_gt_u32(val_a, val_b):
    """
    Return 1 if val_a > val_b, 0 otherwise. Constant time.

    :type val_a: int
    :type val_b: int
    :param val_a: an unsigned integer representable as a 32 bit value
    :param val_b: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    return ct_lt_u32(val_b, val_a)


def ct_le_u32(val_a, val_b):
    """
    Return 1 if val_a <= val_b, 0 otherwise. Constant time.

    :type val_a: int
    :type val_b: int
    :param val_a: an unsigned integer representable as a 32 bit value
    :param val_b: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    return 1 ^ ct_gt_u32(val_a, val_b)


def ct_lsb_prop_u8(val):
    """Propagate LSB to all 8 bits of the returned int. Constant time."""
    val &= 0x01
    val |= val << 1
    val |= val << 2
    val |= val << 4
    return val


def ct_lsb_prop_u16(val):
    """Propagate LSB to all 16 bits of the returned int. Constant time."""
    val &= 0x01
    val |= val << 1
    val |= val << 2
    val |= val << 4
    val |= val << 8
    return val


def ct_isnonzero_u32(val):
    """
    Returns 1 if val is != 0, 0 otherwise. Constant time.

    :type val: int
    :param val: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    val &= 0xffffffff
    return (val|(-val&0xffffffff)) >> 31


def ct_neq_u32(val_a, val_b):
    """
    Return 1 if val_a != val_b, 0 otherwise. Constant time.

    :type val_a: int
    :type val_b: int
    :param val_a: an unsigned integer representable as a 32 bit value
    :param val_b: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    val_a &= 0xffffffff
    val_b &= 0xffffffff

    return (((val_a-val_b)&0xffffffff) | ((val_b-val_a)&0xffffffff)) >> 31

def ct_eq_u32(val_a, val_b):
    """
    Return 1 if val_a == val_b, 0 otherwise. Constant time.

    :type val_a: int
    :type val_b: int
    :param val_a: an unsigned integer representable as a 32 bit value
    :param val_b: an unsigned integer representable as a 32 bit value
    :rtype: int
    """
    return 1 ^ ct_neq_u32(val_a, val_b)

def ct_check_cbc_mac_and_pad(data, mac, seqnumBytes, contentType, version,
                             block_size=16):
    """
    Check CBC cipher HMAC and padding. Close to constant time.

    :type data: bytearray
    :param data: data with HMAC value to test and padding

    :type mac: hashlib mac
    :param mac: empty HMAC, initialised with a key

    :type seqnumBytes: bytearray
    :param seqnumBytes: TLS sequence number, used as input to HMAC

    :type contentType: int
    :param contentType: a single byte, used as input to HMAC

    :type version: tuple of int
    :param version: a tuple of two ints, used as input to HMAC and to guide
        checking of padding

    :rtype: boolean
    :returns: True if MAC and pad is ok, False otherwise
    """
    assert version in ((3, 0), (3, 1), (3, 2), (3, 3))

    data_len = len(data)
    if mac.digest_size + 1 > data_len: # data_len is public
        return False

    # 0 - OK
    result = 0x00

    #
    # check padding
    #
    pad_length = data[data_len-1]
    pad_start = data_len - pad_length - 1
    pad_start = max(0, pad_start)

    if version == (3, 0): # version is public
        # in SSLv3 we can only check if pad is not longer than the cipher
        # block size

        # subtract 1 for the pad length byte
        mask = ct_lsb_prop_u8(ct_lt_u32(block_size, pad_length))
        result |= mask
    else:
        start_pos = max(0, data_len - 256)
        for i in range(start_pos, data_len):
            # if pad_start < i: mask = 0xff; else: mask = 0x00
            mask = ct_lsb_prop_u8(ct_le_u32(pad_start, i))
            # if data[i] != pad_length and "inside_pad": result = False
            result |= (data[i] ^ pad_length) & mask

    #
    # check MAC
    #

    # real place where mac starts and data ends
    mac_start = pad_start - mac.digest_size
    mac_start = max(0, mac_start)

    # place to start processing
    start_pos = max(0, data_len - (256 + mac.digest_size)) // mac.block_size
    start_pos *= mac.block_size

    # add start data
    data_mac = mac.copy()
    data_mac.update(compatHMAC(seqnumBytes))
    data_mac.update(compatHMAC(bytearray([contentType])))
    if version != (3, 0): # version is public
        data_mac.update(compatHMAC(bytearray([version[0]])))
        data_mac.update(compatHMAC(bytearray([version[1]])))
    data_mac.update(compatHMAC(bytearray([mac_start >> 8])))
    data_mac.update(compatHMAC(bytearray([mac_start & 0xff])))
    data_mac.update(compatHMAC(data[:start_pos]))

    # don't check past the array end (already checked to be >= zero)
    end_pos = data_len - mac.digest_size

    # calculate all possible
    for i in range(start_pos, end_pos): # constant for given overall length
        cur_mac = data_mac.copy()
        cur_mac.update(compatHMAC(data[start_pos:i]))
        mac_compare = bytearray(cur_mac.digest())
        # compare the hash for real only if it's the place where mac is
        # supposed to be
        mask = ct_lsb_prop_u8(ct_eq_u32(i, mac_start))
        for j in range(0, mac.digest_size): # digest_size is public
            result |= (data[i+j] ^ mac_compare[j]) & mask

    # return python boolean
    return result == 0

if hasattr(hmac, 'compare_digest'):
    ct_compare_digest = hmac.compare_digest
else:
    def ct_compare_digest(val_a, val_b):
        """Compares if string like objects are equal. Constant time."""
        if len(val_a) != len(val_b):
            return False

        result = 0
        for x, y in zip(val_a, val_b):
            result |= x ^ y

        return result == 0
