# Copyright (C) Jean-Paul Calderone
# See LICENSE for details.

"""
Unit tests for :py:obj:`OpenSSL.SSL`.
"""

from gc import collect, get_referrers
from errno import ECONNREFUSED, EINPROGRESS, EWOULDBLOCK, EPIPE, ESHUTDOWN
from sys import platform, getfilesystemencoding
from socket import SHUT_RDWR, error, socket
from os import makedirs
from os.path import join
from unittest import main
from weakref import ref
from warnings import catch_warnings, simplefilter

from six import PY3, text_type, u

from OpenSSL.crypto import TYPE_RSA, FILETYPE_PEM
from OpenSSL.crypto import PKey, X509, X509Extension, X509Store
from OpenSSL.crypto import dump_privatekey, load_privatekey
from OpenSSL.crypto import dump_certificate, load_certificate
from OpenSSL.crypto import get_elliptic_curves

from OpenSSL.SSL import OPENSSL_VERSION_NUMBER, SSLEAY_VERSION, SSLEAY_CFLAGS
from OpenSSL.SSL import SSLEAY_PLATFORM, SSLEAY_DIR, SSLEAY_BUILT_ON
from OpenSSL.SSL import SENT_SHUTDOWN, RECEIVED_SHUTDOWN
from OpenSSL.SSL import (
    SSLv2_METHOD, SSLv3_METHOD, SSLv23_METHOD, TLSv1_METHOD,
    TLSv1_1_METHOD, TLSv1_2_METHOD)
from OpenSSL.SSL import OP_SINGLE_DH_USE, OP_NO_SSLv2, OP_NO_SSLv3
from OpenSSL.SSL import (
    VERIFY_PEER, VERIFY_FAIL_IF_NO_PEER_CERT, VERIFY_CLIENT_ONCE, VERIFY_NONE)

from OpenSSL.SSL import (
    SESS_CACHE_OFF, SESS_CACHE_CLIENT, SESS_CACHE_SERVER, SESS_CACHE_BOTH,
    SESS_CACHE_NO_AUTO_CLEAR, SESS_CACHE_NO_INTERNAL_LOOKUP,
    SESS_CACHE_NO_INTERNAL_STORE, SESS_CACHE_NO_INTERNAL)

from OpenSSL.SSL import (
    Error, SysCallError, WantReadError, WantWriteError, ZeroReturnError)
from OpenSSL.SSL import (
    Context, ContextType, Session, Connection, ConnectionType, SSLeay_version)

from OpenSSL._util import lib as _lib

from OpenSSL.test.util import WARNING_TYPE_EXPECTED, NON_ASCII, TestCase, b
from OpenSSL.test.test_crypto import (
    cleartextCertificatePEM, cleartextPrivateKeyPEM,
    client_cert_pem, client_key_pem, server_cert_pem, server_key_pem,
    root_cert_pem)

try:
    from OpenSSL.SSL import OP_NO_QUERY_MTU
except ImportError:
    OP_NO_QUERY_MTU = None
try:
    from OpenSSL.SSL import OP_COOKIE_EXCHANGE
except ImportError:
    OP_COOKIE_EXCHANGE = None
try:
    from OpenSSL.SSL import OP_NO_TICKET
except ImportError:
    OP_NO_TICKET = None

try:
    from OpenSSL.SSL import OP_NO_COMPRESSION
except ImportError:
    OP_NO_COMPRESSION = None

try:
    from OpenSSL.SSL import MODE_RELEASE_BUFFERS
except ImportError:
    MODE_RELEASE_BUFFERS = None

try:
    from OpenSSL.SSL import OP_NO_TLSv1, OP_NO_TLSv1_1, OP_NO_TLSv1_2
except ImportError:
    OP_NO_TLSv1 = OP_NO_TLSv1_1 = OP_NO_TLSv1_2 = None

from OpenSSL.SSL import (
    SSL_ST_CONNECT, SSL_ST_ACCEPT, SSL_ST_MASK, SSL_ST_INIT, SSL_ST_BEFORE,
    SSL_ST_OK, SSL_ST_RENEGOTIATE,
    SSL_CB_LOOP, SSL_CB_EXIT, SSL_CB_READ, SSL_CB_WRITE, SSL_CB_ALERT,
    SSL_CB_READ_ALERT, SSL_CB_WRITE_ALERT, SSL_CB_ACCEPT_LOOP,
    SSL_CB_ACCEPT_EXIT, SSL_CB_CONNECT_LOOP, SSL_CB_CONNECT_EXIT,
    SSL_CB_HANDSHAKE_START, SSL_CB_HANDSHAKE_DONE)

# openssl dhparam 128 -out dh-128.pem (note that 128 is a small number of bits
# to use)
dhparam = """\
-----BEGIN DH PARAMETERS-----
MBYCEQCobsg29c9WZP/54oAPcwiDAgEC
-----END DH PARAMETERS-----
"""


def join_bytes_or_unicode(prefix, suffix):
    """
    Join two path components of either ``bytes`` or ``unicode``.

    The return type is the same as the type of ``prefix``.
    """
    # If the types are the same, nothing special is necessary.
    if type(prefix) == type(suffix):
        return join(prefix, suffix)

    # Otherwise, coerce suffix to the type of prefix.
    if isinstance(prefix, text_type):
        return join(prefix, suffix.decode(getfilesystemencoding()))
    else:
        return join(prefix, suffix.encode(getfilesystemencoding()))


def verify_cb(conn, cert, errnum, depth, ok):
    return ok


def socket_pair():
    """
    Establish and return a pair of network sockets connected to each other.
    """
    # Connect a pair of sockets
    port = socket()
    port.bind(('', 0))
    port.listen(1)
    client = socket()
    client.setblocking(False)
    client.connect_ex(("127.0.0.1", port.getsockname()[1]))
    client.setblocking(True)
    server = port.accept()[0]

    # Let's pass some unencrypted data to make sure our socket connection is
    # fine.  Just one byte, so we don't have to worry about buffers getting
    # filled up or fragmentation.
    server.send(b("x"))
    assert client.recv(1024) == b("x")
    client.send(b("y"))
    assert server.recv(1024) == b("y")

    # Most of our callers want non-blocking sockets, make it easy for them.
    server.setblocking(False)
    client.setblocking(False)

    return (server, client)



def handshake(client, server):
    conns = [client, server]
    while conns:
        for conn in conns:
            try:
                conn.do_handshake()
            except WantReadError:
                pass
            else:
                conns.remove(conn)


def _create_certificate_chain():
    """
    Construct and return a chain of certificates.

        1. A new self-signed certificate authority certificate (cacert)
        2. A new intermediate certificate signed by cacert (icert)
        3. A new server certificate signed by icert (scert)
    """
    caext = X509Extension(b('basicConstraints'), False, b('CA:true'))

    # Step 1
    cakey = PKey()
    cakey.generate_key(TYPE_RSA, 512)
    cacert = X509()
    cacert.get_subject().commonName = "Authority Certificate"
    cacert.set_issuer(cacert.get_subject())
    cacert.set_pubkey(cakey)
    cacert.set_notBefore(b("20000101000000Z"))
    cacert.set_notAfter(b("20200101000000Z"))
    cacert.add_extensions([caext])
    cacert.set_serial_number(0)
    cacert.sign(cakey, "sha1")

    # Step 2
    ikey = PKey()
    ikey.generate_key(TYPE_RSA, 512)
    icert = X509()
    icert.get_subject().commonName = "Intermediate Certificate"
    icert.set_issuer(cacert.get_subject())
    icert.set_pubkey(ikey)
    icert.set_notBefore(b("20000101000000Z"))
    icert.set_notAfter(b("20200101000000Z"))
    icert.add_extensions([caext])
    icert.set_serial_number(0)
    icert.sign(cakey, "sha1")

    # Step 3
    skey = PKey()
    skey.generate_key(TYPE_RSA, 512)
    scert = X509()
    scert.get_subject().commonName = "Server Certificate"
    scert.set_issuer(icert.get_subject())
    scert.set_pubkey(skey)
    scert.set_notBefore(b("20000101000000Z"))
    scert.set_notAfter(b("20200101000000Z"))
    scert.add_extensions([
            X509Extension(b('basicConstraints'), True, b('CA:false'))])
    scert.set_serial_number(0)
    scert.sign(ikey, "sha1")

    return [(cakey, cacert), (ikey, icert), (skey, scert)]



class _LoopbackMixin:
    """
    Helper mixin which defines methods for creating a connected socket pair and
    for forcing two connected SSL sockets to talk to each other via memory BIOs.
    """
    def _loopbackClientFactory(self, socket):
        client = Connection(Context(TLSv1_METHOD), socket)
        client.set_connect_state()
        return client


    def _loopbackServerFactory(self, socket):
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        ctx.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))
        server = Connection(ctx, socket)
        server.set_accept_state()
        return server


    def _loopback(self, serverFactory=None, clientFactory=None):
        if serverFactory is None:
            serverFactory = self._loopbackServerFactory
        if clientFactory is None:
            clientFactory = self._loopbackClientFactory

        (server, client) = socket_pair()
        server = serverFactory(server)
        client = clientFactory(client)

        handshake(client, server)

        server.setblocking(True)
        client.setblocking(True)
        return server, client


    def _interactInMemory(self, client_conn, server_conn):
        """
        Try to read application bytes from each of the two :py:obj:`Connection`
        objects.  Copy bytes back and forth between their send/receive buffers
        for as long as there is anything to copy.  When there is nothing more
        to copy, return :py:obj:`None`.  If one of them actually manages to deliver
        some application bytes, return a two-tuple of the connection from which
        the bytes were read and the bytes themselves.
        """
        wrote = True
        while wrote:
            # Loop until neither side has anything to say
            wrote = False

            # Copy stuff from each side's send buffer to the other side's
            # receive buffer.
            for (read, write) in [(client_conn, server_conn),
                                  (server_conn, client_conn)]:

                # Give the side a chance to generate some more bytes, or
                # succeed.
                try:
                    data = read.recv(2 ** 16)
                except WantReadError:
                    # It didn't succeed, so we'll hope it generated some
                    # output.
                    pass
                else:
                    # It did succeed, so we'll stop now and let the caller deal
                    # with it.
                    return (read, data)

                while True:
                    # Keep copying as long as there's more stuff there.
                    try:
                        dirty = read.bio_read(4096)
                    except WantReadError:
                        # Okay, nothing more waiting to be sent.  Stop
                        # processing this send buffer.
                        break
                    else:
                        # Keep track of the fact that someone generated some
                        # output.
                        wrote = True
                        write.bio_write(dirty)


    def _handshakeInMemory(self, client_conn, server_conn):
        """
        Perform the TLS handshake between two :py:class:`Connection` instances
        connected to each other via memory BIOs.
        """
        client_conn.set_connect_state()
        server_conn.set_accept_state()

        for conn in [client_conn, server_conn]:
            try:
                conn.do_handshake()
            except WantReadError:
                pass

        self._interactInMemory(client_conn, server_conn)



class VersionTests(TestCase):
    """
    Tests for version information exposed by
    :py:obj:`OpenSSL.SSL.SSLeay_version` and
    :py:obj:`OpenSSL.SSL.OPENSSL_VERSION_NUMBER`.
    """
    def test_OPENSSL_VERSION_NUMBER(self):
        """
        :py:obj:`OPENSSL_VERSION_NUMBER` is an integer with status in the low
        byte and the patch, fix, minor, and major versions in the
        nibbles above that.
        """
        self.assertTrue(isinstance(OPENSSL_VERSION_NUMBER, int))


    def test_SSLeay_version(self):
        """
        :py:obj:`SSLeay_version` takes a version type indicator and returns
        one of a number of version strings based on that indicator.
        """
        versions = {}
        for t in [SSLEAY_VERSION, SSLEAY_CFLAGS, SSLEAY_BUILT_ON,
                  SSLEAY_PLATFORM, SSLEAY_DIR]:
            version = SSLeay_version(t)
            versions[version] = t
            self.assertTrue(isinstance(version, bytes))
        self.assertEqual(len(versions), 5)



