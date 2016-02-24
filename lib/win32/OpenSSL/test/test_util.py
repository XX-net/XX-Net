from OpenSSL._util import exception_from_error_queue, lib
from OpenSSL.test.util import TestCase



class ErrorTests(TestCase):
    """
    Tests for handling of certain OpenSSL error cases.
    """
    def test_exception_from_error_queue_nonexistent_reason(self):
        """
        :py:func:`exception_from_error_queue` raises ``ValueError`` when it
        encounters an OpenSSL error code which does not have a reason string.
        """
        lib.ERR_put_error(lib.ERR_LIB_EVP, 0, 1112, b"", 10)
        exc = self.assertRaises(ValueError, exception_from_error_queue, ValueError)
        self.assertEqual(exc.args[0][0][2], "")
