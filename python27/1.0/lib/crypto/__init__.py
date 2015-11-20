# -*- coding: utf-8 -*-

# Copyright (c) 2011 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Package implementing cryptography related functionality.
"""

from __future__ import unicode_literals

import random
import base64

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtGui import QLineEdit, QInputDialog

from E5Gui import E5MessageBox

import Preferences

###############################################################################
## password handling functions below
###############################################################################


EncodeMarker = "CE4"
CryptoMarker = "CR5"

Delimiter = "$"

MasterPassword = None


def pwEncode(pw):
    """
    Module function to encode a password.

    @param pw password to encode (string)
    @return encoded password (string)
    """
    pop = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" \
          ".,;:-_!$?*+#"
    rpw = "".join(random.sample(pop, 32)) + pw + \
        "".join(random.sample(pop, 32))
    return EncodeMarker + base64.b64encode(rpw.encode("utf-8")).decode("ascii")


def pwDecode(epw):
    """
    Module function to decode a password.

    @param epw encoded password to decode (string)
    @return decoded password (string)
    """
    if not epw.startswith(EncodeMarker):
        return epw  # it was not encoded using pwEncode

    return base64.b64decode(epw[3:].encode("ascii"))[32:-32].decode("utf-8")


def __getMasterPassword():
    """
    Private module function to get the password from the user.
    """
    global MasterPassword

    pw, ok = QInputDialog.getText(
        None,
        QCoreApplication.translate("Crypto", "Master Password"),
        QCoreApplication.translate("Crypto", "Enter the master password:"),
        QLineEdit.Password)
    if ok:
        from .py3PBKDF2 import verifyPassword
        masterPassword = Preferences.getUser("MasterPassword")
        try:
            if masterPassword:
                if verifyPassword(pw, masterPassword):
                    MasterPassword = pwEncode(pw)
                else:
                    E5MessageBox.warning(
                        None,
                        QCoreApplication.translate(
                            "Crypto", "Master Password"),
                        QCoreApplication.translate(
                            "Crypto",
                            """The given password is incorrect."""))
            else:
                E5MessageBox.critical(
                    None,
                    QCoreApplication.translate("Crypto", "Master Password"),
                    QCoreApplication.translate(
                        "Crypto",
                        """There is no master password registered."""))
        except ValueError as why:
            E5MessageBox.warning(
                None,
                QCoreApplication.translate("Crypto", "Master Password"),
                QCoreApplication.translate(
                    "Crypto",
                    """<p>The given password cannot be verified.</p>"""
                    """<p>Reason: {0}""".format(str(why))))


def pwEncrypt(pw, masterPW=None):
    """
    Module function to encrypt a password.

    @param pw password to encrypt (string)
    @param masterPW password to be used for encryption (string)
    @return encrypted password (string) and flag indicating
        success (boolean)
    """
    if masterPW is None:
        if MasterPassword is None:
            __getMasterPassword()
            if MasterPassword is None:
                return "", False

        masterPW = pwDecode(MasterPassword)

    from .py3PBKDF2 import hashPasswordTuple
    digestname, iterations, salt, hash = hashPasswordTuple(masterPW)
    key = hash[:32]
    from .py3AES import encryptData
    try:
        cipher = encryptData(key, pw.encode("utf-8"))
    except ValueError:
        return "", False
    return CryptoMarker + Delimiter.join([
        digestname,
        str(iterations),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(cipher).decode("ascii")
    ]), True


def pwDecrypt(epw, masterPW=None):
    """
    Module function to decrypt a password.

    @param epw hashed password to decrypt (string)
    @param masterPW password to be used for decryption (string)
    @return decrypted password (string) and flag indicating
        success (boolean)
    """
    if not epw.startswith(CryptoMarker):
        return epw, False  # it was not encoded using pwEncrypt

    if masterPW is None:
        if MasterPassword is None:
            __getMasterPassword()
            if MasterPassword is None:
                return "", False

        masterPW = pwDecode(MasterPassword)

    from .py3AES import decryptData
    from .py3PBKDF2 import rehashPassword

    hashParameters, epw = epw[3:].rsplit(Delimiter, 1)
    try:
        # recreate the key used to encrypt
        key = rehashPassword(masterPW, hashParameters)[:32]
        plaintext = decryptData(key, base64.b64decode(epw.encode("ascii")))
    except ValueError:
        return "", False
    return plaintext.decode("utf-8"), True


def pwReencrypt(epw, oldPassword, newPassword):
    """
    Module function to re-encrypt a password.

    @param epw hashed password to re-encrypt (string)
    @param oldPassword password used to encrypt (string)
    @param newPassword new password to be used (string)
    @return encrypted password (string) and flag indicating
        success (boolean)
    """
    plaintext, ok = pwDecrypt(epw, oldPassword)
    if ok:
        return pwEncrypt(plaintext, newPassword)
    else:
        return "", False


def pwRecode(epw, oldPassword, newPassword):
    """
    Module function to re-encode a password.

    In case of an error the encoded password is returned unchanged.

    @param epw encoded password to re-encode (string)
    @param oldPassword password used to encode (string)
    @param newPassword new password to be used (string)
    @return encoded password (string)
    """
    if epw == "":
        return epw

    if newPassword == "":
        plaintext, ok = pwDecrypt(epw)
        return (pwEncode(plaintext) if ok else epw)
    else:
        if oldPassword == "":
            plaintext = pwDecode(epw)
            cipher, ok = pwEncrypt(plaintext, newPassword)
            return (cipher if ok else epw)
        else:
            npw, ok = pwReencrypt(epw, oldPassword, newPassword)
            return (npw if ok else epw)


def pwConvert(pw, encode=True):
    """
    Module function to convert a plaintext password to the encoded form or
    vice versa.

    If there is an error, an empty code is returned for the encode function
    or the given encoded password for the decode function.

    @param pw password to encode (string)
    @param encode flag indicating an encode or decode function (boolean)
    @return encoded or decoded password (string)
    """
    if pw == "":
        return pw

    if encode:
        # plain text -> encoded
        if Preferences.getUser("UseMasterPassword"):
            epw = pwEncrypt(pw)[0]
        else:
            epw = pwEncode(pw)
        return epw
    else:
        # encoded -> plain text
        if Preferences.getUser("UseMasterPassword"):
            plain, ok = pwDecrypt(pw)
        else:
            plain, ok = pwDecode(pw), True
        return (plain if ok else pw)


def changeRememberedMaster(newPassword):
    """
    Module function to change the remembered master password.

    @param newPassword new password to be used (string)
    """
    global MasterPassword

    if newPassword == "":
        MasterPassword = None
    else:
        MasterPassword = pwEncode(newPassword)


def dataEncrypt(data, password, keyLength=32, hashIterations=10000):
    """
    Module function to encrypt a password.

    @param data data to encrypt (bytes)
    @param password password to be used for encryption (string)
    @keyparam keyLength length of the key to be generated for encryption
        (16, 24 or 32)
    @keyparam hashIterations number of hashes to be applied to the password for
        generating the encryption key (integer)
    @return encrypted data (bytes) and flag indicating
        success (boolean)
    """
    from .py3AES import encryptData
    from .py3PBKDF2 import hashPasswordTuple

    digestname, iterations, salt, hash = \
        hashPasswordTuple(password, iterations=hashIterations)
    key = hash[:keyLength]
    try:
        cipher = encryptData(key, data)
    except ValueError:
        return b"", False
    return CryptoMarker.encode() + Delimiter.encode().join([
        digestname.encode(),
        str(iterations).encode(),
        base64.b64encode(salt),
        base64.b64encode(cipher)
    ]), True


def dataDecrypt(edata, password, keyLength=32):
    """
    Module function to decrypt a password.

    @param edata hashed data to decrypt (string)
    @param password password to be used for decryption (string)
    @keyparam keyLength length of the key to be generated for decryption
        (16, 24 or 32)
    @return decrypted data (bytes) and flag indicating
        success (boolean)
    """
    if not edata.startswith(CryptoMarker.encode()):
        return edata, False  # it was not encoded using dataEncrypt

    from .py3AES import decryptData
    from .py3PBKDF2 import rehashPassword

    hashParametersBytes, edata = edata[3:].rsplit(Delimiter.encode(), 1)
    hashParameters = hashParametersBytes.decode()
    try:
        # recreate the key used to encrypt
        key = rehashPassword(password, hashParameters)[:keyLength]
        plaintext = decryptData(key, base64.b64decode(edata))
    except ValueError:
        return "", False
    return plaintext, True

if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication([])

    mpw = "blahblah"
    cpw = "SomeSecret"

    cipher, ok = pwEncrypt(cpw)
    print(ok, cipher)
    plain, ok = pwDecrypt(cipher)
    print(ok, plain)

    cipher, ok = pwEncrypt(cpw, mpw)
    print(ok, cipher)
    plain, ok = pwDecrypt(cipher, mpw)
    print(ok, plain)

    sys.exit(0)