class ContextTests(TestCase, _LoopbackMixin):
    """
    Unit tests for :py:obj:`OpenSSL.SSL.Context`.
    """
    def test_method(self):
        """
        :py:obj:`Context` can be instantiated with one of :py:obj:`SSLv2_METHOD`,
        :py:obj:`SSLv3_METHOD`, :py:obj:`SSLv23_METHOD`, :py:obj:`TLSv1_METHOD`,
        :py:obj:`TLSv1_1_METHOD`, or :py:obj:`TLSv1_2_METHOD`.
        """
        methods = [
            SSLv3_METHOD, SSLv23_METHOD, TLSv1_METHOD]
        for meth in methods:
            Context(meth)


        maybe = [SSLv2_METHOD, TLSv1_1_METHOD, TLSv1_2_METHOD]
        for meth in maybe:
            try:
                Context(meth)
            except (Error, ValueError):
                # Some versions of OpenSSL have SSLv2 / TLSv1.1 / TLSv1.2, some
                # don't.  Difficult to say in advance.
                pass

        self.assertRaises(TypeError, Context, "")
        self.assertRaises(ValueError, Context, 10)


    if not PY3:
        def test_method_long(self):
            """
            On Python 2 :py:class:`Context` accepts values of type
            :py:obj:`long` as well as :py:obj:`int`.
            """
            Context(long(TLSv1_METHOD))



    def test_type(self):
        """
        :py:obj:`Context` and :py:obj:`ContextType` refer to the same type object and can be
        used to create instances of that type.
        """
        self.assertIdentical(Context, ContextType)
        self.assertConsistentType(Context, 'Context', TLSv1_METHOD)


    def test_use_privatekey(self):
        """
        :py:obj:`Context.use_privatekey` takes an :py:obj:`OpenSSL.crypto.PKey` instance.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 128)
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(key)
        self.assertRaises(TypeError, ctx.use_privatekey, "")


    def test_use_privatekey_file_missing(self):
        """
        :py:obj:`Context.use_privatekey_file` raises :py:obj:`OpenSSL.SSL.Error`
        when passed the name of a file which does not exist.
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(Error, ctx.use_privatekey_file, self.mktemp())


    def _use_privatekey_file_test(self, pemfile, filetype):
        """
        Verify that calling ``Context.use_privatekey_file`` with the given
        arguments does not raise an exception.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 128)

        with open(pemfile, "wt") as pem:
            pem.write(
                dump_privatekey(FILETYPE_PEM, key).decode("ascii")
            )

        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey_file(pemfile, filetype)


    def test_use_privatekey_file_bytes(self):
        """
        A private key can be specified from a file by passing a ``bytes``
        instance giving the file name to ``Context.use_privatekey_file``.
        """
        self._use_privatekey_file_test(
            self.mktemp() + NON_ASCII.encode(getfilesystemencoding()),
            FILETYPE_PEM,
        )


    def test_use_privatekey_file_unicode(self):
        """
        A private key can be specified from a file by passing a ``unicode``
        instance giving the file name to ``Context.use_privatekey_file``.
        """
        self._use_privatekey_file_test(
            self.mktemp().decode(getfilesystemencoding()) + NON_ASCII,
            FILETYPE_PEM,
        )


    if not PY3:
        def test_use_privatekey_file_long(self):
            """
            On Python 2 :py:obj:`Context.use_privatekey_file` accepts a
            filetype of type :py:obj:`long` as well as :py:obj:`int`.
            """
            self._use_privatekey_file_test(self.mktemp(), long(FILETYPE_PEM))


    def test_use_certificate_wrong_args(self):
        """
        :py:obj:`Context.use_certificate_wrong_args` raises :py:obj:`TypeError`
        when not passed exactly one :py:obj:`OpenSSL.crypto.X509` instance as an
        argument.
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, ctx.use_certificate)
        self.assertRaises(TypeError, ctx.use_certificate, "hello, world")
        self.assertRaises(TypeError, ctx.use_certificate, X509(), "hello, world")


    def test_use_certificate_uninitialized(self):
        """
        :py:obj:`Context.use_certificate` raises :py:obj:`OpenSSL.SSL.Error`
        when passed a :py:obj:`OpenSSL.crypto.X509` instance which has not been
        initialized (ie, which does not actually have any certificate data).
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(Error, ctx.use_certificate, X509())


    def test_use_certificate(self):
        """
        :py:obj:`Context.use_certificate` sets the certificate which will be
        used to identify connections created using the context.
        """
        # TODO
        # Hard to assert anything.  But we could set a privatekey then ask
        # OpenSSL if the cert and key agree using check_privatekey.  Then as
        # long as check_privatekey works right we're good...
        ctx = Context(TLSv1_METHOD)
        ctx.use_certificate(load_certificate(FILETYPE_PEM, cleartextCertificatePEM))


    def test_use_certificate_file_wrong_args(self):
        """
        :py:obj:`Context.use_certificate_file` raises :py:obj:`TypeError` if
        called with zero arguments or more than two arguments, or if the first
        argument is not a byte string or the second argumnent is not an integer.
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, ctx.use_certificate_file)
        self.assertRaises(TypeError, ctx.use_certificate_file, b"somefile", object())
        self.assertRaises(
            TypeError, ctx.use_certificate_file, b"somefile", FILETYPE_PEM, object())
        self.assertRaises(
            TypeError, ctx.use_certificate_file, object(), FILETYPE_PEM)
        self.assertRaises(
            TypeError, ctx.use_certificate_file, b"somefile", object())


    def test_use_certificate_file_missing(self):
        """
        :py:obj:`Context.use_certificate_file` raises
        `:py:obj:`OpenSSL.SSL.Error` if passed the name of a file which does not
        exist.
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(Error, ctx.use_certificate_file, self.mktemp())


    def _use_certificate_file_test(self, certificate_file):
        """
        Verify that calling ``Context.use_certificate_file`` with the given
        filename doesn't raise an exception.
        """
        # TODO
        # Hard to assert anything.  But we could set a privatekey then ask
        # OpenSSL if the cert and key agree using check_privatekey.  Then as
        # long as check_privatekey works right we're good...
        with open(certificate_file, "wb") as pem_file:
            pem_file.write(cleartextCertificatePEM)

        ctx = Context(TLSv1_METHOD)
        ctx.use_certificate_file(certificate_file)


    def test_use_certificate_file_bytes(self):
        """
        :py:obj:`Context.use_certificate_file` sets the certificate (given as a
        ``bytes`` filename) which will be used to identify connections created
        using the context.
        """
        filename = self.mktemp() + NON_ASCII.encode(getfilesystemencoding())
        self._use_certificate_file_test(filename)


    def test_use_certificate_file_unicode(self):
        """
        :py:obj:`Context.use_certificate_file` sets the certificate (given as a
        ``bytes`` filename) which will be used to identify connections created
        using the context.
        """
        filename = self.mktemp().decode(getfilesystemencoding()) + NON_ASCII
        self._use_certificate_file_test(filename)


    if not PY3:
        def test_use_certificate_file_long(self):
            """
            On Python 2 :py:obj:`Context.use_certificate_file` accepts a
            filetype of type :py:obj:`long` as well as :py:obj:`int`.
            """
            pem_filename = self.mktemp()
            with open(pem_filename, "wb") as pem_file:
                pem_file.write(cleartextCertificatePEM)

            ctx = Context(TLSv1_METHOD)
            ctx.use_certificate_file(pem_filename, long(FILETYPE_PEM))


    def test_check_privatekey_valid(self):
        """
        :py:obj:`Context.check_privatekey` returns :py:obj:`None` if the
        :py:obj:`Context` instance has been configured to use a matched key and
        certificate pair.
        """
        key = load_privatekey(FILETYPE_PEM, client_key_pem)
        cert = load_certificate(FILETYPE_PEM, client_cert_pem)
        context = Context(TLSv1_METHOD)
        context.use_privatekey(key)
        context.use_certificate(cert)
        self.assertIs(None, context.check_privatekey())


    def test_check_privatekey_invalid(self):
        """
        :py:obj:`Context.check_privatekey` raises :py:obj:`Error` if the
        :py:obj:`Context` instance has been configured to use a key and
        certificate pair which don't relate to each other.
        """
        key = load_privatekey(FILETYPE_PEM, client_key_pem)
        cert = load_certificate(FILETYPE_PEM, server_cert_pem)
        context = Context(TLSv1_METHOD)
        context.use_privatekey(key)
        context.use_certificate(cert)
        self.assertRaises(Error, context.check_privatekey)


    def test_check_privatekey_wrong_args(self):
        """
        :py:obj:`Context.check_privatekey` raises :py:obj:`TypeError` if called
        with other than no arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.check_privatekey, object())


    def test_set_app_data_wrong_args(self):
        """
        :py:obj:`Context.set_app_data` raises :py:obj:`TypeError` if called with other than
        one argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_app_data)
        self.assertRaises(TypeError, context.set_app_data, None, None)


    def test_get_app_data_wrong_args(self):
        """
        :py:obj:`Context.get_app_data` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.get_app_data, None)


    def test_app_data(self):
        """
        :py:obj:`Context.set_app_data` stores an object for later retrieval using
        :py:obj:`Context.get_app_data`.
        """
        app_data = object()
        context = Context(TLSv1_METHOD)
        context.set_app_data(app_data)
        self.assertIdentical(context.get_app_data(), app_data)


    def test_set_options_wrong_args(self):
        """
        :py:obj:`Context.set_options` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or a non-:py:obj:`int` argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_options)
        self.assertRaises(TypeError, context.set_options, None)
        self.assertRaises(TypeError, context.set_options, 1, None)


    def test_set_options(self):
        """
        :py:obj:`Context.set_options` returns the new options value.
        """
        context = Context(TLSv1_METHOD)
        options = context.set_options(OP_NO_SSLv2)
        self.assertTrue(OP_NO_SSLv2 & options)


    if not PY3:
        def test_set_options_long(self):
            """
            On Python 2 :py:obj:`Context.set_options` accepts values of type
            :py:obj:`long` as well as :py:obj:`int`.
            """
            context = Context(TLSv1_METHOD)
            options = context.set_options(long(OP_NO_SSLv2))
            self.assertTrue(OP_NO_SSLv2 & options)


    def test_set_mode_wrong_args(self):
        """
        :py:obj:`Context.set`mode} raises :py:obj:`TypeError` if called with the wrong
        number of arguments or a non-:py:obj:`int` argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_mode)
        self.assertRaises(TypeError, context.set_mode, None)
        self.assertRaises(TypeError, context.set_mode, 1, None)


    if MODE_RELEASE_BUFFERS is not None:
        def test_set_mode(self):
            """
            :py:obj:`Context.set_mode` accepts a mode bitvector and returns the newly
            set mode.
            """
            context = Context(TLSv1_METHOD)
            self.assertTrue(
                MODE_RELEASE_BUFFERS & context.set_mode(MODE_RELEASE_BUFFERS))

        if not PY3:
            def test_set_mode_long(self):
                """
                On Python 2 :py:obj:`Context.set_mode` accepts values of type
                :py:obj:`long` as well as :py:obj:`int`.
                """
                context = Context(TLSv1_METHOD)
                mode = context.set_mode(long(MODE_RELEASE_BUFFERS))
                self.assertTrue(MODE_RELEASE_BUFFERS & mode)
    else:
        "MODE_RELEASE_BUFFERS unavailable - OpenSSL version may be too old"


    def test_set_timeout_wrong_args(self):
        """
        :py:obj:`Context.set_timeout` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or a non-:py:obj:`int` argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_timeout)
        self.assertRaises(TypeError, context.set_timeout, None)
        self.assertRaises(TypeError, context.set_timeout, 1, None)


    def test_get_timeout_wrong_args(self):
        """
        :py:obj:`Context.get_timeout` raises :py:obj:`TypeError` if called with any arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.get_timeout, None)


    def test_timeout(self):
        """
        :py:obj:`Context.set_timeout` sets the session timeout for all connections
        created using the context object.  :py:obj:`Context.get_timeout` retrieves this
        value.
        """
        context = Context(TLSv1_METHOD)
        context.set_timeout(1234)
        self.assertEquals(context.get_timeout(), 1234)


    if not PY3:
        def test_timeout_long(self):
            """
            On Python 2 :py:obj:`Context.set_timeout` accepts values of type
            `long` as well as int.
            """
            context = Context(TLSv1_METHOD)
            context.set_timeout(long(1234))
            self.assertEquals(context.get_timeout(), 1234)


    def test_set_verify_depth_wrong_args(self):
        """
        :py:obj:`Context.set_verify_depth` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or a non-:py:obj:`int` argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_verify_depth)
        self.assertRaises(TypeError, context.set_verify_depth, None)
        self.assertRaises(TypeError, context.set_verify_depth, 1, None)


    def test_get_verify_depth_wrong_args(self):
        """
        :py:obj:`Context.get_verify_depth` raises :py:obj:`TypeError` if called with any arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.get_verify_depth, None)


    def test_verify_depth(self):
        """
        :py:obj:`Context.set_verify_depth` sets the number of certificates in a chain
        to follow before giving up.  The value can be retrieved with
        :py:obj:`Context.get_verify_depth`.
        """
        context = Context(TLSv1_METHOD)
        context.set_verify_depth(11)
        self.assertEquals(context.get_verify_depth(), 11)


    if not PY3:
        def test_verify_depth_long(self):
            """
            On Python 2 :py:obj:`Context.set_verify_depth` accepts values of
            type `long` as well as int.
            """
            context = Context(TLSv1_METHOD)
            context.set_verify_depth(long(11))
            self.assertEquals(context.get_verify_depth(), 11)


    def _write_encrypted_pem(self, passphrase):
        """
        Write a new private key out to a new file, encrypted using the given
        passphrase.  Return the path to the new file.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 128)
        pemFile = self.mktemp()
        fObj = open(pemFile, 'w')
        pem = dump_privatekey(FILETYPE_PEM, key, "blowfish", passphrase)
        fObj.write(pem.decode('ascii'))
        fObj.close()
        return pemFile


    def test_set_passwd_cb_wrong_args(self):
        """
        :py:obj:`Context.set_passwd_cb` raises :py:obj:`TypeError` if called with the
        wrong arguments or with a non-callable first argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_passwd_cb)
        self.assertRaises(TypeError, context.set_passwd_cb, None)
        self.assertRaises(TypeError, context.set_passwd_cb, lambda: None, None, None)


    def test_set_passwd_cb(self):
        """
        :py:obj:`Context.set_passwd_cb` accepts a callable which will be invoked when
        a private key is loaded from an encrypted PEM.
        """
        passphrase = b("foobar")
        pemFile = self._write_encrypted_pem(passphrase)
        calledWith = []
        def passphraseCallback(maxlen, verify, extra):
            calledWith.append((maxlen, verify, extra))
            return passphrase
        context = Context(TLSv1_METHOD)
        context.set_passwd_cb(passphraseCallback)
        context.use_privatekey_file(pemFile)
        self.assertTrue(len(calledWith), 1)
        self.assertTrue(isinstance(calledWith[0][0], int))
        self.assertTrue(isinstance(calledWith[0][1], int))
        self.assertEqual(calledWith[0][2], None)


    def test_passwd_callback_exception(self):
        """
        :py:obj:`Context.use_privatekey_file` propagates any exception raised by the
        passphrase callback.
        """
        pemFile = self._write_encrypted_pem(b("monkeys are nice"))
        def passphraseCallback(maxlen, verify, extra):
            raise RuntimeError("Sorry, I am a fail.")

        context = Context(TLSv1_METHOD)
        context.set_passwd_cb(passphraseCallback)
        self.assertRaises(RuntimeError, context.use_privatekey_file, pemFile)


    def test_passwd_callback_false(self):
        """
        :py:obj:`Context.use_privatekey_file` raises :py:obj:`OpenSSL.SSL.Error` if the
        passphrase callback returns a false value.
        """
        pemFile = self._write_encrypted_pem(b("monkeys are nice"))
        def passphraseCallback(maxlen, verify, extra):
            return b""

        context = Context(TLSv1_METHOD)
        context.set_passwd_cb(passphraseCallback)
        self.assertRaises(Error, context.use_privatekey_file, pemFile)


    def test_passwd_callback_non_string(self):
        """
        :py:obj:`Context.use_privatekey_file` raises :py:obj:`OpenSSL.SSL.Error` if the
        passphrase callback returns a true non-string value.
        """
        pemFile = self._write_encrypted_pem(b("monkeys are nice"))
        def passphraseCallback(maxlen, verify, extra):
            return 10

        context = Context(TLSv1_METHOD)
        context.set_passwd_cb(passphraseCallback)
        self.assertRaises(ValueError, context.use_privatekey_file, pemFile)


    def test_passwd_callback_too_long(self):
        """
        If the passphrase returned by the passphrase callback returns a string
        longer than the indicated maximum length, it is truncated.
        """
        # A priori knowledge!
        passphrase = b("x") * 1024
        pemFile = self._write_encrypted_pem(passphrase)
        def passphraseCallback(maxlen, verify, extra):
            assert maxlen == 1024
            return passphrase + b("y")

        context = Context(TLSv1_METHOD)
        context.set_passwd_cb(passphraseCallback)
        # This shall succeed because the truncated result is the correct
        # passphrase.
        context.use_privatekey_file(pemFile)


    def test_set_info_callback(self):
        """
        :py:obj:`Context.set_info_callback` accepts a callable which will be invoked
        when certain information about an SSL connection is available.
        """
        (server, client) = socket_pair()

        clientSSL = Connection(Context(TLSv1_METHOD), client)
        clientSSL.set_connect_state()

        called = []
        def info(conn, where, ret):
            called.append((conn, where, ret))
        context = Context(TLSv1_METHOD)
        context.set_info_callback(info)
        context.use_certificate(
            load_certificate(FILETYPE_PEM, cleartextCertificatePEM))
        context.use_privatekey(
            load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM))

        serverSSL = Connection(context, server)
        serverSSL.set_accept_state()

        handshake(clientSSL, serverSSL)

        # The callback must always be called with a Connection instance as the
        # first argument.  It would probably be better to split this into
        # separate tests for client and server side info callbacks so we could
        # assert it is called with the right Connection instance.  It would
        # also be good to assert *something* about `where` and `ret`.
        notConnections = [
            conn for (conn, where, ret) in called
            if not isinstance(conn, Connection)]
        self.assertEqual(
            [], notConnections,
            "Some info callback arguments were not Connection instaces.")


    def _load_verify_locations_test(self, *args):
        """
        Create a client context which will verify the peer certificate and call
        its :py:obj:`load_verify_locations` method with the given arguments.
        Then connect it to a server and ensure that the handshake succeeds.
        """
        (server, client) = socket_pair()

        clientContext = Context(TLSv1_METHOD)
        clientContext.load_verify_locations(*args)
        # Require that the server certificate verify properly or the
        # connection will fail.
        clientContext.set_verify(
            VERIFY_PEER,
            lambda conn, cert, errno, depth, preverify_ok: preverify_ok)

        clientSSL = Connection(clientContext, client)
        clientSSL.set_connect_state()

        serverContext = Context(TLSv1_METHOD)
        serverContext.use_certificate(
            load_certificate(FILETYPE_PEM, cleartextCertificatePEM))
        serverContext.use_privatekey(
            load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM))

        serverSSL = Connection(serverContext, server)
        serverSSL.set_accept_state()

        # Without load_verify_locations above, the handshake
        # will fail:
        # Error: [('SSL routines', 'SSL3_GET_SERVER_CERTIFICATE',
        #          'certificate verify failed')]
        handshake(clientSSL, serverSSL)

        cert = clientSSL.get_peer_certificate()
        self.assertEqual(cert.get_subject().CN, 'Testing Root CA')


    def _load_verify_cafile(self, cafile):
        """
        Verify that if path to a file containing a certificate is passed to
        ``Context.load_verify_locations`` for the ``cafile`` parameter, that
        certificate is used as a trust root for the purposes of verifying
        connections created using that ``Context``.
        """
        fObj = open(cafile, 'w')
        fObj.write(cleartextCertificatePEM.decode('ascii'))
        fObj.close()

        self._load_verify_locations_test(cafile)


    def test_load_verify_bytes_cafile(self):
        """
        :py:obj:`Context.load_verify_locations` accepts a file name as a
        ``bytes`` instance and uses the certificates within for verification
        purposes.
        """
        cafile = self.mktemp() + NON_ASCII.encode(getfilesystemencoding())
        self._load_verify_cafile(cafile)


    def test_load_verify_unicode_cafile(self):
        """
        :py:obj:`Context.load_verify_locations` accepts a file name as a
        ``unicode`` instance and uses the certificates within for verification
        purposes.
        """
        self._load_verify_cafile(
            self.mktemp().decode(getfilesystemencoding()) + NON_ASCII
        )


    def test_load_verify_invalid_file(self):
        """
        :py:obj:`Context.load_verify_locations` raises :py:obj:`Error` when passed a
        non-existent cafile.
        """
        clientContext = Context(TLSv1_METHOD)
        self.assertRaises(
            Error, clientContext.load_verify_locations, self.mktemp())


    def _load_verify_directory_locations_capath(self, capath):
        """
        Verify that if path to a directory containing certificate files is
        passed to ``Context.load_verify_locations`` for the ``capath``
        parameter, those certificates are used as trust roots for the purposes
        of verifying connections created using that ``Context``.
        """
        makedirs(capath)
        # Hash values computed manually with c_rehash to avoid depending on
        # c_rehash in the test suite.  One is from OpenSSL 0.9.8, the other
        # from OpenSSL 1.0.0.
        for name in [b'c7adac82.0', b'c3705638.0']:
            cafile = join_bytes_or_unicode(capath, name)
            with open(cafile, 'w') as fObj:
                fObj.write(cleartextCertificatePEM.decode('ascii'))

        self._load_verify_locations_test(None, capath)


    def test_load_verify_directory_bytes_capath(self):
        """
        :py:obj:`Context.load_verify_locations` accepts a directory name as a
        ``bytes`` instance and uses the certificates within for verification
        purposes.
        """
        self._load_verify_directory_locations_capath(
            self.mktemp() + NON_ASCII.encode(getfilesystemencoding())
        )


    def test_load_verify_directory_unicode_capath(self):
        """
        :py:obj:`Context.load_verify_locations` accepts a directory name as a
        ``unicode`` instance and uses the certificates within for verification
        purposes.
        """
        self._load_verify_directory_locations_capath(
            self.mktemp().decode(getfilesystemencoding()) + NON_ASCII
        )


    def test_load_verify_locations_wrong_args(self):
        """
        :py:obj:`Context.load_verify_locations` raises :py:obj:`TypeError` if called with
        the wrong number of arguments or with non-:py:obj:`str` arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.load_verify_locations)
        self.assertRaises(TypeError, context.load_verify_locations, object())
        self.assertRaises(TypeError, context.load_verify_locations, object(), object())
        self.assertRaises(TypeError, context.load_verify_locations, None, None, None)


    if platform == "win32":
        "set_default_verify_paths appears not to work on Windows.  "
        "See LP#404343 and LP#404344."
    else:
        def test_set_default_verify_paths(self):
            """
            :py:obj:`Context.set_default_verify_paths` causes the platform-specific CA
            certificate locations to be used for verification purposes.
            """
            # Testing this requires a server with a certificate signed by one of
            # the CAs in the platform CA location.  Getting one of those costs
            # money.  Fortunately (or unfortunately, depending on your
            # perspective), it's easy to think of a public server on the
            # internet which has such a certificate.  Connecting to the network
            # in a unit test is bad, but it's the only way I can think of to
            # really test this. -exarkun

            # Arg, verisign.com doesn't speak anything newer than TLS 1.0
            context = Context(TLSv1_METHOD)
            context.set_default_verify_paths()
            context.set_verify(
                VERIFY_PEER,
                lambda conn, cert, errno, depth, preverify_ok: preverify_ok)

            client = socket()
            client.connect(('verisign.com', 443))
            clientSSL = Connection(context, client)
            clientSSL.set_connect_state()
            clientSSL.do_handshake()
            clientSSL.send(b"GET / HTTP/1.0\r\n\r\n")
            self.assertTrue(clientSSL.recv(1024))


    def test_set_default_verify_paths_signature(self):
        """
        :py:obj:`Context.set_default_verify_paths` takes no arguments and raises
        :py:obj:`TypeError` if given any.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_default_verify_paths, None)
        self.assertRaises(TypeError, context.set_default_verify_paths, 1)
        self.assertRaises(TypeError, context.set_default_verify_paths, "")


    def test_add_extra_chain_cert_invalid_cert(self):
        """
        :py:obj:`Context.add_extra_chain_cert` raises :py:obj:`TypeError` if called with
        other than one argument or if called with an object which is not an
        instance of :py:obj:`X509`.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.add_extra_chain_cert)
        self.assertRaises(TypeError, context.add_extra_chain_cert, object())
        self.assertRaises(TypeError, context.add_extra_chain_cert, object(), object())


    def _handshake_test(self, serverContext, clientContext):
        """
        Verify that a client and server created with the given contexts can
        successfully handshake and communicate.
        """
        serverSocket, clientSocket = socket_pair()

        server = Connection(serverContext, serverSocket)
        server.set_accept_state()

        client = Connection(clientContext, clientSocket)
        client.set_connect_state()

        # Make them talk to each other.
        # self._interactInMemory(client, server)
        for i in range(3):
            for s in [client, server]:
                try:
                    s.do_handshake()
                except WantReadError:
                    pass


    def test_set_verify_callback_connection_argument(self):
        """
        The first argument passed to the verify callback is the
        :py:class:`Connection` instance for which verification is taking place.
        """
        serverContext = Context(TLSv1_METHOD)
        serverContext.use_privatekey(
            load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM))
        serverContext.use_certificate(
            load_certificate(FILETYPE_PEM, cleartextCertificatePEM))
        serverConnection = Connection(serverContext, None)

        class VerifyCallback(object):
            def callback(self, connection, *args):
                self.connection = connection
                return 1

        verify = VerifyCallback()
        clientContext = Context(TLSv1_METHOD)
        clientContext.set_verify(VERIFY_PEER, verify.callback)
        clientConnection = Connection(clientContext, None)
        clientConnection.set_connect_state()

        self._handshakeInMemory(clientConnection, serverConnection)

        self.assertIdentical(verify.connection, clientConnection)


    def test_set_verify_callback_exception(self):
        """
        If the verify callback passed to :py:obj:`Context.set_verify` raises an
        exception, verification fails and the exception is propagated to the
        caller of :py:obj:`Connection.do_handshake`.
        """
        serverContext = Context(TLSv1_METHOD)
        serverContext.use_privatekey(
            load_privatekey(FILETYPE_PEM, cleartextPrivateKeyPEM))
        serverContext.use_certificate(
            load_certificate(FILETYPE_PEM, cleartextCertificatePEM))

        clientContext = Context(TLSv1_METHOD)
        def verify_callback(*args):
            raise Exception("silly verify failure")
        clientContext.set_verify(VERIFY_PEER, verify_callback)

        exc = self.assertRaises(
            Exception, self._handshake_test, serverContext, clientContext)
        self.assertEqual("silly verify failure", str(exc))


    def test_add_extra_chain_cert(self):
        """
        :py:obj:`Context.add_extra_chain_cert` accepts an :py:obj:`X509` instance to add to
        the certificate chain.

        See :py:obj:`_create_certificate_chain` for the details of the certificate
        chain tested.

        The chain is tested by starting a server with scert and connecting
        to it with a client which trusts cacert and requires verification to
        succeed.
        """
        chain = _create_certificate_chain()
        [(cakey, cacert), (ikey, icert), (skey, scert)] = chain

        # Dump the CA certificate to a file because that's the only way to load
        # it as a trusted CA in the client context.
        for cert, name in [(cacert, 'ca.pem'), (icert, 'i.pem'), (scert, 's.pem')]:
            fObj = open(name, 'w')
            fObj.write(dump_certificate(FILETYPE_PEM, cert).decode('ascii'))
            fObj.close()

        for key, name in [(cakey, 'ca.key'), (ikey, 'i.key'), (skey, 's.key')]:
            fObj = open(name, 'w')
            fObj.write(dump_privatekey(FILETYPE_PEM, key).decode('ascii'))
            fObj.close()

        # Create the server context
        serverContext = Context(TLSv1_METHOD)
        serverContext.use_privatekey(skey)
        serverContext.use_certificate(scert)
        # The client already has cacert, we only need to give them icert.
        serverContext.add_extra_chain_cert(icert)

        # Create the client
        clientContext = Context(TLSv1_METHOD)
        clientContext.set_verify(
            VERIFY_PEER | VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
        clientContext.load_verify_locations(b"ca.pem")

        # Try it out.
        self._handshake_test(serverContext, clientContext)


    def _use_certificate_chain_file_test(self, certdir):
        """
        Verify that :py:obj:`Context.use_certificate_chain_file` reads a
        certificate chain from a specified file.

        The chain is tested by starting a server with scert and connecting to
        it with a client which trusts cacert and requires verification to
        succeed.
        """
        chain = _create_certificate_chain()
        [(cakey, cacert), (ikey, icert), (skey, scert)] = chain

        makedirs(certdir)

        chainFile = join_bytes_or_unicode(certdir, "chain.pem")
        caFile = join_bytes_or_unicode(certdir, "ca.pem")

        # Write out the chain file.
        with open(chainFile, 'wb') as fObj:
            # Most specific to least general.
            fObj.write(dump_certificate(FILETYPE_PEM, scert))
            fObj.write(dump_certificate(FILETYPE_PEM, icert))
            fObj.write(dump_certificate(FILETYPE_PEM, cacert))

        with open(caFile, 'w') as fObj:
            fObj.write(dump_certificate(FILETYPE_PEM, cacert).decode('ascii'))

        serverContext = Context(TLSv1_METHOD)
        serverContext.use_certificate_chain_file(chainFile)
        serverContext.use_privatekey(skey)

        clientContext = Context(TLSv1_METHOD)
        clientContext.set_verify(
            VERIFY_PEER | VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb)
        clientContext.load_verify_locations(caFile)

        self._handshake_test(serverContext, clientContext)


    def test_use_certificate_chain_file_bytes(self):
        """
        ``Context.use_certificate_chain_file`` accepts the name of a file (as
        an instance of ``bytes``) to specify additional certificates to use to
        construct and verify a trust chain.
        """
        self._use_certificate_chain_file_test(
            self.mktemp() + NON_ASCII.encode(getfilesystemencoding())
        )


    def test_use_certificate_chain_file_unicode(self):
        """
        ``Context.use_certificate_chain_file`` accepts the name of a file (as
        an instance of ``unicode``) to specify additional certificates to use
        to construct and verify a trust chain.
        """
        self._use_certificate_chain_file_test(
            self.mktemp().decode(getfilesystemencoding()) + NON_ASCII
        )


    def test_use_certificate_chain_file_wrong_args(self):
        """
        :py:obj:`Context.use_certificate_chain_file` raises :py:obj:`TypeError`
        if passed zero or more than one argument or when passed a non-byte
        string single argument.  It also raises :py:obj:`OpenSSL.SSL.Error` when
        passed a bad chain file name (for example, the name of a file which does
        not exist).
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.use_certificate_chain_file)
        self.assertRaises(TypeError, context.use_certificate_chain_file, object())
        self.assertRaises(TypeError, context.use_certificate_chain_file, b"foo", object())

        self.assertRaises(Error, context.use_certificate_chain_file, self.mktemp())

    # XXX load_client_ca
    # XXX set_session_id

    def test_get_verify_mode_wrong_args(self):
        """
        :py:obj:`Context.get_verify_mode` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.get_verify_mode, None)


    def test_set_verify_mode(self):
        """
        :py:obj:`Context.get_verify_mode` returns the verify mode flags previously
        passed to :py:obj:`Context.set_verify`.
        """
        context = Context(TLSv1_METHOD)
        self.assertEquals(context.get_verify_mode(), 0)
        context.set_verify(
            VERIFY_PEER | VERIFY_CLIENT_ONCE, lambda *args: None)
        self.assertEquals(
            context.get_verify_mode(), VERIFY_PEER | VERIFY_CLIENT_ONCE)


    if not PY3:
        def test_set_verify_mode_long(self):
            """
            On Python 2 :py:obj:`Context.set_verify_mode` accepts values of
            type :py:obj:`long` as well as :py:obj:`int`.
            """
            context = Context(TLSv1_METHOD)
            self.assertEquals(context.get_verify_mode(), 0)
            context.set_verify(
                long(VERIFY_PEER | VERIFY_CLIENT_ONCE), lambda *args: None)
            self.assertEquals(
                context.get_verify_mode(), VERIFY_PEER | VERIFY_CLIENT_ONCE)


    def test_load_tmp_dh_wrong_args(self):
        """
        :py:obj:`Context.load_tmp_dh` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or with a non-:py:obj:`str` argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.load_tmp_dh)
        self.assertRaises(TypeError, context.load_tmp_dh, "foo", None)
        self.assertRaises(TypeError, context.load_tmp_dh, object())


    def test_load_tmp_dh_missing_file(self):
        """
        :py:obj:`Context.load_tmp_dh` raises :py:obj:`OpenSSL.SSL.Error` if the specified file
        does not exist.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(Error, context.load_tmp_dh, b"hello")


    def _load_tmp_dh_test(self, dhfilename):
        """
        Verify that calling ``Context.load_tmp_dh`` with the given filename
        does not raise an exception.
        """
        context = Context(TLSv1_METHOD)
        with open(dhfilename, "w") as dhfile:
            dhfile.write(dhparam)

        context.load_tmp_dh(dhfilename)
        # XXX What should I assert here? -exarkun


    def test_load_tmp_dh_bytes(self):
        """
        :py:obj:`Context.load_tmp_dh` loads Diffie-Hellman parameters from the
        specified file (given as ``bytes``).
        """
        self._load_tmp_dh_test(
            self.mktemp() + NON_ASCII.encode(getfilesystemencoding()),
        )


    def test_load_tmp_dh_unicode(self):
        """
        :py:obj:`Context.load_tmp_dh` loads Diffie-Hellman parameters from the
        specified file (given as ``unicode``).
        """
        self._load_tmp_dh_test(
            self.mktemp().decode(getfilesystemencoding()) + NON_ASCII,
        )


    def test_set_tmp_ecdh(self):
        """
        :py:obj:`Context.set_tmp_ecdh` sets the elliptic curve for
        Diffie-Hellman to the specified curve.
        """
        context = Context(TLSv1_METHOD)
        for curve in get_elliptic_curves():
            # The only easily "assertable" thing is that it does not raise an
            # exception.
            context.set_tmp_ecdh(curve)


    def test_set_cipher_list_bytes(self):
        """
        :py:obj:`Context.set_cipher_list` accepts a :py:obj:`bytes` naming the
        ciphers which connections created with the context object will be able
        to choose from.
        """
        context = Context(TLSv1_METHOD)
        context.set_cipher_list(b"hello world:EXP-RC4-MD5")
        conn = Connection(context, None)
        self.assertEquals(conn.get_cipher_list(), ["EXP-RC4-MD5"])


    def test_set_cipher_list_text(self):
        """
        :py:obj:`Context.set_cipher_list` accepts a :py:obj:`unicode` naming
        the ciphers which connections created with the context object will be
        able to choose from.
        """
        context = Context(TLSv1_METHOD)
        context.set_cipher_list(u("hello world:EXP-RC4-MD5"))
        conn = Connection(context, None)
        self.assertEquals(conn.get_cipher_list(), ["EXP-RC4-MD5"])


    def test_set_cipher_list_wrong_args(self):
        """
        :py:obj:`Context.set_cipher_list` raises :py:obj:`TypeError` when
        passed zero arguments or more than one argument or when passed a
        non-string single argument and raises :py:obj:`OpenSSL.SSL.Error` when
        passed an incorrect cipher list string.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_cipher_list)
        self.assertRaises(TypeError, context.set_cipher_list, object())
        self.assertRaises(TypeError, context.set_cipher_list, b"EXP-RC4-MD5", object())

        self.assertRaises(Error, context.set_cipher_list, "imaginary-cipher")


    def test_set_session_cache_mode_wrong_args(self):
        """
        :py:obj:`Context.set_session_cache_mode` raises :py:obj:`TypeError` if
        called with other than one integer argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_session_cache_mode)
        self.assertRaises(TypeError, context.set_session_cache_mode, object())


    def test_get_session_cache_mode_wrong_args(self):
        """
        :py:obj:`Context.get_session_cache_mode` raises :py:obj:`TypeError` if
        called with any arguments.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.get_session_cache_mode, 1)


    def test_session_cache_mode(self):
        """
        :py:obj:`Context.set_session_cache_mode` specifies how sessions are
        cached.  The setting can be retrieved via
        :py:obj:`Context.get_session_cache_mode`.
        """
        context = Context(TLSv1_METHOD)
        context.set_session_cache_mode(SESS_CACHE_OFF)
        off = context.set_session_cache_mode(SESS_CACHE_BOTH)
        self.assertEqual(SESS_CACHE_OFF, off)
        self.assertEqual(SESS_CACHE_BOTH, context.get_session_cache_mode())

    if not PY3:
        def test_session_cache_mode_long(self):
            """
            On Python 2 :py:obj:`Context.set_session_cache_mode` accepts values
            of type :py:obj:`long` as well as :py:obj:`int`.
            """
            context = Context(TLSv1_METHOD)
            context.set_session_cache_mode(long(SESS_CACHE_BOTH))
            self.assertEqual(
                SESS_CACHE_BOTH, context.get_session_cache_mode())


    def test_get_cert_store(self):
        """
        :py:obj:`Context.get_cert_store` returns a :py:obj:`X509Store` instance.
        """
        context = Context(TLSv1_METHOD)
        store = context.get_cert_store()
        self.assertIsInstance(store, X509Store)



