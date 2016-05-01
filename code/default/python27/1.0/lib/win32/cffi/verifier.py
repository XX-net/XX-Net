import sys, os, binascii, imp, shutil
from . import __version__
from . import ffiplatform


class Verifier(object):

    def __init__(self, ffi, preamble, tmpdir=None, modulename=None,
                 ext_package=None, tag='', force_generic_engine=False, **kwds):
        self.ffi = ffi
        self.preamble = preamble
        if not modulename:
            flattened_kwds = ffiplatform.flatten(kwds)
        vengine_class = _locate_engine_class(ffi, force_generic_engine)
        self._vengine = vengine_class(self)
        self._vengine.patch_extension_kwds(kwds)
        self.kwds = kwds
        #
        if modulename:
            if tag:
                raise TypeError("can't specify both 'modulename' and 'tag'")
        else:
            key = '\x00'.join([sys.version[:3], __version__, preamble,
                               flattened_kwds] +
                              ffi._cdefsources)
            if sys.version_info >= (3,):
                key = key.encode('utf-8')
            k1 = hex(binascii.crc32(key[0::2]) & 0xffffffff)
            k1 = k1.lstrip('0x').rstrip('L')
            k2 = hex(binascii.crc32(key[1::2]) & 0xffffffff)
            k2 = k2.lstrip('0').rstrip('L')
            modulename = '_cffi_%s_%s%s%s' % (tag, self._vengine._class_key,
                                              k1, k2)
        suffix = _get_so_suffixes()[0]
        self.tmpdir = tmpdir or _caller_dir_pycache()
        self.sourcefilename = os.path.join(self.tmpdir, modulename + '.c')
        self.modulefilename = os.path.join(self.tmpdir, modulename + suffix)
        self.ext_package = ext_package
        self._has_source = False
        self._has_module = False

    def write_source(self, file=None):
        """Write the C source code.  It is produced in 'self.sourcefilename',
        which can be tweaked beforehand."""
        with self.ffi._lock:
            if self._has_source and file is None:
                raise ffiplatform.VerificationError(
                    "source code already written")
            self._write_source(file)

    def compile_module(self):
        """Write the C source code (if not done already) and compile it.
        This produces a dynamic link library in 'self.modulefilename'."""
        with self.ffi._lock:
            if self._has_module:
                raise ffiplatform.VerificationError("module already compiled")
            if not self._has_source:
                self._write_source()
            self._compile_module()

    def load_library(self):
        """Get a C module from this Verifier instance.
        Returns an instance of a FFILibrary class that behaves like the
        objects returned by ffi.dlopen(), but that delegates all
        operations to the C module.  If necessary, the C code is written
        and compiled first.
        """
        with self.ffi._lock:
            if not self._has_module:
                self._locate_module()
                if not self._has_module:
                    if not self._has_source:
                        self._write_source()
                    self._compile_module()
            return self._load_library()

    def get_module_name(self):
        basename = os.path.basename(self.modulefilename)
        # kill both the .so extension and the other .'s, as introduced
        # by Python 3: 'basename.cpython-33m.so'
        basename = basename.split('.', 1)[0]
        # and the _d added in Python 2 debug builds --- but try to be
        # conservative and not kill a legitimate _d
        if basename.endswith('_d') and hasattr(sys, 'gettotalrefcount'):
            basename = basename[:-2]
        return basename

    def get_extension(self):
        if not self._has_source:
            with self.ffi._lock:
                if not self._has_source:
                    self._write_source()
        sourcename = ffiplatform.maybe_relative_path(self.sourcefilename)
        modname = self.get_module_name()
        return ffiplatform.get_extension(sourcename, modname, **self.kwds)

    def generates_python_module(self):
        return self._vengine._gen_python_module

    # ----------

    def _locate_module(self):
        if not os.path.isfile(self.modulefilename):
            if self.ext_package:
                try:
                    pkg = __import__(self.ext_package, None, None, ['__doc__'])
                except ImportError:
                    return      # cannot import the package itself, give up
                    # (e.g. it might be called differently before installation)
                path = pkg.__path__
            else:
                path = None
            filename = self._vengine.find_module(self.get_module_name(), path,
                                                 _get_so_suffixes())
            if filename is None:
                return
            self.modulefilename = filename
        self._vengine.collect_types()
        self._has_module = True

    def _write_source(self, file=None):
        must_close = (file is None)
        if must_close:
            _ensure_dir(self.sourcefilename)
            file = open(self.sourcefilename, 'w')
        self._vengine._f = file
        try:
            self._vengine.write_source_to_f()
        finally:
            del self._vengine._f
            if must_close:
                file.close()
        if must_close:
            self._has_source = True

    def _compile_module(self):
        # compile this C source
        tmpdir = os.path.dirname(self.sourcefilename)
        outputfilename = ffiplatform.compile(tmpdir, self.get_extension())
        try:
            same = ffiplatform.samefile(outputfilename, self.modulefilename)
        except OSError:
            same = False
        if not same:
            _ensure_dir(self.modulefilename)
            shutil.move(outputfilename, self.modulefilename)
        self._has_module = True

    def _load_library(self):
        assert self._has_module
        return self._vengine.load_library()

