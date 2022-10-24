# Author: Trevor Perrin
# See the LICENSE file for legal information regarding use of this file.

"""Pure-Python AES implementation."""

from .aes import AES
from .rijndael import Rijndael
from .cryptomath import bytesToNumber, numberToByteArray

__all__ = ['new', 'Python_AES']


def new(key, mode, IV):
    # IV argument name is a part of the interface
    # pylint: disable=invalid-name
    if mode == 2:
        return Python_AES(key, mode, IV)
    elif mode == 6:
        return Python_AES_CTR(key, mode, IV)
    else:
        raise NotImplementedError()


class Python_AES(AES):
    def __init__(self, key, mode, IV):
        # IV argument/field names are a part of the interface
        # pylint: disable=invalid-name
        key, IV = bytearray(key), bytearray(IV)
        super(Python_AES, self).__init__(key, mode, IV, "python")
        self.rijndael = Rijndael(key, 16)
        self.IV = IV

    def encrypt(self, plaintext):
        super(Python_AES, self).encrypt(plaintext)

        plaintextBytes = bytearray(plaintext)
        chainBytes = self.IV[:]

        #CBC Mode: For each block...
        for x in range(len(plaintextBytes)//16):

            #XOR with the chaining block
            blockBytes = plaintextBytes[x*16 : (x*16)+16]
            for y in range(16):
                blockBytes[y] ^= chainBytes[y]

            #Encrypt it
            encryptedBytes = self.rijndael.encrypt(blockBytes)

            #Overwrite the input with the output
            for y in range(16):
                plaintextBytes[(x*16)+y] = encryptedBytes[y]

            #Set the next chaining block
            chainBytes = encryptedBytes

        self.IV = chainBytes[:]
        return plaintextBytes

    def decrypt(self, ciphertext):
        super(Python_AES, self).decrypt(ciphertext)

        ciphertextBytes = ciphertext[:]
        chainBytes = self.IV[:]

        #CBC Mode: For each block...
        for x in range(len(ciphertextBytes)//16):

            #Decrypt it
            blockBytes = ciphertextBytes[x*16 : (x*16)+16]
            decryptedBytes = self.rijndael.decrypt(blockBytes)

            #XOR with the chaining block and overwrite the input with output
            for y in range(16):
                decryptedBytes[y] ^= chainBytes[y]
                ciphertextBytes[(x*16)+y] = decryptedBytes[y]

            #Set the next chaining block
            chainBytes = blockBytes

        self.IV = chainBytes[:]
        return ciphertextBytes


class Python_AES_CTR(AES):
    def __init__(self, key, mode, IV):
        super(Python_AES_CTR, self).__init__(key, mode, IV, "python")
        self.rijndael = Rijndael(key, 16)
        self.IV = IV
        self._counter_bytes = 16 - len(self.IV)
        self._counter = self.IV + bytearray(b'\x00' * self._counter_bytes)

    @property
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, ctr):
        self._counter = ctr

    def _counter_update(self):
        counter_int = bytesToNumber(self._counter) + 1
        self._counter = numberToByteArray(counter_int, 16)
        if self._counter_bytes > 0 and \
                self._counter[-self._counter_bytes:] == \
                bytearray(b'\xff' * self._counter_bytes):
            raise OverflowError("CTR counter overflowed")

    def encrypt(self, plaintext):

        mask = bytearray()
        while len(mask) < len(plaintext):
            mask += self.rijndael.encrypt(self._counter)
            self._counter_update()
        inp_bytes = bytearray(i ^ j for i, j in zip(plaintext, mask))
        return inp_bytes

    def decrypt(self, ciphertext):
        return self.encrypt(ciphertext)