class ServerNameCallbackTests(TestCase, _LoopbackMixin):
    """
    Tests for :py:obj:`Context.set_tlsext_servername_callback` and its interaction with
    :py:obj:`Connection`.
    """
    def test_wrong_args(self):
        """
        :py:obj:`Context.set_tlsext_servername_callback` raises :py:obj:`TypeError` if called
        with other than one argument.
        """
        context = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, context.set_tlsext_servername_callback)
        self.assertRaises(
            TypeError, context.set_tlsext_servername_callback, 1, 2)


    def test_old_callback_forgotten(self):
        """
        If :py:obj:`Context.set_tlsext_servername_callback` is used to specify a new
        callback, the one it replaces is dereferenced.
        """
        def callback(connection):
            pass

        def replacement(connection):
            pass

        context = Context(TLSv1_METHOD)
        context.set_tlsext_servername_callback(callback)

        tracker = ref(callback)
        del callback

        context.set_tlsext_servername_callback(replacement)

        # One run of the garbage collector happens to work on CPython.  PyPy
        # doesn't collect the underlying object until a second run for whatever
        # reason.  That's fine, it still demonstrates our code has properly
        # dropped the reference.
        collect()
        collect()

        callback = tracker()
        if callback is not None:
            referrers = get_referrers(callback)
            if len(referrers) > 1:
                self.fail("Some references remain: %r" % (referrers,))


    def test_no_servername(self):
        """
        When a client specifies no server name, the callback passed to
        :py:obj:`Context.set_tlsext_servername_callback` is invoked and the result of
        :py:obj:`Connection.get_servername` is :py:obj:`None`.
        """
        args = []
        def servername(conn):
            args.append((conn, conn.get_servername()))
        context = Context(TLSv1_METHOD)
        context.set_tlsext_servername_callback(servername)

        # Lose our reference to it.  The Context is responsible for keeping it
        # alive now.
        del servername
        collect()

        # Necessary to actually accept the connection
        context.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        context.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))

        # Do a little connection to trigger the logic
        server = Connection(context, None)
        server.set_accept_state()

        client = Connection(Context(TLSv1_METHOD), None)
        client.set_connect_state()

        self._interactInMemory(server, client)

        self.assertEqual([(server, None)], args)


    def test_servername(self):
        """
        When a client specifies a server name in its hello message, the callback
        passed to :py:obj:`Contexts.set_tlsext_servername_callback` is invoked and the
        result of :py:obj:`Connection.get_servername` is that server name.
        """
        args = []
        def servername(conn):
            args.append((conn, conn.get_servername()))
        context = Context(TLSv1_METHOD)
        context.set_tlsext_servername_callback(servername)

        # Necessary to actually accept the connection
        context.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        context.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))

        # Do a little connection to trigger the logic
        server = Connection(context, None)
        server.set_accept_state()

        client = Connection(Context(TLSv1_METHOD), None)
        client.set_connect_state()
        client.set_tlsext_host_name(b("foo1.example.com"))

        self._interactInMemory(server, client)

        self.assertEqual([(server, b("foo1.example.com"))], args)


