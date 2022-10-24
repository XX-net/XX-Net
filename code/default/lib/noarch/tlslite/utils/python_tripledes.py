#################################################
#               Documentation                   #
#################################################

# Author:   Todd Whiteman
# Date:     16th March, 2009
# Verion:   2.0.0
# License:  Public Domain - free to do as you wish
# Homepage: http://twhiteman.netfirms.com/Des.html
#
# Modified by: Adam Varga, 2018
#
# A pure python implementation of the DES and Triple DES
# encryption algorithms using CBC mode. Triple DES class is
# implemented by utilising the DES base. Triple DES is
# DES-EDE3 with a 24 byte key, or DES-EDE2 with a 16 byte key.

"""
Class initialization
--------------------
pyDes.Des(key, iv)
pyDes.Python_TripleDES(key, iv)

key -> Bytes containing the encryption key. 8 bytes for DES, 16 or 24 bytes
       for Triple DES
iv  -> Initialization Vector in bytes. Length must be 8 bytes.
"""

import sys
import warnings

# PY_VER is used to handle Python2 and Python3 differences.
PY_VER = sys.version_info


def new(key, iv):
    """Operate this 3DES cipher."""

    return Python_TripleDES(key, iv)


class _baseDes(object):
    """The base class shared by DES and triple DES."""

    def __init__(self, iv):
        self.iv = iv

    def _guard_against_unicode(self, data):
        """Check the data for valid datatype and return them.

        Only accept byte strings or ascii unicode values.
        Otherwise there is no way to correctly decode the data into bytes.
        """

        if PY_VER < (3, ):
            if isinstance(data, unicode):
                raise ValueError("Only bytes, bytearray or memoryview "
                                 "objects of them should be passed, "
                                 "not Unicode strings")
        else:
            if isinstance(data, str):
                warnings.warn("Only bytes, bytearray or memoryview "
                              "objects of them should be passed",
                              DeprecationWarning,
                              stacklevel=3)
                # Only accept ascii unicode values.
                try:
                    return data.encode('ascii')
                except UnicodeEncodeError:
                    raise ValueError("The Unicode string shouldn't be passed")
        return data

#############################################
#                   DES                     #
#############################################