# ____________________________________________________________

_FORCE_GENERIC_ENGINE = False      # for tests

def _locate_engine_class(ffi, force_generic_engine):
    if _FORCE_GENERIC_ENGINE:
        force_generic_engine = True
    if not force_generic_engine:
        if '__pypy__' in sys.builtin_module_names:
            force_generic_engine = True
        else:
            try:
                import _cffi_backend
            except ImportError:
                _cffi_backend = '?'
            if ffi._backend is not _cffi_backend:
                force_generic_engine = True
    if force_generic_engine:
        from . import vengine_gen
        return vengine_gen.VGenericEngine
    else:
        from . import vengine_cpy
        return vengine_cpy.VCPythonEngine

# ____________________________________________________________

_TMPDIR = None

def _caller_dir_pycache():
    if _TMPDIR:
        return _TMPDIR
    filename = sys._getframe(2).f_code.co_filename
    return os.path.abspath(os.path.join(os.path.dirname(filename),
                           '__pycache__'))

def set_tmpdir(dirname):
    """Set the temporary directory to use instead of __pycache__."""
    global _TMPDIR
    _TMPDIR = dirname

def cleanup_tmpdir(tmpdir=None, keep_so=False):
    """Clean up the temporary directory by removing all files in it
    called `_cffi_*.{c,so}` as well as the `build` subdirectory."""
    tmpdir = tmpdir or _caller_dir_pycache()
    try:
        filelist = os.listdir(tmpdir)
    except OSError:
        return
    if keep_so:
        suffix = '.c'   # only remove .c files
    else:
        suffix = _get_so_suffixes()[0].lower()
    for fn in filelist:
        if fn.lower().startswith('_cffi_') and (
                fn.lower().endswith(suffix) or fn.lower().endswith('.c')):
            try:
                os.unlink(os.path.join(tmpdir, fn))
            except OSError:
                pass
    clean_dir = [os.path.join(tmpdir, 'build')]
    for dir in clean_dir:
        try:
            for fn in os.listdir(dir):
                fn = os.path.join(dir, fn)
                if os.path.isdir(fn):
                    clean_dir.append(fn)
                else:
                    os.unlink(fn)
        except OSError:
            pass

def _get_so_suffixes():
    suffixes = []
    for suffix, mode, type in imp.get_suffixes():
        if type == imp.C_EXTENSION:
            suffixes.append(suffix)

    if not suffixes:
        # bah, no C_EXTENSION available.  Occurs on pypy without cpyext
        if sys.platform == 'win32':
            suffixes = [".pyd"]
        else:
            suffixes = [".so"]

    return suffixes

def _ensure_dir(filename):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