class NextProtoNegotiationTests(TestCase, _LoopbackMixin):
    """
    Test for Next Protocol Negotiation in PyOpenSSL.
    """
    if _lib.Cryptography_HAS_NEXTPROTONEG:
        def test_npn_success(self):
            """
            Tests that clients and servers that agree on the negotiated next
            protocol can correct establish a connection, and that the agreed
            protocol is reported by the connections.
            """
            advertise_args = []
            select_args = []
            def advertise(conn):
                advertise_args.append((conn,))
                return [b'http/1.1', b'spdy/2']
            def select(conn, options):
                select_args.append((conn, options))
                return b'spdy/2'

            server_context = Context(TLSv1_METHOD)
            server_context.set_npn_advertise_callback(advertise)

            client_context = Context(TLSv1_METHOD)
            client_context.set_npn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            self._interactInMemory(server, client)

            self.assertEqual([(server,)], advertise_args)
            self.assertEqual([(client, [b'http/1.1', b'spdy/2'])], select_args)

            self.assertEqual(server.get_next_proto_negotiated(), b'spdy/2')
            self.assertEqual(client.get_next_proto_negotiated(), b'spdy/2')


        def test_npn_client_fail(self):
            """
            Tests that when clients and servers cannot agree on what protocol
            to use next that the TLS connection does not get established.
            """
            advertise_args = []
            select_args = []
            def advertise(conn):
                advertise_args.append((conn,))
                return [b'http/1.1', b'spdy/2']
            def select(conn, options):
                select_args.append((conn, options))
                return b''

            server_context = Context(TLSv1_METHOD)
            server_context.set_npn_advertise_callback(advertise)

            client_context = Context(TLSv1_METHOD)
            client_context.set_npn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            # If the client doesn't return anything, the connection will fail.
            self.assertRaises(Error, self._interactInMemory, server, client)

            self.assertEqual([(server,)], advertise_args)
            self.assertEqual([(client, [b'http/1.1', b'spdy/2'])], select_args)


        def test_npn_select_error(self):
            """
            Test that we can handle exceptions in the select callback. If
            select fails it should be fatal to the connection.
            """
            advertise_args = []
            def advertise(conn):
                advertise_args.append((conn,))
                return [b'http/1.1', b'spdy/2']
            def select(conn, options):
                raise TypeError

            server_context = Context(TLSv1_METHOD)
            server_context.set_npn_advertise_callback(advertise)

            client_context = Context(TLSv1_METHOD)
            client_context.set_npn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            # If the callback throws an exception it should be raised here.
            self.assertRaises(
                TypeError, self._interactInMemory, server, client
            )
            self.assertEqual([(server,)], advertise_args)


        def test_npn_advertise_error(self):
            """
            Test that we can handle exceptions in the advertise callback. If
            advertise fails no NPN is advertised to the client.
            """
            select_args = []
            def advertise(conn):
                raise TypeError
            def select(conn, options):
                select_args.append((conn, options))
                return b''

            server_context = Context(TLSv1_METHOD)
            server_context.set_npn_advertise_callback(advertise)

            client_context = Context(TLSv1_METHOD)
            client_context.set_npn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            # If the client doesn't return anything, the connection will fail.
            self.assertRaises(
                TypeError, self._interactInMemory, server, client
            )
            self.assertEqual([], select_args)

    else:
        # No NPN.
        def test_npn_not_implemented(self):
            # Test the context methods first.
            context = Context(TLSv1_METHOD)
            fail_methods = [
                context.set_npn_advertise_callback,
                context.set_npn_select_callback,
            ]
            for method in fail_methods:
                self.assertRaises(
                    NotImplementedError, method, None
                )

            # Now test a connection.
            conn = Connection(context)
            fail_methods = [
                conn.get_next_proto_negotiated,
            ]
            for method in fail_methods:
                self.assertRaises(NotImplementedError, method)