class Des(_baseDes):
    """DES encryption/decryption class.

    Supports CBC (Cypher Block Chaining) mode.
    """

    # Permutation and translation tables for DES
    __pc1 = [56, 48, 40, 32, 24, 16, 8,
             0, 57, 49, 41, 33, 25, 17,
             9, 1, 58, 50, 42, 34, 26,
             18, 10, 2, 59, 51, 43, 35,
             62, 54, 46, 38, 30, 22, 14,
             6, 61, 53, 45, 37, 29, 21,
             13, 5, 60, 52, 44, 36, 28,
             20, 12, 4, 27, 19, 11, 3]

    # Number left rotations of pc1
    __left_rotations = [1, 1, 2, 2, 2, 2, 2, 2,
                        1, 2, 2, 2, 2, 2, 2, 1]

    # Permuted choice key (table 2)
    __pc2 = [13, 16, 10, 23, 0, 4,
             2, 27, 14, 5, 20, 9,
             22, 18, 11, 3, 25, 7,
             15, 6, 26, 19, 12, 1,
             40, 51, 30, 36, 46, 54,
             29, 39, 50, 44, 32, 47,
             43, 48, 38, 55, 33, 52,
             45, 41, 49, 35, 28, 31]

    # Initial permutation IP
    __ip = [57, 49, 41, 33, 25, 17, 9, 1,
            59, 51, 43, 35, 27, 19, 11, 3,
            61, 53, 45, 37, 29, 21, 13, 5,
            63, 55, 47, 39, 31, 23, 15, 7,
            56, 48, 40, 32, 24, 16, 8, 0,
            58, 50, 42, 34, 26, 18, 10, 2,
            60, 52, 44, 36, 28, 20, 12, 4,
            62, 54, 46, 38, 30, 22, 14, 6]

    # Expansion table for turning 32 bit blocks into 48 bits
    __expansion_table = [31, 0, 1, 2, 3, 4,
                         3, 4, 5, 6, 7, 8,
                         7, 8, 9, 10, 11, 12,
                         11, 12, 13, 14, 15, 16,
                         15, 16, 17, 18, 19, 20,
                         19, 20, 21, 22, 23, 24,
                         23, 24, 25, 26, 27, 28,
                         27, 28, 29, 30, 31, 0]

    # The (in)famous S-boxes
    __sbox = [  # S1
              [14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
               0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
               4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
               15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 3, 14, 10, 0, 6, 13],

              # S2
              [15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
               3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
               0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
               13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9],

              # S3
              [10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
               13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
               13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
               1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12],

              # S4
              [7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
               13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
               10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
               3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14],

              # S5
              [2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
               14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
               4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
               11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3],

              # S6
              [12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
               10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
               9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
               4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13],

              # S7
              [4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
               13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
               1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
               6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12],

              # S8
              [13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
               1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
               7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
               2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11], ]

    # 32-bit permutation function P used on the output of the S-boxes
    __p = [15, 6, 19, 20, 28, 11,
           27, 16, 0, 14, 22, 25,
           4, 17, 30, 9, 1, 7,
           23, 13, 31, 26, 2, 8,
           18, 12, 29, 5, 21, 10,
           3, 24]

    # Final permutation IP^-1
    __fp = [39, 7, 47, 15, 55, 23, 63, 31,
            38, 6, 46, 14, 54, 22, 62, 30,
            37, 5, 45, 13, 53, 21, 61, 29,
            36, 4, 44, 12, 52, 20, 60, 28,
            35, 3, 43, 11, 51, 19, 59, 27,
            34, 2, 42, 10, 50, 18, 58, 26,
            33, 1, 41, 9, 49, 17, 57, 25,
            32, 0, 40, 8, 48, 16, 56, 24]

    # Type of crypting being done
    ENCRYPT = 0x00
    DECRYPT = 0x01

    # Initialisation
    def __init__(self, key, iv=None):
        # Sanity checking of arguments
        if len(key) != 8:
            raise ValueError("Invalid DES key size. Key must be exactly "
                             "8 bytes long")
        super(Des, self).__init__(iv)

        self.key_size = 8
        self._l = []
        self._r = []
        self._kn = [[0] * 48] * 16  # 16 48-bit keys (K1 - K16)
        self._final = []

        self.set_key(key)

    def set_key(self, key):
        """Set the crypting key for this object. Must be 8 bytes."""

        self.key = key
        self.__create_sub_keys()

    def __string_to_bitlist(self, data):
        """Turn the string data into a list of bits (1, 0)'s."""

        if PY_VER < (3, ):
            # Turn the strings into integers. Python 3 uses a bytes
            # class, which already has this behaviour
            if not isinstance(data, bytearray):
                data = [ord(c) for c in data]
        len_data = len(data) * 8
        result = [0] * len_data
        pos = 0
        for ch in data:
            i = 7
            while i >= 0:
                if ch & (1 << i) != 0:
                    result[pos] = 1
                else:
                    result[pos] = 0
                pos += 1
                i -= 1
        return result

    def __bitlist_to_string(self, data):
        """Turn the data as list of bits into a string."""

        result = []
        pos = 0
        c = 0
        while pos < len(data):
            c += data[pos] << (7 - (pos % 8))
            if (pos % 8) == 7:
                result.append(c)
                c = 0
            pos += 1

        if PY_VER < (3, ):
            return ''.join([chr(c) for c in result])
        else:
            return bytes(result)

    def __permutate(self, table, block):
        """Permutate this block with the specified table."""
        return [block[x] for x in table]

    def __create_sub_keys(self):
        """Transform the secret key for data processing.

        Create the 16 subkeys k[1] to k[16] from the given key.
        """
        key = self.__permutate(Des.__pc1,
                               self.__string_to_bitlist(self.key))
        # Split into Left and Right sections
        self._l = key[:28]
        self._r = key[28:]
        for i in range(16):
            # Perform circular left shifts
            for _ in range(Des.__left_rotations[i]):
                self._l.append(self._l[0])
                del self._l[0]
                self._r.append(self._r[0])
                del self._r[0]

            # Create one of the 16 subkeys through pc2 permutation
            self._kn[i] = self.__permutate(Des.__pc2, self._l + self._r)

    def __des_crypt(self, block, crypt_type):
        """Crypt the block of data through DES bit-manipulation."""

        block = self.__permutate(Des.__ip, block)
        self._l = block[:32]
        self._r = block[32:]

        # Encryption starts from _kn[1] through to _kn[16]
        if crypt_type == Des.ENCRYPT:
            iteration = 0
            iteration_adjustment = 1
        # Decryption starts from _kn[16] down to _kn[1]
        else:
            iteration = 15
            iteration_adjustment = -1

        for _ in range(16):
            # Make a copy of _r[i-1], this will later become _l[i]
            temp_r = self._r[:]

            # Permutate _r[i - 1] to start creating _r[i]
            self._r = self.__permutate(Des.__expansion_table, self._r)

            # Exclusive or _r[i - 1] with k[i], create b[1] to b[8] whilst here
            self._r = [x ^ y for x, y in zip(self._r, self._kn[iteration])]
            b = [self._r[:6], self._r[6:12], self._r[12:18], self._r[18:24],
                 self._r[24:30], self._r[30:36], self._r[36:42], self._r[42:]]

            # Permutate b[1] to b[8] using the S-Boxes
            bn = [0] * 32
            pos = 0
            for j in range(8):
                # Work out the offsets
                m = (b[j][0] << 1) + b[j][5]
                n = (b[j][1] << 3) + (b[j][2] << 2) + (b[j][3] << 1) + b[j][4]

                # Find the permutation value
                v = Des.__sbox[j][(m << 4) + n]

                # Turn value into bits, add it to result: bn
                bn[pos] = (v & 8) >> 3
                bn[pos + 1] = (v & 4) >> 2
                bn[pos + 2] = (v & 2) >> 1
                bn[pos + 3] = v & 1

                pos += 4

            # Permutate the concatination of b[1] to b[8] (bn)
            self._r = self.__permutate(Des.__p, bn)

            # Xor with _l[i - 1]
            self._r = [x ^ y for x, y in zip(self._r, self._l)]
            self._l = temp_r

            iteration += iteration_adjustment

        # Final permutation of _r[16]_l[16]
        self._final = self.__permutate(Des.__fp, self._r + self._l)
        return self._final

    def crypt(self, data, crypt_type):
        """Crypt the data in blocks, running it through des_crypt()."""

        iv = self.__string_to_bitlist(self.iv)

        # Split the data into blocks, crypting each one seperately
        i = 0
        result = []
        while i < len(data):
            # Test code for caching encryption results
            block = self.__string_to_bitlist(data[i:i+8])

            # Xor with iv if using CBC mode
            if crypt_type == Des.ENCRYPT:
                block = [x ^ y for x, y in zip(block, iv)]

            processed_block = self.__des_crypt(block, crypt_type)

            if crypt_type == Des.DECRYPT:
                processed_block = [x ^ y for x, y in zip(processed_block, iv)]
                iv = block
            else:
                iv = processed_block

            # Add the resulting crypted block to our list
            result.append(self.__bitlist_to_string(processed_block))
            i += 8

        # Return the full crypted string
        return b''.join(result)

