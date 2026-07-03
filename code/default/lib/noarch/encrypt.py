#!/usr/bin/env python

# Copyright (c) 2014 clowwindy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import os
import sys
import hashlib
import logging as xlog


from scrypto import m2, rc4_md5, salsa20_ctr, ctypes_openssl, table


method_supported = {}
method_supported.update(rc4_md5.ciphers)
method_supported.update(salsa20_ctr.ciphers)
method_supported.update(ctypes_openssl.ciphers)
# let M2Crypto override ctypes_openssl
method_supported.update(m2.ciphers)
method_supported.update(table.ciphers)


def random_string(length):
    try:
        import M2Crypto.Rand
        return M2Crypto.Rand.rand_bytes(length)
    except ImportError:
        return os.urandom(length)


cached_keys = {}


def _get_cache_key(password):
    if isinstance(password, bytes):
        return hashlib.sha256(password).digest()
    return hashlib.sha256(password.encode('utf-8')).digest()


def try_cipher(key, method=None):
    Encryptor(key, method)


def EVP_BytesToKey(password, key_len, iv_len):
    # equivalent to OpenSSL's EVP_BytesToKey() with count 1
    # so that we make the same key and iv as nodejs version
    # NOTE: MD5 is used here per shadowsocks protocol specification,
    #       NOT a security vulnerability. Changing this would break
    #       compatibility with shadowsocks servers.
    if hasattr(password, 'encode'):
        password = password.encode('utf-8')
    cache_key = _get_cache_key(password)
    r = cached_keys.get(cache_key, None)
    if r:
        return r
    m = []
    i = 0
    while len(b''.join(m)) < (key_len + iv_len):
        md5 = hashlib.md5()
        data = password
        if i > 0:
            data = m[i - 1] + password
        md5.update(data)
        m.append(md5.digest())
        i += 1
    ms = b''.join(m)
    key = ms[:key_len]
    iv = ms[key_len:key_len + iv_len]
    cached_keys[cache_key] = (key, iv)
    return key, iv


class Encryptor(object):
    def __init__(self, key, method):
        self.key = key
        self.method = method
        self.iv = None
        self.iv_sent = False
        self.cipher_iv = b''
        self.decipher = None
        method = method.lower()
        self._method_info = self.get_method_info(method)
        if self._method_info:
            self.cipher = self.get_cipher(key, method, 1,
                                          random_string(self._method_info[1]))
        else:
            xlog.error('method %s not supported' % method)
            sys.exit(1)

    def get_method_info(self, method):
        method = method.lower()
        m = method_supported.get(method)
        if m is None and isinstance(method, str):
            m = method_supported.get(method.encode('utf-8'))
        return m

    def iv_len(self):
        return len(self.cipher_iv)

    def get_cipher(self, password, method, op, iv):
        if hasattr(password, 'encode'):
            password = password.encode('utf-8')
        m = self._method_info
        if m[0] > 0:
            key, iv_ = EVP_BytesToKey(password, m[0], m[1])
        else:
            # key_length == 0 indicates we should use the key directly
            key, iv = password, b''

        iv = iv[:m[1]]
        if op == 1:
            # this iv is for cipher not decipher
            self.cipher_iv = iv[:m[1]]
        return m[2](method, key, iv, op)

    def encrypt(self, buf):
        if len(buf) == 0:
            return buf

        if not self.iv_sent:
            head = self.cipher_iv
            self.iv_sent = True
        else:
            head = b""
        return head + self.cipher.update(buf)

    def decrypt(self, buf):
        if len(buf) == 0:
            return buf
        if self.decipher is None:
            decipher_iv_len = self._method_info[1]
            decipher_iv = buf[:decipher_iv_len]
            self.decipher = self.get_cipher(self.key, self.method, 0,
                                            iv=decipher_iv)
            buf = buf[decipher_iv_len:]
            if len(buf) == 0:
                return buf
        return self.decipher.update(buf)

def encrypt_all(password, method, op, data):
    result = []
    method = method.lower()
    (key_len, iv_len, m) = method_supported[method]
    if key_len > 0:
        key, _ = EVP_BytesToKey(password, key_len, iv_len)
    else:
        key = password
    if op:
        iv = random_string(iv_len)
        result.append(iv)
    else:
        iv = data[:iv_len]
        data = data[iv_len:]
    cipher = m(method, key, iv, op)
    result.append(cipher.update(data))
    return b''.join(result)


try:
    from crypto import RC4Cipher
except ImportError as e:
    xlog.warn('Load crypto.RC4Cipher Failed: %s, falling back to local implementation', e)
    class RC4Cipher(object):
        def __init__(self, key):
            if isinstance(key, str):
                key = key.encode('utf-8')
            x = 0
            box = list(range(256))
            for i, y in enumerate(box):
                x = (x + y + key[i % len(key)]) & 0xff
                box[i], box[x] = box[x], y
            self.__box = box
            self.__x = 0
            self.__y = 0
        def encrypt(self, data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            out = bytearray()
            x = self.__x
            y = self.__y
            box = self.__box
            for char in data:
                x = (x + 1) & 0xff
                y = (y + box[x]) & 0xff
                box[x], box[y] = box[y], box[x]
                out.append(char ^ box[(box[x] + box[y]) & 0xff])
            self.__x = x
            self.__y = y
            return bytes(out)
        def update(self, data):
            return self.encrypt(data)