class ApplicationLayerProtoNegotiationTests(TestCase, _LoopbackMixin):
    """
    Tests for ALPN in PyOpenSSL.
    """
    # Skip tests on versions that don't support ALPN.
    if _lib.Cryptography_HAS_ALPN:

        def test_alpn_success(self):
            """
            Clients and servers that agree on the negotiated ALPN protocol can
            correct establish a connection, and the agreed protocol is reported
            by the connections.
            """
            select_args = []
            def select(conn, options):
                select_args.append((conn, options))
                return b'spdy/2'

            client_context = Context(TLSv1_METHOD)
            client_context.set_alpn_protos([b'http/1.1', b'spdy/2'])

            server_context = Context(TLSv1_METHOD)
            server_context.set_alpn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            self._interactInMemory(server, client)

            self.assertEqual([(server, [b'http/1.1', b'spdy/2'])], select_args)

            self.assertEqual(server.get_alpn_proto_negotiated(), b'spdy/2')
            self.assertEqual(client.get_alpn_proto_negotiated(), b'spdy/2')


        def test_alpn_set_on_connection(self):
            """
            The same as test_alpn_success, but setting the ALPN protocols on
            the connection rather than the context.
            """
            select_args = []
            def select(conn, options):
                select_args.append((conn, options))
                return b'spdy/2'

            # Setup the client context but don't set any ALPN protocols.
            client_context = Context(TLSv1_METHOD)

            server_context = Context(TLSv1_METHOD)
            server_context.set_alpn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            # Set the ALPN protocols on the client connection.
            client = Connection(client_context, None)
            client.set_alpn_protos([b'http/1.1', b'spdy/2'])
            client.set_connect_state()

            self._interactInMemory(server, client)

            self.assertEqual([(server, [b'http/1.1', b'spdy/2'])], select_args)

            self.assertEqual(server.get_alpn_proto_negotiated(), b'spdy/2')
            self.assertEqual(client.get_alpn_proto_negotiated(), b'spdy/2')


        def test_alpn_server_fail(self):
            """
            When clients and servers cannot agree on what protocol to use next
            the TLS connection does not get established.
            """
            select_args = []
            def select(conn, options):
                select_args.append((conn, options))
                return b''

            client_context = Context(TLSv1_METHOD)
            client_context.set_alpn_protos([b'http/1.1', b'spdy/2'])

            server_context = Context(TLSv1_METHOD)
            server_context.set_alpn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            # If the client doesn't return anything, the connection will fail.
            self.assertRaises(Error, self._interactInMemory, server, client)

            self.assertEqual([(server, [b'http/1.1', b'spdy/2'])], select_args)


        def test_alpn_no_server(self):
            """
            When clients and servers cannot agree on what protocol to use next
            because the server doesn't offer ALPN, no protocol is negotiated.
            """
            client_context = Context(TLSv1_METHOD)
            client_context.set_alpn_protos([b'http/1.1', b'spdy/2'])

            server_context = Context(TLSv1_METHOD)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            # Do the dance.
            self._interactInMemory(server, client)

            self.assertEqual(client.get_alpn_proto_negotiated(), b'')


        def test_alpn_callback_exception(self):
            """
            We can handle exceptions in the ALPN select callback.
            """
            select_args = []
            def select(conn, options):
                select_args.append((conn, options))
                raise TypeError()

            client_context = Context(TLSv1_METHOD)
            client_context.set_alpn_protos([b'http/1.1', b'spdy/2'])

            server_context = Context(TLSv1_METHOD)
            server_context.set_alpn_select_callback(select)

            # Necessary to actually accept the connection
            server_context.use_privatekey(
                load_privatekey(FILETYPE_PEM, server_key_pem))
            server_context.use_certificate(
                load_certificate(FILETYPE_PEM, server_cert_pem))

            # Do a little connection to trigger the logic
            server = Connection(server_context, None)
            server.set_accept_state()

            client = Connection(client_context, None)
            client.set_connect_state()

            self.assertRaises(
                TypeError, self._interactInMemory, server, client
            )
            self.assertEqual([(server, [b'http/1.1', b'spdy/2'])], select_args)

    else:
        # No ALPN.
        def test_alpn_not_implemented(self):
            """
            If ALPN is not in OpenSSL, we should raise NotImplementedError.
            """
            # Test the context methods first.
            context = Context(TLSv1_METHOD)
            self.assertRaises(
                NotImplementedError, context.set_alpn_protos, None
            )
            self.assertRaises(
                NotImplementedError, context.set_alpn_select_callback, None
            )

            # Now test a connection.
            conn = Connection(context)
            self.assertRaises(
                NotImplementedError, context.set_alpn_protos, None
            )



class SessionTests(TestCase):
    """
    Unit tests for :py:obj:`OpenSSL.SSL.Session`.
    """
    def test_construction(self):
        """
        :py:class:`Session` can be constructed with no arguments, creating a new
        instance of that type.
        """
        new_session = Session()
        self.assertTrue(isinstance(new_session, Session))


    def test_construction_wrong_args(self):
        """
        If any arguments are passed to :py:class:`Session`, :py:obj:`TypeError`
        is raised.
        """
        self.assertRaises(TypeError, Session, 123)
        self.assertRaises(TypeError, Session, "hello")
        self.assertRaises(TypeError, Session, object())



class ConnectionTests(TestCase, _LoopbackMixin):
    """
    Unit tests for :py:obj:`OpenSSL.SSL.Connection`.
    """
    # XXX get_peer_certificate -> None
    # XXX sock_shutdown
    # XXX master_key -> TypeError
    # XXX server_random -> TypeError
    # XXX state_string
    # XXX connect -> TypeError
    # XXX connect_ex -> TypeError
    # XXX set_connect_state -> TypeError
    # XXX set_accept_state -> TypeError
    # XXX renegotiate_pending
    # XXX do_handshake -> TypeError
    # XXX bio_read -> TypeError
    # XXX recv -> TypeError
    # XXX send -> TypeError
    # XXX bio_write -> TypeError

    def test_type(self):
        """
        :py:obj:`Connection` and :py:obj:`ConnectionType` refer to the same type object and
        can be used to create instances of that type.
        """
        self.assertIdentical(Connection, ConnectionType)
        ctx = Context(TLSv1_METHOD)
        self.assertConsistentType(Connection, 'Connection', ctx, None)


    def test_get_context(self):
        """
        :py:obj:`Connection.get_context` returns the :py:obj:`Context` instance used to
        construct the :py:obj:`Connection` instance.
        """
        context = Context(TLSv1_METHOD)
        connection = Connection(context, None)
        self.assertIdentical(connection.get_context(), context)


    def test_get_context_wrong_args(self):
        """
        :py:obj:`Connection.get_context` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.get_context, None)


    def test_set_context_wrong_args(self):
        """
        :py:obj:`Connection.set_context` raises :py:obj:`TypeError` if called with a
        non-:py:obj:`Context` instance argument or with any number of arguments other
        than 1.
        """
        ctx = Context(TLSv1_METHOD)
        connection = Connection(ctx, None)
        self.assertRaises(TypeError, connection.set_context)
        self.assertRaises(TypeError, connection.set_context, object())
        self.assertRaises(TypeError, connection.set_context, "hello")
        self.assertRaises(TypeError, connection.set_context, 1)
        self.assertRaises(TypeError, connection.set_context, 1, 2)
        self.assertRaises(
            TypeError, connection.set_context, Context(TLSv1_METHOD), 2)
        self.assertIdentical(ctx, connection.get_context())


    def test_set_context(self):
        """
        :py:obj:`Connection.set_context` specifies a new :py:obj:`Context` instance to be used
        for the connection.
        """
        original = Context(SSLv23_METHOD)
        replacement = Context(TLSv1_METHOD)
        connection = Connection(original, None)
        connection.set_context(replacement)
        self.assertIdentical(replacement, connection.get_context())
        # Lose our references to the contexts, just in case the Connection isn't
        # properly managing its own contributions to their reference counts.
        del original, replacement
        collect()


    def test_set_tlsext_host_name_wrong_args(self):
        """
        If :py:obj:`Connection.set_tlsext_host_name` is called with a non-byte string
        argument or a byte string with an embedded NUL or other than one
        argument, :py:obj:`TypeError` is raised.
        """
        conn = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, conn.set_tlsext_host_name)
        self.assertRaises(TypeError, conn.set_tlsext_host_name, object())
        self.assertRaises(TypeError, conn.set_tlsext_host_name, 123, 456)
        self.assertRaises(
            TypeError, conn.set_tlsext_host_name, b("with\0null"))

        if PY3:
            # On Python 3.x, don't accidentally implicitly convert from text.
            self.assertRaises(
                TypeError,
                conn.set_tlsext_host_name, b("example.com").decode("ascii"))


    def test_get_servername_wrong_args(self):
        """
        :py:obj:`Connection.get_servername` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.get_servername, object())
        self.assertRaises(TypeError, connection.get_servername, 1)
        self.assertRaises(TypeError, connection.get_servername, "hello")


    def test_pending(self):
        """
        :py:obj:`Connection.pending` returns the number of bytes available for
        immediate read.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertEquals(connection.pending(), 0)


    def test_pending_wrong_args(self):
        """
        :py:obj:`Connection.pending` raises :py:obj:`TypeError` if called with any arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.pending, None)


    def test_connect_wrong_args(self):
        """
        :py:obj:`Connection.connect` raises :py:obj:`TypeError` if called with a non-address
        argument or with the wrong number of arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), socket())
        self.assertRaises(TypeError, connection.connect, None)
        self.assertRaises(TypeError, connection.connect)
        self.assertRaises(TypeError, connection.connect, ("127.0.0.1", 1), None)


    def test_connect_refused(self):
        """
        :py:obj:`Connection.connect` raises :py:obj:`socket.error` if the underlying socket
        connect method raises it.
        """
        client = socket()
        context = Context(TLSv1_METHOD)
        clientSSL = Connection(context, client)
        exc = self.assertRaises(error, clientSSL.connect, ("127.0.0.1", 1))
        self.assertEquals(exc.args[0], ECONNREFUSED)


    def test_connect(self):
        """
        :py:obj:`Connection.connect` establishes a connection to the specified address.
        """
        port = socket()
        port.bind(('', 0))
        port.listen(3)

        clientSSL = Connection(Context(TLSv1_METHOD), socket())
        clientSSL.connect(('127.0.0.1', port.getsockname()[1]))
        # XXX An assertion?  Or something?


    if platform == "darwin":
        "connect_ex sometimes causes a kernel panic on OS X 10.6.4"
    else:
        def test_connect_ex(self):
            """
            If there is a connection error, :py:obj:`Connection.connect_ex` returns the
            errno instead of raising an exception.
            """
            port = socket()
            port.bind(('', 0))
            port.listen(3)

            clientSSL = Connection(Context(TLSv1_METHOD), socket())
            clientSSL.setblocking(False)
            result = clientSSL.connect_ex(port.getsockname())
            expected = (EINPROGRESS, EWOULDBLOCK)
            self.assertTrue(
                    result in expected, "%r not in %r" % (result, expected))


    def test_accept_wrong_args(self):
        """
        :py:obj:`Connection.accept` raises :py:obj:`TypeError` if called with any arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), socket())
        self.assertRaises(TypeError, connection.accept, None)


    def test_accept(self):
        """
        :py:obj:`Connection.accept` accepts a pending connection attempt and returns a
        tuple of a new :py:obj:`Connection` (the accepted client) and the address the
        connection originated from.
        """
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        ctx.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))
        port = socket()
        portSSL = Connection(ctx, port)
        portSSL.bind(('', 0))
        portSSL.listen(3)

        clientSSL = Connection(Context(TLSv1_METHOD), socket())

        # Calling portSSL.getsockname() here to get the server IP address sounds
        # great, but frequently fails on Windows.
        clientSSL.connect(('127.0.0.1', portSSL.getsockname()[1]))

        serverSSL, address = portSSL.accept()

        self.assertTrue(isinstance(serverSSL, Connection))
        self.assertIdentical(serverSSL.get_context(), ctx)
        self.assertEquals(address, clientSSL.getsockname())


    def test_shutdown_wrong_args(self):
        """
        :py:obj:`Connection.shutdown` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or with arguments other than integers.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.shutdown, None)
        self.assertRaises(TypeError, connection.get_shutdown, None)
        self.assertRaises(TypeError, connection.set_shutdown)
        self.assertRaises(TypeError, connection.set_shutdown, None)
        self.assertRaises(TypeError, connection.set_shutdown, 0, 1)


    def test_shutdown(self):
        """
        :py:obj:`Connection.shutdown` performs an SSL-level connection shutdown.
        """
        server, client = self._loopback()
        self.assertFalse(server.shutdown())
        self.assertEquals(server.get_shutdown(), SENT_SHUTDOWN)
        self.assertRaises(ZeroReturnError, client.recv, 1024)
        self.assertEquals(client.get_shutdown(), RECEIVED_SHUTDOWN)
        client.shutdown()
        self.assertEquals(client.get_shutdown(), SENT_SHUTDOWN|RECEIVED_SHUTDOWN)
        self.assertRaises(ZeroReturnError, server.recv, 1024)
        self.assertEquals(server.get_shutdown(), SENT_SHUTDOWN|RECEIVED_SHUTDOWN)


    def test_shutdown_closed(self):
        """
        If the underlying socket is closed, :py:obj:`Connection.shutdown` propagates the
        write error from the low level write call.
        """
        server, client = self._loopback()
        server.sock_shutdown(2)
        exc = self.assertRaises(SysCallError, server.shutdown)
        if platform == "win32":
            self.assertEqual(exc.args[0], ESHUTDOWN)
        else:
            self.assertEqual(exc.args[0], EPIPE)


    def test_shutdown_truncated(self):
        """
        If the underlying connection is truncated, :obj:`Connection.shutdown`
        raises an :obj:`Error`.
        """
        server_ctx = Context(TLSv1_METHOD)
        client_ctx = Context(TLSv1_METHOD)
        server_ctx.use_privatekey(
            load_privatekey(FILETYPE_PEM, server_key_pem))
        server_ctx.use_certificate(
            load_certificate(FILETYPE_PEM, server_cert_pem))
        server = Connection(server_ctx, None)
        client = Connection(client_ctx, None)
        self._handshakeInMemory(client, server)
        self.assertEqual(server.shutdown(), False)
        self.assertRaises(WantReadError, server.shutdown)
        server.bio_shutdown()
        self.assertRaises(Error, server.shutdown)


    def test_set_shutdown(self):
        """
        :py:obj:`Connection.set_shutdown` sets the state of the SSL connection shutdown
        process.
        """
        connection = Connection(Context(TLSv1_METHOD), socket())
        connection.set_shutdown(RECEIVED_SHUTDOWN)
        self.assertEquals(connection.get_shutdown(), RECEIVED_SHUTDOWN)


    if not PY3:
        def test_set_shutdown_long(self):
            """
            On Python 2 :py:obj:`Connection.set_shutdown` accepts an argument
            of type :py:obj:`long` as well as :py:obj:`int`.
            """
            connection = Connection(Context(TLSv1_METHOD), socket())
            connection.set_shutdown(long(RECEIVED_SHUTDOWN))
            self.assertEquals(connection.get_shutdown(), RECEIVED_SHUTDOWN)


    def test_app_data_wrong_args(self):
        """
        :py:obj:`Connection.set_app_data` raises :py:obj:`TypeError` if called with other than
        one argument.  :py:obj:`Connection.get_app_data` raises :py:obj:`TypeError` if called
        with any arguments.
        """
        conn = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, conn.get_app_data, None)
        self.assertRaises(TypeError, conn.set_app_data)
        self.assertRaises(TypeError, conn.set_app_data, None, None)


    def test_app_data(self):
        """
        Any object can be set as app data by passing it to
        :py:obj:`Connection.set_app_data` and later retrieved with
        :py:obj:`Connection.get_app_data`.
        """
        conn = Connection(Context(TLSv1_METHOD), None)
        app_data = object()
        conn.set_app_data(app_data)
        self.assertIdentical(conn.get_app_data(), app_data)


    def test_makefile(self):
        """
        :py:obj:`Connection.makefile` is not implemented and calling that method raises
        :py:obj:`NotImplementedError`.
        """
        conn = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(NotImplementedError, conn.makefile)


    def test_get_peer_cert_chain_wrong_args(self):
        """
        :py:obj:`Connection.get_peer_cert_chain` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        conn = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, conn.get_peer_cert_chain, 1)
        self.assertRaises(TypeError, conn.get_peer_cert_chain, "foo")
        self.assertRaises(TypeError, conn.get_peer_cert_chain, object())
        self.assertRaises(TypeError, conn.get_peer_cert_chain, [])


    def test_get_peer_cert_chain(self):
        """
        :py:obj:`Connection.get_peer_cert_chain` returns a list of certificates which
        the connected server returned for the certification verification.
        """
        chain = _create_certificate_chain()
        [(cakey, cacert), (ikey, icert), (skey, scert)] = chain

        serverContext = Context(TLSv1_METHOD)
        serverContext.use_privatekey(skey)
        serverContext.use_certificate(scert)
        serverContext.add_extra_chain_cert(icert)
        serverContext.add_extra_chain_cert(cacert)
        server = Connection(serverContext, None)
        server.set_accept_state()

        # Create the client
        clientContext = Context(TLSv1_METHOD)
        clientContext.set_verify(VERIFY_NONE, verify_cb)
        client = Connection(clientContext, None)
        client.set_connect_state()

        self._interactInMemory(client, server)

        chain = client.get_peer_cert_chain()
        self.assertEqual(len(chain), 3)
        self.assertEqual(
            "Server Certificate", chain[0].get_subject().CN)
        self.assertEqual(
            "Intermediate Certificate", chain[1].get_subject().CN)
        self.assertEqual(
            "Authority Certificate", chain[2].get_subject().CN)


    def test_get_peer_cert_chain_none(self):
        """
        :py:obj:`Connection.get_peer_cert_chain` returns :py:obj:`None` if the peer sends no
        certificate chain.
        """
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        ctx.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))
        server = Connection(ctx, None)
        server.set_accept_state()
        client = Connection(Context(TLSv1_METHOD), None)
        client.set_connect_state()
        self._interactInMemory(client, server)
        self.assertIdentical(None, server.get_peer_cert_chain())


    def test_get_session_wrong_args(self):
        """
        :py:obj:`Connection.get_session` raises :py:obj:`TypeError` if called
        with any arguments.
        """
        ctx = Context(TLSv1_METHOD)
        server = Connection(ctx, None)
        self.assertRaises(TypeError, server.get_session, 123)
        self.assertRaises(TypeError, server.get_session, "hello")
        self.assertRaises(TypeError, server.get_session, object())


    def test_get_session_unconnected(self):
        """
        :py:obj:`Connection.get_session` returns :py:obj:`None` when used with
        an object which has not been connected.
        """
        ctx = Context(TLSv1_METHOD)
        server = Connection(ctx, None)
        session = server.get_session()
        self.assertIdentical(None, session)


    def test_server_get_session(self):
        """
        On the server side of a connection, :py:obj:`Connection.get_session`
        returns a :py:class:`Session` instance representing the SSL session for
        that connection.
        """
        server, client = self._loopback()
        session = server.get_session()
        self.assertIsInstance(session, Session)


    def test_client_get_session(self):
        """
        On the client side of a connection, :py:obj:`Connection.get_session`
        returns a :py:class:`Session` instance representing the SSL session for
        that connection.
        """
        server, client = self._loopback()
        session = client.get_session()
        self.assertIsInstance(session, Session)


    def test_set_session_wrong_args(self):
        """
        If called with an object that is not an instance of :py:class:`Session`,
        or with other than one argument, :py:obj:`Connection.set_session` raises
        :py:obj:`TypeError`.
        """
        ctx = Context(TLSv1_METHOD)
        connection = Connection(ctx, None)
        self.assertRaises(TypeError, connection.set_session)
        self.assertRaises(TypeError, connection.set_session, 123)
        self.assertRaises(TypeError, connection.set_session, "hello")
        self.assertRaises(TypeError, connection.set_session, object())
        self.assertRaises(
            TypeError, connection.set_session, Session(), Session())


    def test_client_set_session(self):
        """
        :py:obj:`Connection.set_session`, when used prior to a connection being
        established, accepts a :py:class:`Session` instance and causes an
        attempt to re-use the session it represents when the SSL handshake is
        performed.
        """
        key = load_privatekey(FILETYPE_PEM, server_key_pem)
        cert = load_certificate(FILETYPE_PEM, server_cert_pem)
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(key)
        ctx.use_certificate(cert)
        ctx.set_session_id("unity-test")

        def makeServer(socket):
            server = Connection(ctx, socket)
            server.set_accept_state()
            return server

        originalServer, originalClient = self._loopback(
            serverFactory=makeServer)
        originalSession = originalClient.get_session()

        def makeClient(socket):
            client = self._loopbackClientFactory(socket)
            client.set_session(originalSession)
            return client
        resumedServer, resumedClient = self._loopback(
            serverFactory=makeServer,
            clientFactory=makeClient)

        # This is a proxy: in general, we have no access to any unique
        # identifier for the session (new enough versions of OpenSSL expose a
        # hash which could be usable, but "new enough" is very, very new).
        # Instead, exploit the fact that the master key is re-used if the
        # session is re-used.  As long as the master key for the two connections
        # is the same, the session was re-used!
        self.assertEqual(
            originalServer.master_key(), resumedServer.master_key())


    def test_set_session_wrong_method(self):
        """
        If :py:obj:`Connection.set_session` is passed a :py:class:`Session`
        instance associated with a context using a different SSL method than the
        :py:obj:`Connection` is using, a :py:class:`OpenSSL.SSL.Error` is
        raised.
        """
        key = load_privatekey(FILETYPE_PEM, server_key_pem)
        cert = load_certificate(FILETYPE_PEM, server_cert_pem)
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(key)
        ctx.use_certificate(cert)
        ctx.set_session_id("unity-test")

        def makeServer(socket):
            server = Connection(ctx, socket)
            server.set_accept_state()
            return server

        originalServer, originalClient = self._loopback(
            serverFactory=makeServer)
        originalSession = originalClient.get_session()

        def makeClient(socket):
            # Intentionally use a different, incompatible method here.
            client = Connection(Context(SSLv3_METHOD), socket)
            client.set_connect_state()
            client.set_session(originalSession)
            return client

        self.assertRaises(
            Error,
            self._loopback, clientFactory=makeClient, serverFactory=makeServer)


    def test_wantWriteError(self):
        """
        :py:obj:`Connection` methods which generate output raise
        :py:obj:`OpenSSL.SSL.WantWriteError` if writing to the connection's BIO
        fail indicating a should-write state.
        """
        client_socket, server_socket = socket_pair()
        # Fill up the client's send buffer so Connection won't be able to write
        # anything.  Only write a single byte at a time so we can be sure we
        # completely fill the buffer.  Even though the socket API is allowed to
        # signal a short write via its return value it seems this doesn't
        # always happen on all platforms (FreeBSD and OS X particular) for the
        # very last bit of available buffer space.
        msg = b"x"
        for i in range(1024 * 1024 * 4):
            try:
                client_socket.send(msg)
            except error as e:
                if e.errno == EWOULDBLOCK:
                    break
                raise
        else:
            self.fail(
                "Failed to fill socket buffer, cannot test BIO want write")

        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, client_socket)
        # Client's speak first, so make it an SSL client
        conn.set_connect_state()
        self.assertRaises(WantWriteError, conn.do_handshake)

    # XXX want_read

    def test_get_finished_before_connect(self):
        """
        :py:obj:`Connection.get_finished` returns :py:obj:`None` before TLS
        handshake is completed.
        """
        ctx = Context(TLSv1_METHOD)
        connection = Connection(ctx, None)
        self.assertEqual(connection.get_finished(), None)


    def test_get_peer_finished_before_connect(self):
        """
        :py:obj:`Connection.get_peer_finished` returns :py:obj:`None` before
        TLS handshake is completed.
        """
        ctx = Context(TLSv1_METHOD)
        connection = Connection(ctx, None)
        self.assertEqual(connection.get_peer_finished(), None)


    def test_get_finished(self):
        """
        :py:obj:`Connection.get_finished` method returns the TLS Finished
        message send from client, or server. Finished messages are send during
        TLS handshake.
        """

        server, client = self._loopback()

        self.assertNotEqual(server.get_finished(), None)
        self.assertTrue(len(server.get_finished()) > 0)


    def test_get_peer_finished(self):
        """
        :py:obj:`Connection.get_peer_finished` method returns the TLS Finished
        message received from client, or server. Finished messages are send
        during TLS handshake.
        """
        server, client = self._loopback()

        self.assertNotEqual(server.get_peer_finished(), None)
        self.assertTrue(len(server.get_peer_finished()) > 0)


    def test_tls_finished_message_symmetry(self):
        """
        The TLS Finished message send by server must be the TLS Finished message
        received by client.

        The TLS Finished message send by client must be the TLS Finished message
        received by server.
        """
        server, client = self._loopback()

        self.assertEqual(server.get_finished(), client.get_peer_finished())
        self.assertEqual(client.get_finished(), server.get_peer_finished())


    def test_get_cipher_name_before_connect(self):
        """
        :py:obj:`Connection.get_cipher_name` returns :py:obj:`None` if no
        connection has been established.
        """
        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, None)
        self.assertIdentical(conn.get_cipher_name(), None)


    def test_get_cipher_name(self):
        """
        :py:obj:`Connection.get_cipher_name` returns a :py:class:`unicode`
        string giving the name of the currently used cipher.
        """
        server, client = self._loopback()
        server_cipher_name, client_cipher_name = \
            server.get_cipher_name(), client.get_cipher_name()

        self.assertIsInstance(server_cipher_name, text_type)
        self.assertIsInstance(client_cipher_name, text_type)

        self.assertEqual(server_cipher_name, client_cipher_name)


    def test_get_cipher_version_before_connect(self):
        """
        :py:obj:`Connection.get_cipher_version` returns :py:obj:`None` if no
        connection has been established.
        """
        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, None)
        self.assertIdentical(conn.get_cipher_version(), None)


    def test_get_cipher_version(self):
        """
        :py:obj:`Connection.get_cipher_version` returns a :py:class:`unicode`
        string giving the protocol name of the currently used cipher.
        """
        server, client = self._loopback()
        server_cipher_version, client_cipher_version = \
            server.get_cipher_version(), client.get_cipher_version()

        self.assertIsInstance(server_cipher_version, text_type)
        self.assertIsInstance(client_cipher_version, text_type)

        self.assertEqual(server_cipher_version, client_cipher_version)


    def test_get_cipher_bits_before_connect(self):
        """
        :py:obj:`Connection.get_cipher_bits` returns :py:obj:`None` if no
        connection has been established.
        """
        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, None)
        self.assertIdentical(conn.get_cipher_bits(), None)


    def test_get_cipher_bits(self):
        """
        :py:obj:`Connection.get_cipher_bits` returns the number of secret bits
        of the currently used cipher.
        """
        server, client = self._loopback()
        server_cipher_bits, client_cipher_bits = \
            server.get_cipher_bits(), client.get_cipher_bits()

        self.assertIsInstance(server_cipher_bits, int)
        self.assertIsInstance(client_cipher_bits, int)

        self.assertEqual(server_cipher_bits, client_cipher_bits)