#############################################
#               Triple DES                  #
#############################################


class Python_TripleDES(_baseDes):
    """Triple DES encryption/decrytpion class.

    This algorithm uses the DES-EDE3 (when a 24 byte key is supplied) or
    the DES-EDE2 (when a 16 byte key is supplied) encryption methods.
    Supports CBC (Cypher Block Chaining) mode.
    """
    def __init__(self, key, iv=None):
        self.block_size = 8
        if iv:
            if len(iv) != self.block_size:
                raise ValueError("Invalid Initialization Vector (iv) must be"
                                 " {0} bytes long".format(self.block_size))
            iv = self._guard_against_unicode(iv)
        else:
            raise ValueError("Initialization Vector (iv) must be supplied")

        super(Python_TripleDES, self).__init__(iv)

        # Will set crypting key for this object. Either 16/24 bytes long.
        self.key_size = len(key)
        if self.key_size not in (16, 24):
            raise ValueError("Invalid triple DES key size. "
                             "Key must be either 16 or 24 bytes long")
        key = self._guard_against_unicode(key)

        self.__key1 = Des(key[:8], self.iv)
        self.__key2 = Des(key[8:16], self.iv)
        if self.key_size == 16:
            self.__key3 = Des(key[:8], self.iv)
        else:
            self.__key3 = Des(key[16:], self.iv)

        self.isAEAD = False
        self.isBlockCipher = True
        self.name = "3des"
        self.implementation = "python"

        self.__key1.iv = self.iv
        self.__key2.iv = self.iv
        self.__key3.iv = self.iv

    def encrypt(self, data):
        """Encrypt data and return bytes.

        data : bytes to be encrypted

        The data must be a multiple of 8 bytes and will be encrypted
        with the already specified key.
        """

        ENCRYPT = Des.ENCRYPT
        DECRYPT = Des.DECRYPT

        if not data:
            return bytearray(b'')

        data = self._guard_against_unicode(data)
        if len(data) % self.block_size:
            raise ValueError("Invalid data length, must be a multiple "
                             "of {0} bytes".format(self.block_size))

        i = 0
        result = []
        while i < len(data):
            block = self.__key1.crypt(data[i:i+8], ENCRYPT)
            block = self.__key2.crypt(block, DECRYPT)
            block = self.__key3.crypt(block, ENCRYPT)
            self.__key1.iv = block
            self.__key2.iv = block
            self.__key3.iv = block
            result.append(block)
            i += 8

        return bytearray(b''.join(result))

    def decrypt(self, data):
        """Decrypt data and return bytes.

        data : bytes to be encrypted

        The data must be a multiple of 8 bytes and will be decrypted
        with the already specified key.
        """
        ENCRYPT = Des.ENCRYPT
        DECRYPT = Des.DECRYPT

        if not data:
            return bytearray(b'')

        data = self._guard_against_unicode(data)
        if len(data) % self.block_size:
            raise ValueError("Invalid data length, must be a multiple "
                             "of {0} bytes".format(self.block_size))

        i = 0
        result = []
        while i < len(data):
            iv = data[i:i+8]
            block = self.__key3.crypt(iv, DECRYPT)
            block = self.__key2.crypt(block, ENCRYPT)
            block = self.__key1.crypt(block, DECRYPT)
            self.__key1.iv = iv
            self.__key2.iv = iv
            self.__key3.iv = iv
            result.append(block)
            i += 8
        data = b''.join(result)

        return bytearray(data)
