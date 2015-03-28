# Copyright (C) Jean-Paul Calderone
# Copyright (C) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Helpers for the OpenSSL test suite, largely copied from
U{Twisted<http://twistedmatrix.com/>}.
"""

import shutil
import os, os.path
from tempfile import mktemp
from unittest import TestCase
import sys

from OpenSSL.crypto import Error, _exception_from_error_queue

if sys.version_info < (3, 0):
    def b(s):
        return s
    bytes = str
else:
    def b(s):
        return s.encode("charmap")
    bytes = bytes


class TestCase(TestCase):
    """
    L{TestCase} adds useful testing functionality beyond what is available
    from the standard library L{unittest.TestCase}.
    """
    def tearDown(self):
        """
        Clean up any files or directories created using L{TestCase.mktemp}.
        Subclasses must invoke this method if they override it or the
        cleanup will not occur.
        """
        if False and self._temporaryFiles is not None:
            for temp in self._temporaryFiles:
                if os.path.isdir(temp):
                    shutil.rmtree(temp)
                elif os.path.exists(temp):
                    os.unlink(temp)
        try:
            _exception_from_error_queue()
        except Error:
            e = sys.exc_info()[1]
            if e.args != ([],):
                self.fail("Left over errors in OpenSSL error queue: " + repr(e))


    def failUnlessIn(self, containee, container, msg=None):
        """
        Fail the test if C{containee} is not found in C{container}.

        @param containee: the value that should be in C{container}
        @param container: a sequence type, or in the case of a mapping type,
                          will follow semantics of 'if key in dict.keys()'
        @param msg: if msg is None, then the failure message will be
                    '%r not in %r' % (first, second)
        """
        if containee not in container:
            raise self.failureException(msg or "%r not in %r"
                                        % (containee, container))
        return containee
    assertIn = failUnlessIn

    def failUnlessIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is not C{second}.  This is an
        obect-identity-equality test, not an object equality
        (i.e. C{__eq__}) test.

        @param msg: if msg is None, then the failure message will be
        '%r is not %r' % (first, second)
        """
        if first is not second:
            raise self.failureException(msg or '%r is not %r' % (first, second))
        return first
    assertIdentical = failUnlessIdentical


    def failIfIdentical(self, first, second, msg=None):
        """
        Fail the test if C{first} is C{second}.  This is an
        obect-identity-equality test, not an object equality
        (i.e. C{__eq__}) test.

        @param msg: if msg is None, then the failure message will be
        '%r is %r' % (first, second)
        """
        if first is second:
            raise self.failureException(msg or '%r is %r' % (first, second))
        return first
    assertNotIdentical = failIfIdentical


    def failUnlessRaises(self, exception, f, *args, **kwargs):
        """
        Fail the test unless calling the function C{f} with the given
        C{args} and C{kwargs} raises C{exception}. The failure will report
        the traceback and call stack of the unexpected exception.

        @param exception: exception type that is to be expected
        @param f: the function to call

        @return: The raised exception instance, if it is of the given type.
        @raise self.failureException: Raised if the function call does
            not raise an exception or if it raises an exception of a
            different type.
        """
        try:
            result = f(*args, **kwargs)
        except exception:
            inst = sys.exc_info()[1]
            return inst
        except:
            raise self.failureException('%s raised instead of %s'
                                        % (sys.exc_info()[0],
                                           exception.__name__,
                                          ))
        else:
            raise self.failureException('%s not raised (%r returned)'
                                        % (exception.__name__, result))
    assertRaises = failUnlessRaises


    _temporaryFiles = None
    def mktemp(self):
        """
        Pathetic substitute for twisted.trial.unittest.TestCase.mktemp.
        """
        if self._temporaryFiles is None:
            self._temporaryFiles = []
        temp = mktemp(dir=".")
        self._temporaryFiles.append(temp)
        return temp


    # Python 2.3 compatibility.
    def assertTrue(self, *a, **kw):
        return self.failUnless(*a, **kw)


    def assertFalse(self, *a, **kw):
        return self.failIf(*a, **kw)


    # Other stuff
    def assertConsistentType(self, theType, name, *constructionArgs):
        """
        Perform various assertions about C{theType} to ensure that it is a
        well-defined type.  This is useful for extension types, where it's
        pretty easy to do something wacky.  If something about the type is
        unusual, an exception will be raised.

        @param theType: The type object about which to make assertions.
        @param name: A string giving the name of the type.
        @param constructionArgs: Positional arguments to use with C{theType} to
            create an instance of it.
        """
        self.assertEqual(theType.__name__, name)
        self.assertTrue(isinstance(theType, type))
        instance = theType(*constructionArgs)
        self.assertIdentical(type(instance), theType)