class ConnectionGetCipherListTests(TestCase):
    """
    Tests for :py:obj:`Connection.get_cipher_list`.
    """
    def test_wrong_args(self):
        """
        :py:obj:`Connection.get_cipher_list` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.get_cipher_list, None)


    def test_result(self):
        """
        :py:obj:`Connection.get_cipher_list` returns a :py:obj:`list` of
        :py:obj:`bytes` giving the names of the ciphers which might be used.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        ciphers = connection.get_cipher_list()
        self.assertTrue(isinstance(ciphers, list))
        for cipher in ciphers:
            self.assertTrue(isinstance(cipher, str))



class ConnectionSendTests(TestCase, _LoopbackMixin):
    """
    Tests for :py:obj:`Connection.send`
    """
    def test_wrong_args(self):
        """
        When called with arguments other than string argument for its first
        parameter or more than two arguments, :py:obj:`Connection.send` raises
        :py:obj:`TypeError`.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.send)
        self.assertRaises(TypeError, connection.send, object())
        self.assertRaises(TypeError, connection.send, "foo", object(), "bar")


    def test_short_bytes(self):
        """
        When passed a short byte string, :py:obj:`Connection.send` transmits all of it
        and returns the number of bytes sent.
        """
        server, client = self._loopback()
        count = server.send(b('xy'))
        self.assertEquals(count, 2)
        self.assertEquals(client.recv(2), b('xy'))


    def test_text(self):
        """
        When passed a text, :py:obj:`Connection.send` transmits all of it and
        returns the number of bytes sent. It also raises a DeprecationWarning.
        """
        server, client = self._loopback()
        with catch_warnings(record=True) as w:
            simplefilter("always")
            count = server.send(b"xy".decode("ascii"))
            self.assertEqual(
                "{0} for buf is no longer accepted, use bytes".format(
                    WARNING_TYPE_EXPECTED
                ),
                str(w[-1].message)
            )
            self.assertIs(w[-1].category, DeprecationWarning)
        self.assertEquals(count, 2)
        self.assertEquals(client.recv(2), b"xy")

    try:
        memoryview
    except NameError:
        "cannot test sending memoryview without memoryview"
    else:
        def test_short_memoryview(self):
            """
            When passed a memoryview onto a small number of bytes,
            :py:obj:`Connection.send` transmits all of them and returns the number of
            bytes sent.
            """
            server, client = self._loopback()
            count = server.send(memoryview(b('xy')))
            self.assertEquals(count, 2)
            self.assertEquals(client.recv(2), b('xy'))


    try:
        buffer
    except NameError:
        "cannot test sending buffer without buffer"
    else:
        def test_short_buffer(self):
            """
            When passed a buffer containing a small number of bytes,
            :py:obj:`Connection.send` transmits all of them and returns the number of
            bytes sent.
            """
            server, client = self._loopback()
            count = server.send(buffer(b('xy')))
            self.assertEquals(count, 2)
            self.assertEquals(client.recv(2), b('xy'))



def _make_memoryview(size):
    """
    Create a new ``memoryview`` wrapped around a ``bytearray`` of the given
    size.
    """
    return memoryview(bytearray(size))



class ConnectionRecvIntoTests(TestCase, _LoopbackMixin):
    """
    Tests for :py:obj:`Connection.recv_into`
    """
    def _no_length_test(self, factory):
        """
        Assert that when the given buffer is passed to
        ``Connection.recv_into``, whatever bytes are available to be received
        that fit into that buffer are written into that buffer.
        """
        output_buffer = factory(5)

        server, client = self._loopback()
        server.send(b('xy'))

        self.assertEqual(client.recv_into(output_buffer), 2)
        self.assertEqual(output_buffer, bytearray(b('xy\x00\x00\x00')))


    def test_bytearray_no_length(self):
        """
        :py:obj:`Connection.recv_into` can be passed a ``bytearray`` instance
        and data in the receive buffer is written to it.
        """
        self._no_length_test(bytearray)


    def _respects_length_test(self, factory):
        """
        Assert that when the given buffer is passed to ``Connection.recv_into``
        along with a value for ``nbytes`` that is less than the size of that
        buffer, only ``nbytes`` bytes are written into the buffer.
        """
        output_buffer = factory(10)

        server, client = self._loopback()
        server.send(b('abcdefghij'))

        self.assertEqual(client.recv_into(output_buffer, 5), 5)
        self.assertEqual(
            output_buffer, bytearray(b('abcde\x00\x00\x00\x00\x00'))
        )


    def test_bytearray_respects_length(self):
        """
        When called with a ``bytearray`` instance,
        :py:obj:`Connection.recv_into` respects the ``nbytes`` parameter and
        doesn't copy in more than that number of bytes.
        """
        self._respects_length_test(bytearray)


    def _doesnt_overfill_test(self, factory):
        """
        Assert that if there are more bytes available to be read from the
        receive buffer than would fit into the buffer passed to
        :py:obj:`Connection.recv_into`, only as many as fit are written into
        it.
        """
        output_buffer = factory(5)

        server, client = self._loopback()
        server.send(b('abcdefghij'))

        self.assertEqual(client.recv_into(output_buffer), 5)
        self.assertEqual(output_buffer, bytearray(b('abcde')))
        rest = client.recv(5)
        self.assertEqual(b('fghij'), rest)


    def test_bytearray_doesnt_overfill(self):
        """
        When called with a ``bytearray`` instance,
        :py:obj:`Connection.recv_into` respects the size of the array and
        doesn't write more bytes into it than will fit.
        """
        self._doesnt_overfill_test(bytearray)


    def _really_doesnt_overfill_test(self, factory):
        """
        Assert that if the value given by ``nbytes`` is greater than the actual
        size of the output buffer passed to :py:obj:`Connection.recv_into`, the
        behavior is as if no value was given for ``nbytes`` at all.
        """
        output_buffer = factory(5)

        server, client = self._loopback()
        server.send(b('abcdefghij'))

        self.assertEqual(client.recv_into(output_buffer, 50), 5)
        self.assertEqual(output_buffer, bytearray(b('abcde')))
        rest = client.recv(5)
        self.assertEqual(b('fghij'), rest)


    def test_bytearray_really_doesnt_overfill(self):
        """
        When called with a ``bytearray`` instance and an ``nbytes`` value that
        is too large, :py:obj:`Connection.recv_into` respects the size of the
        array and not the ``nbytes`` value and doesn't write more bytes into
        the buffer than will fit.
        """
        self._doesnt_overfill_test(bytearray)


    try:
        memoryview
    except NameError:
        "cannot test recv_into memoryview without memoryview"
    else:
        def test_memoryview_no_length(self):
            """
            :py:obj:`Connection.recv_into` can be passed a ``memoryview``
            instance and data in the receive buffer is written to it.
            """
            self._no_length_test(_make_memoryview)


        def test_memoryview_respects_length(self):
            """
            When called with a ``memoryview`` instance,
            :py:obj:`Connection.recv_into` respects the ``nbytes`` parameter
            and doesn't copy more than that number of bytes in.
            """
            self._respects_length_test(_make_memoryview)


        def test_memoryview_doesnt_overfill(self):
            """
            When called with a ``memoryview`` instance,
            :py:obj:`Connection.recv_into` respects the size of the array and
            doesn't write more bytes into it than will fit.
            """
            self._doesnt_overfill_test(_make_memoryview)


        def test_memoryview_really_doesnt_overfill(self):
            """
            When called with a ``memoryview`` instance and an ``nbytes`` value
            that is too large, :py:obj:`Connection.recv_into` respects the size
            of the array and not the ``nbytes`` value and doesn't write more
            bytes into the buffer than will fit.
            """
            self._doesnt_overfill_test(_make_memoryview)



class ConnectionSendallTests(TestCase, _LoopbackMixin):
    """
    Tests for :py:obj:`Connection.sendall`.
    """
    def test_wrong_args(self):
        """
        When called with arguments other than a string argument for its first
        parameter or with more than two arguments, :py:obj:`Connection.sendall`
        raises :py:obj:`TypeError`.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.sendall)
        self.assertRaises(TypeError, connection.sendall, object())
        self.assertRaises(
            TypeError, connection.sendall, "foo", object(), "bar")


    def test_short(self):
        """
        :py:obj:`Connection.sendall` transmits all of the bytes in the string passed to
        it.
        """
        server, client = self._loopback()
        server.sendall(b('x'))
        self.assertEquals(client.recv(1), b('x'))


    def test_text(self):
        """
        :py:obj:`Connection.sendall` transmits all the content in the string
        passed to it raising a DeprecationWarning in case of this being a text.
        """
        server, client = self._loopback()
        with catch_warnings(record=True) as w:
            simplefilter("always")
            server.sendall(b"x".decode("ascii"))
            self.assertEqual(
                "{0} for buf is no longer accepted, use bytes".format(
                    WARNING_TYPE_EXPECTED
                ),
                str(w[-1].message)
            )
            self.assertIs(w[-1].category, DeprecationWarning)
        self.assertEquals(client.recv(1), b"x")


    try:
        memoryview
    except NameError:
        "cannot test sending memoryview without memoryview"
    else:
        def test_short_memoryview(self):
            """
            When passed a memoryview onto a small number of bytes,
            :py:obj:`Connection.sendall` transmits all of them.
            """
            server, client = self._loopback()
            server.sendall(memoryview(b('x')))
            self.assertEquals(client.recv(1), b('x'))


    try:
        buffer
    except NameError:
        "cannot test sending buffers without buffers"
    else:
        def test_short_buffers(self):
            """
            When passed a buffer containing a small number of bytes,
            :py:obj:`Connection.sendall` transmits all of them.
            """
            server, client = self._loopback()
            server.sendall(buffer(b('x')))
            self.assertEquals(client.recv(1), b('x'))


    def test_long(self):
        """
        :py:obj:`Connection.sendall` transmits all of the bytes in the string passed to
        it even if this requires multiple calls of an underlying write function.
        """
        server, client = self._loopback()
        # Should be enough, underlying SSL_write should only do 16k at a time.
        # On Windows, after 32k of bytes the write will block (forever - because
        # no one is yet reading).
        message = b('x') * (1024 * 32 - 1) + b('y')
        server.sendall(message)
        accum = []
        received = 0
        while received < len(message):
            data = client.recv(1024)
            accum.append(data)
            received += len(data)
        self.assertEquals(message, b('').join(accum))


    def test_closed(self):
        """
        If the underlying socket is closed, :py:obj:`Connection.sendall` propagates the
        write error from the low level write call.
        """
        server, client = self._loopback()
        server.sock_shutdown(2)
        exc = self.assertRaises(SysCallError, server.sendall, b"hello, world")
        if platform == "win32":
            self.assertEqual(exc.args[0], ESHUTDOWN)
        else:
            self.assertEqual(exc.args[0], EPIPE)



