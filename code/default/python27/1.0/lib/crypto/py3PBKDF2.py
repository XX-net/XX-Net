# -*- coding: utf-8 -*-

# Copyright (c) 2002 - 2014 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing PBKDF2 functions.
"""

from __future__ import unicode_literals

import hashlib
import hmac
import os
import base64

Hashes = {
    "sha1": hashlib.sha1,
    "sha224": hashlib.sha224,
    "sha256": hashlib.sha256,
    "sha384": hashlib.sha384,
    "sha512": hashlib.sha512,
    "md5": hashlib.md5,
}

Delimiter = "$"


def pbkdf2(password, salt, iterations, digestMod):
    """
    Module function to hash a password according to the PBKDF2 specification.

    @param password clear text password (bytes)
    @param salt salt value (bytes)
    @param iterations number of times hash function should be applied (integer)
    @param digestMod hash function
    @return hashed password (bytes)
    """
    hash = password
    for i in range(iterations):
        hash = hmac.new(salt, hash, digestMod).digest()
    return hash


def hashPasswordTuple(password, digestMod=hashlib.sha512, iterations=10000,
                      saltSize=32):
    """
    Module function to hash a password according to the PBKDF2 specification.

    @param password clear text password (string)
    @param digestMod hash function
    @param iterations number of times hash function should be applied (integer)
    @param saltSize size of the salt (integer)
    @return tuple of digestname (string), number of iterations (integer),
        salt (bytes) and hashed password (bytes)
    """
    salt = os.urandom(saltSize)
    password = password.encode("utf-8")
    hash = pbkdf2(password, salt, iterations, digestMod)
    digestname = digestMod.__name__.replace("openssl_", "")
    return digestname, iterations, salt, hash


def hashPassword(password, digestMod=hashlib.sha512, iterations=10000,
                 saltSize=32):
    """
    Module function to hash a password according to the PBKDF2 specification.

    @param password clear text password (string)
    @param digestMod hash function
    @param iterations number of times hash function should be applied (integer)
    @param saltSize size of the salt (integer)
    @return hashed password entry according to PBKDF2 specification (string)
    """
    digestname, iterations, salt, hash = \
        hashPasswordTuple(password, digestMod, iterations, saltSize)
    return Delimiter.join([
        digestname,
        str(iterations),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(hash).decode("ascii")
    ])


def verifyPassword(password, hash):
    """
    Module function to verify a password against a hash encoded password.

    @param password clear text password (string)
    @param hash hash encoded password in the form
        'digestmod$iterations$salt$hashed_password' as produced by the
        hashPassword function (string)
    @return flag indicating a successfull verification (boolean)
    @exception ValueError the hash is not of the expected format or the
        digest is not one of the known ones
    """
    try:
        digestname, iterations, salt, pwHash = hash.split(Delimiter)
    except ValueError:
        raise ValueError(
            "Expected hash encoded password in format "
            "'digestmod{0}iterations{0}salt{0}hashed_password"
            .format(Delimiter))

    if digestname not in Hashes.keys():
        raise ValueError(
            "Unsupported hash algorithm '{0}' for hash encoded password '{1}'."
            .format(digestname, hash))

    iterations = int(iterations)
    salt = base64.b64decode(salt.encode("ascii"))
    pwHash = base64.b64decode(pwHash.encode("ascii"))
    password = password.encode("utf-8")
    return pwHash == pbkdf2(password, salt, iterations, Hashes[digestname])


def rehashPassword(password, hashParameters):
    """
    Module function to recreate a password hash given the hash parameters.

    @param password clear text password (string)
    @param hashParameters hash parameters in the form
        'digestmod$iterations$salt' (string)
    @return hashed password (bytes)
    @exception ValueError the hash parameters string is not of the expected
        format or the digest is not one of the known ones
    """
    try:
        digestname, iterations, salt = hashParameters.split(Delimiter)
    except ValueError:
        raise ValueError(
            "Expected hash parameters string in format "
            "'digestmod{0}iterations{0}salt".format(Delimiter))

    if digestname not in Hashes.keys():
        raise ValueError(
            "Unsupported hash algorithm '{0}' for hash parameters '{1}'."
            .format(digestname, hash))

    iterations = int(iterations)
    salt = base64.b64decode(salt.encode("ascii"))
    password = password.encode("utf-8")
    return pbkdf2(password, salt, iterations, Hashes[digestname])


if __name__ == "__main__":
    import sys
    pw = "secret_password"
    print(len(hashPasswordTuple(pw)[-1]))
    pwHash = hashPassword(pw)
    print(pwHash)
    print(verifyPassword(pw, pwHash))
    sys.exit(0)
