# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""OpenSSL/M2Crypto RSA implementation."""

from .cryptomath import *

from .rsakey import *
from .python_rsakey import Python_RSAKey
from .compat import compatAscii2Bytes, compat_b2a

#copied from M2Crypto.util.py, so when we load the local copy of m2
#we can still use it
def password_callback(v, prompt1='Enter private key passphrase:',
                           prompt2='Verify passphrase:'):
    from getpass import getpass
    while 1:
        try:
            p1=getpass(prompt1)
            if v:
                p2=getpass(prompt2)
                if p1==p2:
                    break
            else:
                break
        except KeyboardInterrupt:
            return None
    return p1


if m2cryptoLoaded:
    import M2Crypto

    class OpenSSL_RSAKey(RSAKey):
        def __init__(self, n=0, e=0, key_type="rsa"):
            self.rsa = None
            self._hasPrivateKey = False
            if (n and not e) or (e and not n):
                raise AssertionError()
            if n and e:
                self.rsa = m2.rsa_new()
                m2.rsa_set_n(self.rsa, numberToMPI(n))
                m2.rsa_set_e(self.rsa, numberToMPI(e))
            self.key_type = key_type

        def __del__(self):
            if self.rsa:
                m2.rsa_free(self.rsa)

        def __getattr__(self, name):
            if name == 'e':
                if not self.rsa:
                    return 0
                return mpiToNumber(m2.rsa_get_e(self.rsa))
            elif name == 'n':
                if not self.rsa:
                    return 0
                return mpiToNumber(m2.rsa_get_n(self.rsa))
            else:
                raise AttributeError

        def hasPrivateKey(self):
            return self._hasPrivateKey

        def _rawPrivateKeyOp(self, message):
            data = numberToByteArray(message, numBytes(self.n))
            string = m2.rsa_private_encrypt(self.rsa, bytes(data),
                                            m2.no_padding)
            ciphertext = bytesToNumber(bytearray(string))
            return ciphertext

        def _raw_private_key_op_bytes(self, message):
            return self._call_m2crypto(
                m2.rsa_private_encrypt, message,
                "Bad parameters to private key operation")

        def _rawPublicKeyOp(self, ciphertext):
            data = numberToByteArray(ciphertext, numBytes(self.n))
            string = m2.rsa_public_decrypt(self.rsa, bytes(data),
                                           m2.no_padding)
            message = bytesToNumber(bytearray(string))
            return message

        def _call_m2crypto(self, method, param, err_msg):
            try:
                return bytearray(method(self.rsa, bytes(param), m2.no_padding))
            except M2Crypto.RSA.RSAError:
                raise ValueError(err_msg)

        def _raw_public_key_op_bytes(self, ciphertext):
            return self._call_m2crypto(
                m2.rsa_public_decrypt, ciphertext,
                "Bad parameters to public key operation")

        def acceptsPassword(self): return True

        def write(self, password=None):
            bio = m2.bio_new(m2.bio_s_mem())
            if self._hasPrivateKey:
                if password:
                    def f(v): return password
                    m2.rsa_write_key(self.rsa, bio, m2.des_ede_cbc(), f)
                else:
                    def f(): pass
                    m2.rsa_write_key_no_cipher(self.rsa, bio, f)
            else:
                if password:
                    raise AssertionError()
                m2.rsa_write_pub_key(self.rsa, bio)
            s = m2.bio_read(bio, m2.bio_ctrl_pending(bio))
            m2.bio_free(bio)
            return s

        @staticmethod
        def generate(bits, key_type="rsa"):
            key = OpenSSL_RSAKey()
            def f():pass
            key.rsa = m2.rsa_generate_key(bits, 3, f)
            key._hasPrivateKey = True
            key.key_type = key_type
            b64_key = compat_b2a(key.write())
            py_key = Python_RSAKey.parsePEM(b64_key)
            key.d = py_key.d
            return key

        @staticmethod
        def parse(s, passwordCallback=None):
            # Skip forward to the first PEM header
            start = s.find("-----BEGIN ")
            if start == -1:
                raise SyntaxError()
            s = s[start:]            
            if s.startswith("-----BEGIN "):
                if passwordCallback==None:
                    callback = password_callback
                else:
                    def f(v, prompt1=None, prompt2=None):
                        return passwordCallback()
                    callback = f
                bio = m2.bio_new(m2.bio_s_mem())
                try:
                    m2.bio_write(bio, compatAscii2Bytes(s))
                    key = OpenSSL_RSAKey()
                    # parse SSLay format PEM file
                    if s.startswith("-----BEGIN RSA PRIVATE KEY-----"):
                        def f():pass
                        key.rsa = m2.rsa_read_key(bio, callback)
                        if key.rsa == None:
                            raise SyntaxError()
                        key._hasPrivateKey = True
                    # parse a standard PKCS#8 PEM file
                    elif s.startswith("-----BEGIN PRIVATE KEY-----"):
                        def f():pass
                        key.rsa = m2.pkey_read_pem(bio, callback)
                        # the below code assumes RSA key while PKCS#8 files
                        # (and by extension the EVP_PKEY structure) can be
                        # also DSA or EC, thus the double check against None
                        # (first if the file was properly loaded and second
                        # if the file actually has a RSA key in it)
                        # tlslite doesn't support DSA or EC so it's useless
                        # to handle them in a different way
                        if key.rsa == None:
                            raise SyntaxError()
                        key.rsa = m2.pkey_get1_rsa(key.rsa)
                        if key.rsa == None:
                            raise SyntaxError()
                        key._hasPrivateKey = True
                    elif s.startswith("-----BEGIN PUBLIC KEY-----"):
                        key.rsa = m2.rsa_read_pub_key(bio)
                        if key.rsa == None:
                            raise SyntaxError()
                        key._hasPrivateKey = False
                    else:
                        raise SyntaxError()
                    if key._hasPrivateKey:
                        b64_key = compat_b2a(key.write())
                        py_key = Python_RSAKey.parsePEM(b64_key)
                        key.d = py_key.d
                    return key
                finally:
                    m2.bio_free(bio)
            else:
                raise SyntaxError()