class ConnectionRenegotiateTests(TestCase, _LoopbackMixin):
    """
    Tests for SSL renegotiation APIs.
    """
    def test_renegotiate_wrong_args(self):
        """
        :py:obj:`Connection.renegotiate` raises :py:obj:`TypeError` if called with any
        arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.renegotiate, None)


    def test_total_renegotiations_wrong_args(self):
        """
        :py:obj:`Connection.total_renegotiations` raises :py:obj:`TypeError` if called with
        any arguments.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertRaises(TypeError, connection.total_renegotiations, None)


    def test_total_renegotiations(self):
        """
        :py:obj:`Connection.total_renegotiations` returns :py:obj:`0` before any
        renegotiations have happened.
        """
        connection = Connection(Context(TLSv1_METHOD), None)
        self.assertEquals(connection.total_renegotiations(), 0)


#     def test_renegotiate(self):
#         """
#         """
#         server, client = self._loopback()

#         server.send("hello world")
#         self.assertEquals(client.recv(len("hello world")), "hello world")

#         self.assertEquals(server.total_renegotiations(), 0)
#         self.assertTrue(server.renegotiate())

#         server.setblocking(False)
#         client.setblocking(False)
#         while server.renegotiate_pending():
#             client.do_handshake()
#             server.do_handshake()

#         self.assertEquals(server.total_renegotiations(), 1)




class ErrorTests(TestCase):
    """
    Unit tests for :py:obj:`OpenSSL.SSL.Error`.
    """
    def test_type(self):
        """
        :py:obj:`Error` is an exception type.
        """
        self.assertTrue(issubclass(Error, Exception))
        self.assertEqual(Error.__name__, 'Error')



