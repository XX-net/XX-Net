import sys, os


class VerificationError(Exception):
    """ An error raised when verification fails
    """

class VerificationMissing(Exception):
    """ An error raised when incomplete structures are passed into
    cdef, but no verification has been done
    """


LIST_OF_FILE_NAMES = ['sources', 'include_dirs', 'library_dirs',
                      'extra_objects', 'depends']

def get_extension(srcfilename, modname, sources=(), **kwds):
    from distutils.core import Extension
    allsources = [srcfilename]
    allsources.extend(sources)
    return Extension(name=modname, sources=allsources, **kwds)

def compile(tmpdir, ext):
    """Compile a C extension module using distutils."""

    saved_environ = os.environ.copy()
    try:
        outputfilename = _build(tmpdir, ext)
        outputfilename = os.path.abspath(outputfilename)
    finally:
        # workaround for a distutils bugs where some env vars can
        # become longer and longer every time it is used
        for key, value in saved_environ.items():
            if os.environ.get(key) != value:
                os.environ[key] = value
    return outputfilename

def _build(tmpdir, ext):
    # XXX compact but horrible :-(
    from distutils.core import Distribution
    import distutils.errors
    #
    dist = Distribution({'ext_modules': [ext]})
    dist.parse_config_files()
    options = dist.get_option_dict('build_ext')
    options['force'] = ('ffiplatform', True)
    options['build_lib'] = ('ffiplatform', tmpdir)
    options['build_temp'] = ('ffiplatform', tmpdir)
    #
    try:
        dist.run_command('build_ext')
    except (distutils.errors.CompileError,
            distutils.errors.LinkError) as e:
        raise VerificationError('%s: %s' % (e.__class__.__name__, e))
    #
    cmd_obj = dist.get_command_obj('build_ext')
    [soname] = cmd_obj.get_outputs()
    return soname

try:
    from os.path import samefile
except ImportError:
    def samefile(f1, f2):
        return os.path.abspath(f1) == os.path.abspath(f2)

def maybe_relative_path(path):
    if not os.path.isabs(path):
        return path      # already relative
    dir = path
    names = []
    while True:
        prevdir = dir
        dir, name = os.path.split(prevdir)
        if dir == prevdir or not dir:
            return path     # failed to make it relative
        names.append(name)
        try:
            if samefile(dir, os.curdir):
                names.reverse()
                return os.path.join(*names)
        except OSError:
            pass

# ____________________________________________________________

try:
    int_or_long = (int, long)
    import cStringIO
except NameError:
    int_or_long = int      # Python 3
    import io as cStringIO

def _flatten(x, f):
    if isinstance(x, str):
        f.write('%ds%s' % (len(x), x))
    elif isinstance(x, dict):
        keys = sorted(x.keys())
        f.write('%dd' % len(keys))
        for key in keys:
            _flatten(key, f)
            _flatten(x[key], f)
    elif isinstance(x, (list, tuple)):
        f.write('%dl' % len(x))
        for value in x:
            _flatten(value, f)
    elif isinstance(x, int_or_long):
        f.write('%di' % (x,))
    else:
        raise TypeError(
            "the keywords to verify() contains unsupported object %r" % (x,))

def flatten(x):
    f = cStringIO.StringIO()
    _flatten(x, f)
    return f.getvalue()
