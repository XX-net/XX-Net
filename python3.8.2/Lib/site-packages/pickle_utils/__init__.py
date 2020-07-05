import os.path
import pickle
import functools
import logging
import gzip

__all__ = ['load', 'dump', 'memoize']
log = logging.getLogger(__name__)

def _smart_open(filename, *args, **kwargs):
    if filename[-7:] == '.pkl.gz':
        return gzip.open(filename, *args, **kwargs)
    elif filename[-4:] == '.pkl':
        return open(filename, *args, **kwargs)
    else:
        raise ValueError("Unknown extension in: `{:s}`. Valid extensions are \".pkl\" and \".pkl.gz\"".format(filename))

def load(filename_or_object):
    """Like `pickle.load`, but takes as argument a file name or a
    file-like object. If the argument is a file name, it must end in ".pkl" or
    ".pkl.gz". In the second case the file will be compressed."""
    if isinstance(filename_or_object, str):
        with _smart_open(filename_or_object, 'rb') as f:
            return pickle.load(f)
    return pickle.load(filename_or_object)

def dump(data, filename_or_object):
    """Like `pickle.dump`, but takes as second argument a file name or a
    file-like object. If the argument is a file name, it must end in ".pkl" or
    ".pkl.gz". In the second case the file will be compressed."""
    if isinstance(filename_or_object, str):
        with _smart_open(filename_or_object, 'wb') as f:
            return pickle.dump(data, f)
    return pickle.dump(data, filename_or_object)

def memoize(filename, log_level='info'):
    """Decorator to memoize the output of a function to `filename` with pickle.
    The function will be executed only if `filename` does not exist.

    To accommodate saving different files for different arguments, you can use
    a formatted string in `filename`. The string will be formatted using the
    `args` and `kwargs` passed to the wrapped function before checking for file
    existence.

    `verbose` controls the level at which to log whether the function is loaded
    from disk or computed. It may be `None`, to indicate no logging should be
    performed.
    """

    def pk_decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            f_fname = filename.format(*args, **kwargs)
            if os.path.exists(f_fname):
                if log_level:
                    getattr(log, log_level)(
                        "File `{:s}` exists! Reading data...".format(f_fname))
                data = load(f_fname)
            else:
                if log_level:
                    getattr(log, log_level)(
                        "Generating data for file `{:s}`, for function `{:s}`..."
                            .format(f_fname, function.__name__))
                data = function(*args, **kwargs)
                dump(data, f_fname)
            return data
        return wrapper
    return pk_decorator

### Testing

import unittest
import tempfile
import os

class Test(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
    def tearDown(self):
        for f in os.listdir(self.tmp_dir):
            os.unlink(os.path.join(self.tmp_dir, f))
        os.rmdir(self.tmp_dir)

    def test_filename(self):
        a = [1,2,3,4,5]
        fname = os.path.join(self.tmp_dir, 'a.pkl')
        dump(a, fname)
        b = load(fname)
        self.assertEqual(a, b)

    def test_filename_compressed(self):
        a = [1,2,3,4,5]
        fname = os.path.join(self.tmp_dir, 'a.pkl.gz')
        dump(a, fname)
        b = load(fname)
        self.assertEqual(a, b)

    def test_object(self):
        a = [1,2,3,4,5]
        fname = os.path.join(self.tmp_dir, 'a.pkl')
        with open(fname, 'wb') as f:
            dump(a, f)
        with open(fname, 'rb') as f:
            b = load(f)
        self.assertEqual(a, b)

    def test_memoize(self):
        @memoize(os.path.join(self.tmp_dir, 'a_{0:d}_c_{c:d}.pkl.gz'))
        def fun(a, b, c):
            return a*b + c

        r = fun(3, 2, c=-1)
        r2 = fun(3, 1, c=-1)
        self.assertEqual(r, r2)

        r3 = load(os.path.join(self.tmp_dir, 'a_3_c_-1.pkl.gz'))
        self.assertEqual(r, r3)

if __name__ == '__main__':
    unittest.main()
