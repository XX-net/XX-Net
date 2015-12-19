"""
PRNG management routines, thin wrappers.

See the file RATIONALE for a short explanation of why this module was written.
"""

from functools import partial

from six import integer_types as _integer_types

from OpenSSL._util import (
    ffi as _ffi,
    lib as _lib,
    exception_from_error_queue as _exception_from_error_queue,
    path_string as _path_string)


class Error(Exception):
    """
    An error occurred in an `OpenSSL.rand` API.
    """

_raise_current_error = partial(_exception_from_error_queue, Error)

_unspecified = object()

_builtin_bytes = bytes

def bytes(num_bytes):
    """
    Get some random bytes as a string.

    :param num_bytes: The number of bytes to fetch
    :return: A string of random bytes
    """
    if not isinstance(num_bytes, _integer_types):
        raise TypeError("num_bytes must be an integer")

    if num_bytes < 0:
        raise ValueError("num_bytes must not be negative")

    result_buffer = _ffi.new("char[]", num_bytes)
    result_code = _lib.RAND_bytes(result_buffer, num_bytes)
    if result_code == -1:
        # TODO: No tests for this code path.  Triggering a RAND_bytes failure
        # might involve supplying a custom ENGINE?  That's hard.
        _raise_current_error()

    return _ffi.buffer(result_buffer)[:]



def add(buffer, entropy):
    """
    Add data with a given entropy to the PRNG

    :param buffer: Buffer with random data
    :param entropy: The entropy (in bytes) measurement of the buffer
    :return: None
    """
    if not isinstance(buffer, _builtin_bytes):
        raise TypeError("buffer must be a byte string")

    if not isinstance(entropy, int):
        raise TypeError("entropy must be an integer")

    # TODO Nothing tests this call actually being made, or made properly.
    _lib.RAND_add(buffer, len(buffer), entropy)



def seed(buffer):
    """
    Alias for rand_add, with entropy equal to length

    :param buffer: Buffer with random data
    :return: None
    """
    if not isinstance(buffer, _builtin_bytes):
        raise TypeError("buffer must be a byte string")

    # TODO Nothing tests this call actually being made, or made properly.
    _lib.RAND_seed(buffer, len(buffer))



def status():
    """
    Retrieve the status of the PRNG

    :return: True if the PRNG is seeded enough, false otherwise
    """
    return _lib.RAND_status()



def egd(path, bytes=_unspecified):
    """
    Query an entropy gathering daemon (EGD) for random data and add it to the
    PRNG. I haven't found any problems when the socket is missing, the function
    just returns 0.

    :param path: The path to the EGD socket
    :param bytes: (optional) The number of bytes to read, default is 255
    :returns: The number of bytes read (NB: a value of 0 isn't necessarily an
              error, check rand.status())
    """
    if not isinstance(path, _builtin_bytes):
        raise TypeError("path must be a byte string")

    if bytes is _unspecified:
        bytes = 255
    elif not isinstance(bytes, int):
        raise TypeError("bytes must be an integer")

    return _lib.RAND_egd_bytes(path, bytes)



def cleanup():
    """
    Erase the memory used by the PRNG.

    :return: None
    """
    # TODO Nothing tests this call actually being made, or made properly.
    _lib.RAND_cleanup()



def load_file(filename, maxbytes=_unspecified):
    """
    Seed the PRNG with data from a file

    :param filename: The file to read data from (``bytes`` or ``unicode``).
    :param maxbytes: (optional) The number of bytes to read, default is to read
        the entire file

    :return: The number of bytes read
    """
    filename = _path_string(filename)

    if maxbytes is _unspecified:
        maxbytes = -1
    elif not isinstance(maxbytes, int):
        raise TypeError("maxbytes must be an integer")

    return _lib.RAND_load_file(filename, maxbytes)



def write_file(filename):
    """
    Save PRNG state to a file

    :param filename: The file to write data to (``bytes`` or ``unicode``).

    :return: The number of bytes written
    """
    filename = _path_string(filename)
    return _lib.RAND_write_file(filename)


# TODO There are no tests for screen at all
def screen():
    """
    Add the current contents of the screen to the PRNG state. Availability:
    Windows.

    :return: None
    """
    _lib.RAND_screen()

if getattr(_lib, 'RAND_screen', None) is None:
    del screen


# TODO There are no tests for the RAND strings being loaded, whatever that
# means.
_lib.ERR_load_RAND_strings()