class ConstantsTests(TestCase):
    """
    Tests for the values of constants exposed in :py:obj:`OpenSSL.SSL`.

    These are values defined by OpenSSL intended only to be used as flags to
    OpenSSL APIs.  The only assertions it seems can be made about them is
    their values.
    """
    # unittest.TestCase has no skip mechanism
    if OP_NO_QUERY_MTU is not None:
        def test_op_no_query_mtu(self):
            """
            The value of :py:obj:`OpenSSL.SSL.OP_NO_QUERY_MTU` is 0x1000, the value of
            :py:const:`SSL_OP_NO_QUERY_MTU` defined by :file:`openssl/ssl.h`.
            """
            self.assertEqual(OP_NO_QUERY_MTU, 0x1000)
    else:
        "OP_NO_QUERY_MTU unavailable - OpenSSL version may be too old"


    if OP_COOKIE_EXCHANGE is not None:
        def test_op_cookie_exchange(self):
            """
            The value of :py:obj:`OpenSSL.SSL.OP_COOKIE_EXCHANGE` is 0x2000, the value
            of :py:const:`SSL_OP_COOKIE_EXCHANGE` defined by :file:`openssl/ssl.h`.
            """
            self.assertEqual(OP_COOKIE_EXCHANGE, 0x2000)
    else:
        "OP_COOKIE_EXCHANGE unavailable - OpenSSL version may be too old"


    if OP_NO_TICKET is not None:
        def test_op_no_ticket(self):
            """
            The value of :py:obj:`OpenSSL.SSL.OP_NO_TICKET` is 0x4000, the value of
            :py:const:`SSL_OP_NO_TICKET` defined by :file:`openssl/ssl.h`.
            """
            self.assertEqual(OP_NO_TICKET, 0x4000)
    else:
        "OP_NO_TICKET unavailable - OpenSSL version may be too old"


    if OP_NO_COMPRESSION is not None:
        def test_op_no_compression(self):
            """
            The value of :py:obj:`OpenSSL.SSL.OP_NO_COMPRESSION` is 0x20000, the value
            of :py:const:`SSL_OP_NO_COMPRESSION` defined by :file:`openssl/ssl.h`.
            """
            self.assertEqual(OP_NO_COMPRESSION, 0x20000)
    else:
        "OP_NO_COMPRESSION unavailable - OpenSSL version may be too old"


    def test_sess_cache_off(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_OFF` 0x0, the value of
        :py:obj:`SSL_SESS_CACHE_OFF` defined by ``openssl/ssl.h``.
        """
        self.assertEqual(0x0, SESS_CACHE_OFF)


    def test_sess_cache_client(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_CLIENT` 0x1, the value of
        :py:obj:`SSL_SESS_CACHE_CLIENT` defined by ``openssl/ssl.h``.
        """
        self.assertEqual(0x1, SESS_CACHE_CLIENT)


    def test_sess_cache_server(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_SERVER` 0x2, the value of
        :py:obj:`SSL_SESS_CACHE_SERVER` defined by ``openssl/ssl.h``.
        """
        self.assertEqual(0x2, SESS_CACHE_SERVER)


    def test_sess_cache_both(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_BOTH` 0x3, the value of
        :py:obj:`SSL_SESS_CACHE_BOTH` defined by ``openssl/ssl.h``.
        """
        self.assertEqual(0x3, SESS_CACHE_BOTH)


    def test_sess_cache_no_auto_clear(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_NO_AUTO_CLEAR` 0x80, the
        value of :py:obj:`SSL_SESS_CACHE_NO_AUTO_CLEAR` defined by
        ``openssl/ssl.h``.
        """
        self.assertEqual(0x80, SESS_CACHE_NO_AUTO_CLEAR)


    def test_sess_cache_no_internal_lookup(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_NO_INTERNAL_LOOKUP` 0x100,
        the value of :py:obj:`SSL_SESS_CACHE_NO_INTERNAL_LOOKUP` defined by
        ``openssl/ssl.h``.
        """
        self.assertEqual(0x100, SESS_CACHE_NO_INTERNAL_LOOKUP)


    def test_sess_cache_no_internal_store(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_NO_INTERNAL_STORE` 0x200,
        the value of :py:obj:`SSL_SESS_CACHE_NO_INTERNAL_STORE` defined by
        ``openssl/ssl.h``.
        """
        self.assertEqual(0x200, SESS_CACHE_NO_INTERNAL_STORE)


    def test_sess_cache_no_internal(self):
        """
        The value of :py:obj:`OpenSSL.SSL.SESS_CACHE_NO_INTERNAL` 0x300, the
        value of :py:obj:`SSL_SESS_CACHE_NO_INTERNAL` defined by
        ``openssl/ssl.h``.
        """
        self.assertEqual(0x300, SESS_CACHE_NO_INTERNAL)



class MemoryBIOTests(TestCase, _LoopbackMixin):
    """
    Tests for :py:obj:`OpenSSL.SSL.Connection` using a memory BIO.
    """
    def _server(self, sock):
        """
        Create a new server-side SSL :py:obj:`Connection` object wrapped around
        :py:obj:`sock`.
        """
        # Create the server side Connection.  This is mostly setup boilerplate
        # - use TLSv1, use a particular certificate, etc.
        server_ctx = Context(TLSv1_METHOD)
        server_ctx.set_options(OP_NO_SSLv2 | OP_NO_SSLv3 | OP_SINGLE_DH_USE )
        server_ctx.set_verify(VERIFY_PEER|VERIFY_FAIL_IF_NO_PEER_CERT|VERIFY_CLIENT_ONCE, verify_cb)
        server_store = server_ctx.get_cert_store()
        server_ctx.use_privatekey(load_privatekey(FILETYPE_PEM, server_key_pem))
        server_ctx.use_certificate(load_certificate(FILETYPE_PEM, server_cert_pem))
        server_ctx.check_privatekey()
        server_store.add_cert(load_certificate(FILETYPE_PEM, root_cert_pem))
        # Here the Connection is actually created.  If None is passed as the 2nd
        # parameter, it indicates a memory BIO should be created.
        server_conn = Connection(server_ctx, sock)
        server_conn.set_accept_state()
        return server_conn


    def _client(self, sock):
        """
        Create a new client-side SSL :py:obj:`Connection` object wrapped around
        :py:obj:`sock`.
        """
        # Now create the client side Connection.  Similar boilerplate to the
        # above.
        client_ctx = Context(TLSv1_METHOD)
        client_ctx.set_options(OP_NO_SSLv2 | OP_NO_SSLv3 | OP_SINGLE_DH_USE )
        client_ctx.set_verify(VERIFY_PEER|VERIFY_FAIL_IF_NO_PEER_CERT|VERIFY_CLIENT_ONCE, verify_cb)
        client_store = client_ctx.get_cert_store()
        client_ctx.use_privatekey(load_privatekey(FILETYPE_PEM, client_key_pem))
        client_ctx.use_certificate(load_certificate(FILETYPE_PEM, client_cert_pem))
        client_ctx.check_privatekey()
        client_store.add_cert(load_certificate(FILETYPE_PEM, root_cert_pem))
        client_conn = Connection(client_ctx, sock)
        client_conn.set_connect_state()
        return client_conn


    def test_memoryConnect(self):
        """
        Two :py:obj:`Connection`s which use memory BIOs can be manually connected by
        reading from the output of each and writing those bytes to the input of
        the other and in this way establish a connection and exchange
        application-level bytes with each other.
        """
        server_conn = self._server(None)
        client_conn = self._client(None)

        # There should be no key or nonces yet.
        self.assertIdentical(server_conn.master_key(), None)
        self.assertIdentical(server_conn.client_random(), None)
        self.assertIdentical(server_conn.server_random(), None)

        # First, the handshake needs to happen.  We'll deliver bytes back and
        # forth between the client and server until neither of them feels like
        # speaking any more.
        self.assertIdentical(
            self._interactInMemory(client_conn, server_conn), None)

        # Now that the handshake is done, there should be a key and nonces.
        self.assertNotIdentical(server_conn.master_key(), None)
        self.assertNotIdentical(server_conn.client_random(), None)
        self.assertNotIdentical(server_conn.server_random(), None)
        self.assertEquals(server_conn.client_random(), client_conn.client_random())
        self.assertEquals(server_conn.server_random(), client_conn.server_random())
        self.assertNotEquals(server_conn.client_random(), server_conn.server_random())
        self.assertNotEquals(client_conn.client_random(), client_conn.server_random())

        # Here are the bytes we'll try to send.
        important_message = b('One if by land, two if by sea.')

        server_conn.write(important_message)
        self.assertEquals(
            self._interactInMemory(client_conn, server_conn),
            (client_conn, important_message))

        client_conn.write(important_message[::-1])
        self.assertEquals(
            self._interactInMemory(client_conn, server_conn),
            (server_conn, important_message[::-1]))


    def test_socketConnect(self):
        """
        Just like :py:obj:`test_memoryConnect` but with an actual socket.

        This is primarily to rule out the memory BIO code as the source of
        any problems encountered while passing data over a :py:obj:`Connection` (if
        this test fails, there must be a problem outside the memory BIO
        code, as no memory BIO is involved here).  Even though this isn't a
        memory BIO test, it's convenient to have it here.
        """
        server_conn, client_conn = self._loopback()

        important_message = b("Help me Obi Wan Kenobi, you're my only hope.")
        client_conn.send(important_message)
        msg = server_conn.recv(1024)
        self.assertEqual(msg, important_message)

        # Again in the other direction, just for fun.
        important_message = important_message[::-1]
        server_conn.send(important_message)
        msg = client_conn.recv(1024)
        self.assertEqual(msg, important_message)


    def test_socketOverridesMemory(self):
        """
        Test that :py:obj:`OpenSSL.SSL.bio_read` and :py:obj:`OpenSSL.SSL.bio_write` don't
        work on :py:obj:`OpenSSL.SSL.Connection`() that use sockets.
        """
        context = Context(SSLv3_METHOD)
        client = socket()
        clientSSL = Connection(context, client)
        self.assertRaises( TypeError, clientSSL.bio_read, 100)
        self.assertRaises( TypeError, clientSSL.bio_write, "foo")
        self.assertRaises( TypeError, clientSSL.bio_shutdown )


    def test_outgoingOverflow(self):
        """
        If more bytes than can be written to the memory BIO are passed to
        :py:obj:`Connection.send` at once, the number of bytes which were written is
        returned and that many bytes from the beginning of the input can be
        read from the other end of the connection.
        """
        server = self._server(None)
        client = self._client(None)

        self._interactInMemory(client, server)

        size = 2 ** 15
        sent = client.send(b"x" * size)
        # Sanity check.  We're trying to test what happens when the entire
        # input can't be sent.  If the entire input was sent, this test is
        # meaningless.
        self.assertTrue(sent < size)

        receiver, received = self._interactInMemory(client, server)
        self.assertIdentical(receiver, server)

        # We can rely on all of these bytes being received at once because
        # _loopback passes 2 ** 16 to recv - more than 2 ** 15.
        self.assertEquals(len(received), sent)


    def test_shutdown(self):
        """
        :py:obj:`Connection.bio_shutdown` signals the end of the data stream from
        which the :py:obj:`Connection` reads.
        """
        server = self._server(None)
        server.bio_shutdown()
        e = self.assertRaises(Error, server.recv, 1024)
        # We don't want WantReadError or ZeroReturnError or anything - it's a
        # handshake failure.
        self.assertEquals(e.__class__, Error)


    def test_unexpectedEndOfFile(self):
        """
        If the connection is lost before an orderly SSL shutdown occurs,
        :py:obj:`OpenSSL.SSL.SysCallError` is raised with a message of
        "Unexpected EOF".
        """
        server_conn, client_conn = self._loopback()
        client_conn.sock_shutdown(SHUT_RDWR)
        exc = self.assertRaises(SysCallError, server_conn.recv, 1024)
        self.assertEqual(exc.args, (-1, "Unexpected EOF"))


    def _check_client_ca_list(self, func):
        """
        Verify the return value of the :py:obj:`get_client_ca_list` method for server and client connections.

        :param func: A function which will be called with the server context
            before the client and server are connected to each other.  This
            function should specify a list of CAs for the server to send to the
            client and return that same list.  The list will be used to verify
            that :py:obj:`get_client_ca_list` returns the proper value at various
            times.
        """
        server = self._server(None)
        client = self._client(None)
        self.assertEqual(client.get_client_ca_list(), [])
        self.assertEqual(server.get_client_ca_list(), [])
        ctx = server.get_context()
        expected = func(ctx)
        self.assertEqual(client.get_client_ca_list(), [])
        self.assertEqual(server.get_client_ca_list(), expected)
        self._interactInMemory(client, server)
        self.assertEqual(client.get_client_ca_list(), expected)
        self.assertEqual(server.get_client_ca_list(), expected)


    def test_set_client_ca_list_errors(self):
        """
        :py:obj:`Context.set_client_ca_list` raises a :py:obj:`TypeError` if called with a
        non-list or a list that contains objects other than X509Names.
        """
        ctx = Context(TLSv1_METHOD)
        self.assertRaises(TypeError, ctx.set_client_ca_list, "spam")
        self.assertRaises(TypeError, ctx.set_client_ca_list, ["spam"])
        self.assertIdentical(ctx.set_client_ca_list([]), None)


    def test_set_empty_ca_list(self):
        """
        If passed an empty list, :py:obj:`Context.set_client_ca_list` configures the
        context to send no CA names to the client and, on both the server and
        client sides, :py:obj:`Connection.get_client_ca_list` returns an empty list
        after the connection is set up.
        """
        def no_ca(ctx):
            ctx.set_client_ca_list([])
            return []
        self._check_client_ca_list(no_ca)


    def test_set_one_ca_list(self):
        """
        If passed a list containing a single X509Name,
        :py:obj:`Context.set_client_ca_list` configures the context to send that CA
        name to the client and, on both the server and client sides,
        :py:obj:`Connection.get_client_ca_list` returns a list containing that
        X509Name after the connection is set up.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        cadesc = cacert.get_subject()
        def single_ca(ctx):
            ctx.set_client_ca_list([cadesc])
            return [cadesc]
        self._check_client_ca_list(single_ca)


    def test_set_multiple_ca_list(self):
        """
        If passed a list containing multiple X509Name objects,
        :py:obj:`Context.set_client_ca_list` configures the context to send those CA
        names to the client and, on both the server and client sides,
        :py:obj:`Connection.get_client_ca_list` returns a list containing those
        X509Names after the connection is set up.
        """
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)
        clcert = load_certificate(FILETYPE_PEM, server_cert_pem)

        sedesc = secert.get_subject()
        cldesc = clcert.get_subject()

        def multiple_ca(ctx):
            L = [sedesc, cldesc]
            ctx.set_client_ca_list(L)
            return L
        self._check_client_ca_list(multiple_ca)


    def test_reset_ca_list(self):
        """
        If called multiple times, only the X509Names passed to the final call
        of :py:obj:`Context.set_client_ca_list` are used to configure the CA names
        sent to the client.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)
        clcert = load_certificate(FILETYPE_PEM, server_cert_pem)

        cadesc = cacert.get_subject()
        sedesc = secert.get_subject()
        cldesc = clcert.get_subject()

        def changed_ca(ctx):
            ctx.set_client_ca_list([sedesc, cldesc])
            ctx.set_client_ca_list([cadesc])
            return [cadesc]
        self._check_client_ca_list(changed_ca)


    def test_mutated_ca_list(self):
        """
        If the list passed to :py:obj:`Context.set_client_ca_list` is mutated
        afterwards, this does not affect the list of CA names sent to the
        client.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)

        cadesc = cacert.get_subject()
        sedesc = secert.get_subject()

        def mutated_ca(ctx):
            L = [cadesc]
            ctx.set_client_ca_list([cadesc])
            L.append(sedesc)
            return [cadesc]
        self._check_client_ca_list(mutated_ca)


    def test_add_client_ca_errors(self):
        """
        :py:obj:`Context.add_client_ca` raises :py:obj:`TypeError` if called with a non-X509
        object or with a number of arguments other than one.
        """
        ctx = Context(TLSv1_METHOD)
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        self.assertRaises(TypeError, ctx.add_client_ca)
        self.assertRaises(TypeError, ctx.add_client_ca, "spam")
        self.assertRaises(TypeError, ctx.add_client_ca, cacert, cacert)


    def test_one_add_client_ca(self):
        """
        A certificate's subject can be added as a CA to be sent to the client
        with :py:obj:`Context.add_client_ca`.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        cadesc = cacert.get_subject()
        def single_ca(ctx):
            ctx.add_client_ca(cacert)
            return [cadesc]
        self._check_client_ca_list(single_ca)


    def test_multiple_add_client_ca(self):
        """
        Multiple CA names can be sent to the client by calling
        :py:obj:`Context.add_client_ca` with multiple X509 objects.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)

        cadesc = cacert.get_subject()
        sedesc = secert.get_subject()

        def multiple_ca(ctx):
            ctx.add_client_ca(cacert)
            ctx.add_client_ca(secert)
            return [cadesc, sedesc]
        self._check_client_ca_list(multiple_ca)


    def test_set_and_add_client_ca(self):
        """
        A call to :py:obj:`Context.set_client_ca_list` followed by a call to
        :py:obj:`Context.add_client_ca` results in using the CA names from the first
        call and the CA name from the second call.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)
        clcert = load_certificate(FILETYPE_PEM, server_cert_pem)

        cadesc = cacert.get_subject()
        sedesc = secert.get_subject()
        cldesc = clcert.get_subject()

        def mixed_set_add_ca(ctx):
            ctx.set_client_ca_list([cadesc, sedesc])
            ctx.add_client_ca(clcert)
            return [cadesc, sedesc, cldesc]
        self._check_client_ca_list(mixed_set_add_ca)


    def test_set_after_add_client_ca(self):
        """
        A call to :py:obj:`Context.set_client_ca_list` after a call to
        :py:obj:`Context.add_client_ca` replaces the CA name specified by the former
        call with the names specified by the latter cal.
        """
        cacert = load_certificate(FILETYPE_PEM, root_cert_pem)
        secert = load_certificate(FILETYPE_PEM, server_cert_pem)
        clcert = load_certificate(FILETYPE_PEM, server_cert_pem)

        cadesc = cacert.get_subject()
        sedesc = secert.get_subject()

        def set_replaces_add_ca(ctx):
            ctx.add_client_ca(clcert)
            ctx.set_client_ca_list([cadesc])
            ctx.add_client_ca(secert)
            return [cadesc, sedesc]
        self._check_client_ca_list(set_replaces_add_ca)



class ConnectionBIOTests(TestCase):
    """
    Tests for :py:obj:`Connection.bio_read` and :py:obj:`Connection.bio_write`.
    """
    def test_wantReadError(self):
        """
        :py:obj:`Connection.bio_read` raises :py:obj:`OpenSSL.SSL.WantReadError`
        if there are no bytes available to be read from the BIO.
        """
        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, None)
        self.assertRaises(WantReadError, conn.bio_read, 1024)


    def test_buffer_size(self):
        """
        :py:obj:`Connection.bio_read` accepts an integer giving the maximum
        number of bytes to read and return.
        """
        ctx = Context(TLSv1_METHOD)
        conn = Connection(ctx, None)
        conn.set_connect_state()
        try:
            conn.do_handshake()
        except WantReadError:
            pass
        data = conn.bio_read(2)
        self.assertEqual(2, len(data))


    if not PY3:
        def test_buffer_size_long(self):
            """
            On Python 2 :py:obj:`Connection.bio_read` accepts values of type
            :py:obj:`long` as well as :py:obj:`int`.
            """
            ctx = Context(TLSv1_METHOD)
            conn = Connection(ctx, None)
            conn.set_connect_state()
            try:
                conn.do_handshake()
            except WantReadError:
                pass
            data = conn.bio_read(long(2))
            self.assertEqual(2, len(data))




class InfoConstantTests(TestCase):
    """
    Tests for assorted constants exposed for use in info callbacks.
    """
    def test_integers(self):
        """
        All of the info constants are integers.

        This is a very weak test.  It would be nice to have one that actually
        verifies that as certain info events happen, the value passed to the
        info callback matches up with the constant exposed by OpenSSL.SSL.
        """
        for const in [
            SSL_ST_CONNECT, SSL_ST_ACCEPT, SSL_ST_MASK, SSL_ST_INIT,
            SSL_ST_BEFORE, SSL_ST_OK, SSL_ST_RENEGOTIATE,
            SSL_CB_LOOP, SSL_CB_EXIT, SSL_CB_READ, SSL_CB_WRITE, SSL_CB_ALERT,
            SSL_CB_READ_ALERT, SSL_CB_WRITE_ALERT, SSL_CB_ACCEPT_LOOP,
            SSL_CB_ACCEPT_EXIT, SSL_CB_CONNECT_LOOP, SSL_CB_CONNECT_EXIT,
            SSL_CB_HANDSHAKE_START, SSL_CB_HANDSHAKE_DONE]:

            self.assertTrue(isinstance(const, int))


if __name__ == '__main__':
    main()
