# Copyright (c) Frederick Dean
# See LICENSE for details.

"""
Unit tests for :py:obj:`OpenSSL.rand`.
"""

from unittest import main
import os
import stat
import sys

from OpenSSL.test.util import NON_ASCII, TestCase, b
from OpenSSL import rand


class RandTests(TestCase):
    def test_bytes_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.bytes` raises :py:obj:`TypeError` if called with the wrong
        number of arguments or with a non-:py:obj:`int` argument.
        """
        self.assertRaises(TypeError, rand.bytes)
        self.assertRaises(TypeError, rand.bytes, None)
        self.assertRaises(TypeError, rand.bytes, 3, None)


    def test_insufficientMemory(self):
        """
        :py:obj:`OpenSSL.rand.bytes` raises :py:obj:`MemoryError` if more bytes
        are requested than will fit in memory.
        """
        self.assertRaises(MemoryError, rand.bytes, sys.maxsize)


    def test_bytes(self):
        """
        Verify that we can obtain bytes from rand_bytes() and
        that they are different each time.  Test the parameter
        of rand_bytes() for bad values.
        """
        b1 = rand.bytes(50)
        self.assertEqual(len(b1), 50)
        b2 = rand.bytes(num_bytes=50)  # parameter by name
        self.assertNotEqual(b1, b2)  #  Hip, Hip, Horay! FIPS complaince
        b3 = rand.bytes(num_bytes=0)
        self.assertEqual(len(b3), 0)
        exc = self.assertRaises(ValueError, rand.bytes, -1)
        self.assertEqual(str(exc), "num_bytes must not be negative")


    def test_add_wrong_args(self):
        """
        When called with the wrong number of arguments, or with arguments not of
        type :py:obj:`str` and :py:obj:`int`, :py:obj:`OpenSSL.rand.add` raises :py:obj:`TypeError`.
        """
        self.assertRaises(TypeError, rand.add)
        self.assertRaises(TypeError, rand.add, b("foo"), None)
        self.assertRaises(TypeError, rand.add, None, 3)
        self.assertRaises(TypeError, rand.add, b("foo"), 3, None)


    def test_add(self):
        """
        :py:obj:`OpenSSL.rand.add` adds entropy to the PRNG.
        """
        rand.add(b('hamburger'), 3)


    def test_seed_wrong_args(self):
        """
        When called with the wrong number of arguments, or with a non-:py:obj:`str`
        argument, :py:obj:`OpenSSL.rand.seed` raises :py:obj:`TypeError`.
        """
        self.assertRaises(TypeError, rand.seed)
        self.assertRaises(TypeError, rand.seed, None)
        self.assertRaises(TypeError, rand.seed, b("foo"), None)


    def test_seed(self):
        """
        :py:obj:`OpenSSL.rand.seed` adds entropy to the PRNG.
        """
        rand.seed(b('milk shake'))


    def test_status_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.status` raises :py:obj:`TypeError` when called with any
        arguments.
        """
        self.assertRaises(TypeError, rand.status, None)


    def test_status(self):
        """
        :py:obj:`OpenSSL.rand.status` returns :py:obj:`True` if the PRNG has sufficient
        entropy, :py:obj:`False` otherwise.
        """
        # It's hard to know what it is actually going to return.  Different
        # OpenSSL random engines decide differently whether they have enough
        # entropy or not.
        self.assertTrue(rand.status() in (1, 2))


    def test_egd_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.egd` raises :py:obj:`TypeError` when called with the wrong
        number of arguments or with arguments not of type :py:obj:`str` and :py:obj:`int`.
        """
        self.assertRaises(TypeError, rand.egd)
        self.assertRaises(TypeError, rand.egd, None)
        self.assertRaises(TypeError, rand.egd, "foo", None)
        self.assertRaises(TypeError, rand.egd, None, 3)
        self.assertRaises(TypeError, rand.egd, "foo", 3, None)


    def test_egd_missing(self):
        """
        :py:obj:`OpenSSL.rand.egd` returns :py:obj:`0` or :py:obj:`-1` if the
        EGD socket passed to it does not exist.
        """
        result = rand.egd(self.mktemp())
        expected = (-1, 0)
        self.assertTrue(
            result in expected,
            "%r not in %r" % (result, expected))


    def test_egd_missing_and_bytes(self):
        """
        :py:obj:`OpenSSL.rand.egd` returns :py:obj:`0` or :py:obj:`-1` if the
        EGD socket passed to it does not exist even if a size argument is
        explicitly passed.
        """
        result = rand.egd(self.mktemp(), 1024)
        expected = (-1, 0)
        self.assertTrue(
            result in expected,
            "%r not in %r" % (result, expected))


    def test_cleanup_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.cleanup` raises :py:obj:`TypeError` when called with any
        arguments.
        """
        self.assertRaises(TypeError, rand.cleanup, None)


    def test_cleanup(self):
        """
        :py:obj:`OpenSSL.rand.cleanup` releases the memory used by the PRNG and returns
        :py:obj:`None`.
        """
        self.assertIdentical(rand.cleanup(), None)


    def test_load_file_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.load_file` raises :py:obj:`TypeError` when called the wrong
        number of arguments or arguments not of type :py:obj:`str` and :py:obj:`int`.
        """
        self.assertRaises(TypeError, rand.load_file)
        self.assertRaises(TypeError, rand.load_file, "foo", None)
        self.assertRaises(TypeError, rand.load_file, None, 1)
        self.assertRaises(TypeError, rand.load_file, "foo", 1, None)


    def test_write_file_wrong_args(self):
        """
        :py:obj:`OpenSSL.rand.write_file` raises :py:obj:`TypeError` when called with the
        wrong number of arguments or a non-:py:obj:`str` argument.
        """
        self.assertRaises(TypeError, rand.write_file)
        self.assertRaises(TypeError, rand.write_file, None)
        self.assertRaises(TypeError, rand.write_file, "foo", None)

    def _read_write_test(self, path):
        """
        Verify that ``rand.write_file`` and ``rand.load_file`` can be used.
        """
        # Create the file so cleanup is more straightforward
        with open(path, "w"):
            pass

        try:
            # Write random bytes to a file
            rand.write_file(path)

            # Verify length of written file
            size = os.stat(path)[stat.ST_SIZE]
            self.assertEqual(1024, size)

            # Read random bytes from file
            rand.load_file(path)
            rand.load_file(path, 4)  # specify a length
        finally:
            # Cleanup
            os.unlink(path)


    def test_bytes_paths(self):
        """
        Random data can be saved and loaded to files with paths specified as
        bytes.
        """
        path = self.mktemp()
        path += NON_ASCII.encode(sys.getfilesystemencoding())
        self._read_write_test(path)


    def test_unicode_paths(self):
        """
        Random data can be saved and loaded to files with paths specified as
        unicode.
        """
        path = self.mktemp().decode('utf-8') + NON_ASCII
        self._read_write_test(path)


if __name__ == '__main__':
    main()
