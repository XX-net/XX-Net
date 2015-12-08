# -*- coding: ascii -*-

from doctest import DocFileSuite
import unittest, os.path, sys

THIS_DIR = os.path.dirname(__file__)

README = os.path.join(THIS_DIR, os.pardir, os.pardir, 'README.txt')


class DocumentationTestCase(unittest.TestCase):
    def test_readme_encoding(self):
        '''Confirm the README.txt is pure ASCII.'''
        f = open(README, 'rb')
        try:
            f.read().decode('US-ASCII')
        finally:
            f.close()


def test_suite():
    "For the Z3 test runner"
    return unittest.TestSuite((
        DocumentationTestCase('test_readme_encoding'),
        DocFileSuite(os.path.join(os.pardir, os.pardir, 'README.txt'))))


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join(
        THIS_DIR, os.pardir, os.pardir
        )))
    unittest.main(defaultTest='test_suite')


