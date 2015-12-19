# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import collections
import os
import threading
import types

from cryptography.exceptions import InternalError
from cryptography.hazmat.bindings._openssl import ffi, lib
from cryptography.hazmat.bindings.openssl._conditional import CONDITIONAL_NAMES


_OpenSSLError = collections.namedtuple("_OpenSSLError",
                                       ["code", "lib", "func", "reason"])


def _consume_errors(lib):
    errors = []
    while True:
        code = lib.ERR_get_error()
        if code == 0:
            break

        err_lib = lib.ERR_GET_LIB(code)
        err_func = lib.ERR_GET_FUNC(code)
        err_reason = lib.ERR_GET_REASON(code)

        errors.append(_OpenSSLError(code, err_lib, err_func, err_reason))
    return errors


def _openssl_assert(lib, ok):
    if not ok:
        errors = _consume_errors(lib)
        raise InternalError(
            "Unknown OpenSSL error. Please file an issue at https://github.com"
            "/pyca/cryptography/issues with information on how to reproduce "
            "this. ({0!r})".format(errors),
            errors
        )


@ffi.callback("int (*)(unsigned char *, int)", error=-1)
def _osrandom_rand_bytes(buf, size):
    signed = ffi.cast("char *", buf)
    result = os.urandom(size)
    signed[0:size] = result
    return 1


@ffi.callback("int (*)(void)")
def _osrandom_rand_status():
    return 1


def build_conditional_library(lib, conditional_names):
    conditional_lib = types.ModuleType("lib")
    excluded_names = set()
    for condition, names in conditional_names.items():
        if not getattr(lib, condition):
            excluded_names |= set(names)

    for attr in dir(lib):
        if attr not in excluded_names:
            setattr(conditional_lib, attr, getattr(lib, attr))

    return conditional_lib


class Binding(object):
    """
    OpenSSL API wrapper.
    """
    lib = None
    ffi = ffi
    _lib_loaded = False
    _locks = None
    _lock_cb_handle = None
    _init_lock = threading.Lock()
    _lock_init_lock = threading.Lock()

    _osrandom_engine_id = ffi.new("const char[]", b"osrandom")
    _osrandom_engine_name = ffi.new("const char[]", b"osrandom_engine")
    _osrandom_method = ffi.new(
        "RAND_METHOD *",
        dict(bytes=_osrandom_rand_bytes, pseudorand=_osrandom_rand_bytes,
             status=_osrandom_rand_status)
    )

    def __init__(self):
        self._ensure_ffi_initialized()

    @classmethod
    def _register_osrandom_engine(cls):
        _openssl_assert(cls.lib, cls.lib.ERR_peek_error() == 0)

        engine = cls.lib.ENGINE_new()
        _openssl_assert(cls.lib, engine != cls.ffi.NULL)
        try:
            result = cls.lib.ENGINE_set_id(engine, cls._osrandom_engine_id)
            _openssl_assert(cls.lib, result == 1)
            result = cls.lib.ENGINE_set_name(engine, cls._osrandom_engine_name)
            _openssl_assert(cls.lib, result == 1)
            result = cls.lib.ENGINE_set_RAND(engine, cls._osrandom_method)
            _openssl_assert(cls.lib, result == 1)
            result = cls.lib.ENGINE_add(engine)
            if result != 1:
                errors = _consume_errors(cls.lib)
                _openssl_assert(
                    cls.lib,
                    errors[0].reason == cls.lib.ENGINE_R_CONFLICTING_ENGINE_ID
                )

        finally:
            result = cls.lib.ENGINE_free(engine)
            _openssl_assert(cls.lib, result == 1)

    @classmethod
    def _ensure_ffi_initialized(cls):
        with cls._init_lock:
            if not cls._lib_loaded:
                cls.lib = build_conditional_library(lib, CONDITIONAL_NAMES)
                cls._lib_loaded = True
                # initialize the SSL library
                cls.lib.SSL_library_init()
                # adds all ciphers/digests for EVP
                cls.lib.OpenSSL_add_all_algorithms()
                # loads error strings for libcrypto and libssl functions
                cls.lib.SSL_load_error_strings()
                cls._register_osrandom_engine()

    @classmethod
    def init_static_locks(cls):
        with cls._lock_init_lock:
            cls._ensure_ffi_initialized()

            if not cls._lock_cb_handle:
                cls._lock_cb_handle = cls.ffi.callback(
                    "void(int, int, const char *, int)",
                    cls._lock_cb
                )

            # Use Python's implementation if available, importing _ssl triggers
            # the setup for this.
            __import__("_ssl")

            if cls.lib.CRYPTO_get_locking_callback() != cls.ffi.NULL:
                return

            # If nothing else has setup a locking callback already, we set up
            # our own
            num_locks = cls.lib.CRYPTO_num_locks()
            cls._locks = [threading.Lock() for n in range(num_locks)]

            cls.lib.CRYPTO_set_locking_callback(cls._lock_cb_handle)

    @classmethod
    def _lock_cb(cls, mode, n, file, line):
        lock = cls._locks[n]

        if mode & cls.lib.CRYPTO_LOCK:
            lock.acquire()
        elif mode & cls.lib.CRYPTO_UNLOCK:
            lock.release()
        else:
            raise RuntimeError(
                "Unknown lock mode {0}: lock={1}, file={2}, line={3}.".format(
                    mode, n, file, line
                )
            )


# OpenSSL is not thread safe until the locks are initialized. We call this
# method in module scope so that it executes with the import lock. On
# Pythons < 3.4 this import lock is a global lock, which can prevent a race
# condition registering the OpenSSL locks. On Python 3.4+ the import lock
# is per module so this approach will not work.
Binding.init_static_locks()
