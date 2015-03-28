#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#



"""Import hook for dev_appserver.py."""

import dummy_thread
import errno
import imp
import itertools
import locale
import logging
import mimetypes
import os
import pickle
import random
import re
import select
import socket
import sys
import urllib

try:
  import distutils.util
except ImportError:



  pass



from google.appengine import dist



SITE_PACKAGES = os.path.normcase(os.path.join(os.path.dirname(os.__file__),
                                              'site-packages'))


import google
SDK_ROOT = os.path.dirname(os.path.dirname(google.__file__))


CODING_COOKIE_RE = re.compile("coding[:=]\s*([-\w.]+)")
DEFAULT_ENCODING = 'ascii'


def FakeURandom(n):
  """Fake version of os.urandom."""
  bytes = ''
  for _ in range(n):
    bytes += chr(random.randint(0, 255))
  return bytes


def FakeUname():
  """Fake version of os.uname."""
  return ('Linux', '', '', '', '')


def FakeUnlink(path):
  """Fake version of os.unlink."""
  if os.path.isdir(path):
    raise OSError(errno.ENOENT, "Is a directory", path)
  else:
    raise OSError(errno.EPERM, "Operation not permitted", path)


def FakeReadlink(path):
  """Fake version of os.readlink."""
  raise OSError(errno.EINVAL, "Invalid argument", path)


def FakeAccess(path, mode):
  """Fake version of os.access where only reads are supported."""
  if not os.path.exists(path) or mode != os.R_OK:
    return False
  else:
    return True


def FakeSetLocale(category, value=None, original_setlocale=locale.setlocale):
  """Fake version of locale.setlocale that only supports the default."""
  if value not in (None, '', 'C', 'POSIX'):
    raise locale.Error('locale emulation only supports "C" locale')
  return original_setlocale(category, 'C')


def FakeOpen(filename, flags, mode=0777):
  """Fake version of os.open."""
  raise OSError(errno.EPERM, "Operation not permitted", filename)


def FakeRename(src, dst):
  """Fake version of os.rename."""
  raise OSError(errno.EPERM, "Operation not permitted", src)


def FakeUTime(path, times):
  """Fake version of os.utime."""
  raise OSError(errno.EPERM, "Operation not permitted", path)


def FakeFileObject(fp, mode='rb', bufsize=-1, close=False):
  """Assuming that the argument is a StringIO or file instance."""
  if not hasattr(fp, 'fileno'):
    fp.fileno = lambda: None
  return fp


def FakeGetHostByAddr(addr):
  """Fake version of socket.gethostbyaddr."""
  raise NotImplementedError()


def FakeGetProtoByName(protocolname):
  """Fake version of socket.getprotobyname."""
  raise NotImplementedError()


def FakeGetServByPort(portnumber, protocolname=None):
  """Fake version of socket.getservbyport."""
  raise NotImplementedError()


def FakeGetNameInfo(sockaddr, flags):
  """Fake version of socket.getnameinfo."""
  raise NotImplementedError()


def FakeSocketRecvInto(buf, nbytes=0, flags=0):
  """Fake version of socket.socket.recvinto."""
  raise NotImplementedError()


def FakeSocketRecvFromInto(buffer, nbytes=0, flags=0):
  """Fake version of socket.socket.recvfrom_into."""
  raise NotImplementedError()


def FakeGetPlatform():
  """Fake distutils.util.get_platform on OS/X.  Pass-through otherwise."""
  if sys.platform == 'darwin':
    return 'macosx-'
  else:
    return distutils.util.get_platform()






def NeedsMacOSXProxyFakes():
  """Returns True if the MacOS X urllib fakes should be installed."""
  return (sys.platform == 'darwin' and
          (2, 6, 0) <= sys.version_info < (2, 6, 4))


if NeedsMacOSXProxyFakes():
  def _FakeProxyBypassHelper(fn,
                             original_module_dict=sys.modules.copy(),
                             original_uname=os.uname):
    """Setups and restores the state for the Mac OS X urllib fakes."""
    def Inner(*args, **kwargs):
      current_uname = os.uname
      current_meta_path = sys.meta_path[:]
      current_modules = sys.modules.copy()

      try:
        sys.modules.clear()
        sys.modules.update(original_module_dict)
        sys.meta_path[:] = []
        os.uname = original_uname

        return fn(*args, **kwargs)
      finally:
        sys.modules.clear()
        sys.modules.update(current_modules)
        os.uname = current_uname
        sys.meta_path[:] = current_meta_path
    return Inner


  @_FakeProxyBypassHelper
  def FakeProxyBypassMacOSXSysconf(
      host,
      original_proxy_bypass_macosx_sysconf=urllib.proxy_bypass_macosx_sysconf):
    """Fake for urllib.proxy_bypass_macosx_sysconf for Python 2.6.0 to 2.6.3."""
    return original_proxy_bypass_macosx_sysconf(host)


  @_FakeProxyBypassHelper
  def FakeGetProxiesMacOSXSysconf(
      original_getproxies_macosx_sysconf=urllib.getproxies_macosx_sysconf):
    """Fake for urllib.getproxies_macosx_sysconf for Python 2.6.0 to 2.6.3."""
    return original_getproxies_macosx_sysconf()


def IsPathInSubdirectories(filename,
                           subdirectories,
                           normcase=os.path.normcase):
  """Determines if a filename is contained within one of a set of directories.

  Args:
    filename: Path of the file (relative or absolute).
    subdirectories: Iterable collection of paths to subdirectories which the
      given filename may be under.
    normcase: Used for dependency injection.

  Returns:
    True if the supplied filename is in one of the given sub-directories or
    its hierarchy of children. False otherwise.
  """
  file_dir = normcase(os.path.dirname(os.path.abspath(filename)))
  for parent in subdirectories:
    fixed_parent = normcase(os.path.abspath(parent))
    if os.path.commonprefix([file_dir, fixed_parent]) == fixed_parent:
      return True
  return False


def GeneratePythonPaths(*p):
  """Generate all valid filenames for the given file.

  Args:
    p: Positional args are the folders to the file and finally the file
       without a suffix.

  Returns:
    A list of strings representing the given path to a file with each valid
      suffix for this python build.
  """
  suffixes = imp.get_suffixes()
  return [os.path.join(*p) + s for s, m, t in suffixes]


class FakeFile(file):
  """File sub-class that enforces the security restrictions of the production
  environment.
  """

  ALLOWED_MODES = frozenset(['r', 'rb', 'U', 'rU'])


  ALLOWED_FILES = set(os.path.normcase(filename)
                      for filename in mimetypes.knownfiles
                      if os.path.isfile(filename))






  ALLOWED_DIRS = set([
      os.path.normcase(os.path.realpath(os.path.dirname(os.__file__))),
      os.path.normcase(os.path.abspath(os.path.dirname(os.__file__))),
      os.path.normcase(os.path.dirname(os.path.realpath(os.__file__))),
      os.path.normcase(os.path.dirname(os.path.abspath(os.__file__))),
  ])




  NOT_ALLOWED_DIRS = set([




      SITE_PACKAGES,
  ])








  ALLOWED_SITE_PACKAGE_DIRS = set(
      os.path.normcase(os.path.abspath(os.path.join(SITE_PACKAGES, path)))
      for path in [

          ])

  ALLOWED_SITE_PACKAGE_FILES = set(
      os.path.normcase(os.path.abspath(os.path.join(
          os.path.dirname(os.__file__), 'site-packages', path)))
      for path in itertools.chain(*[

          [os.path.join('Crypto')],
          GeneratePythonPaths('Crypto', '__init__'),
          [os.path.join('Crypto', 'Cipher')],
          GeneratePythonPaths('Crypto', 'Cipher', '__init__'),
          GeneratePythonPaths('Crypto', 'Cipher', 'AES'),
          GeneratePythonPaths('Crypto', 'Cipher', 'ARC2'),
          GeneratePythonPaths('Crypto', 'Cipher', 'ARC4'),
          GeneratePythonPaths('Crypto', 'Cipher', 'Blowfish'),
          GeneratePythonPaths('Crypto', 'Cipher', 'CAST'),
          GeneratePythonPaths('Crypto', 'Cipher', 'DES'),
          GeneratePythonPaths('Crypto', 'Cipher', 'DES3'),
          GeneratePythonPaths('Crypto', 'Cipher', 'XOR'),
          [os.path.join('Crypto', 'Hash')],
          GeneratePythonPaths('Crypto', 'Hash', '__init__'),
          GeneratePythonPaths('Crypto', 'Hash', 'HMAC'),
          os.path.join('Crypto', 'Hash', 'MD2'),
          os.path.join('Crypto', 'Hash', 'MD4'),
          GeneratePythonPaths('Crypto', 'Hash', 'MD5'),
          GeneratePythonPaths('Crypto', 'Hash', 'SHA'),
          os.path.join('Crypto', 'Hash', 'SHA256'),
          os.path.join('Crypto', 'Hash', 'RIPEMD'),
          [os.path.join('Crypto', 'Protocol')],
          GeneratePythonPaths('Crypto', 'Protocol', '__init__'),
          GeneratePythonPaths('Crypto', 'Protocol', 'AllOrNothing'),
          GeneratePythonPaths('Crypto', 'Protocol', 'Chaffing'),
          [os.path.join('Crypto', 'PublicKey')],
          GeneratePythonPaths('Crypto', 'PublicKey', '__init__'),
          GeneratePythonPaths('Crypto', 'PublicKey', 'DSA'),
          GeneratePythonPaths('Crypto', 'PublicKey', 'ElGamal'),
          GeneratePythonPaths('Crypto', 'PublicKey', 'RSA'),
          GeneratePythonPaths('Crypto', 'PublicKey', 'pubkey'),
          GeneratePythonPaths('Crypto', 'PublicKey', 'qNEW'),
          [os.path.join('Crypto', 'Util')],
          GeneratePythonPaths('Crypto', 'Util', '__init__'),
          GeneratePythonPaths('Crypto', 'Util', 'RFC1751'),
          GeneratePythonPaths('Crypto', 'Util', 'number'),
          GeneratePythonPaths('Crypto', 'Util', 'randpool'),
          ]))



  _original_file = file


  _root_path = None
  _application_paths = None
  _skip_files = None
  _static_file_config_matcher = None


  _allow_skipped_files = True


  _availability_cache = {}

  @staticmethod
  def SetAllowedPaths(root_path, application_paths):
    """Configures which paths are allowed to be accessed.

    Must be called at least once before any file objects are created in the
    hardened environment.

    Args:
      root_path: Absolute path to the root of the application.
      application_paths: List of additional paths that the application may
                         access, this must include the App Engine runtime but
                         not the Python library directories.
    """


    FakeFile._application_paths = (set(os.path.realpath(path)
                                       for path in application_paths) |
                                   set(os.path.abspath(path)
                                       for path in application_paths))
    FakeFile._application_paths.add(root_path)


    FakeFile._root_path = os.path.join(root_path, '')

    FakeFile._availability_cache = {}

  @staticmethod
  def SetAllowSkippedFiles(allow_skipped_files):
    """Configures access to files matching FakeFile._skip_files.

    Args:
      allow_skipped_files: Boolean whether to allow access to skipped files
    """
    FakeFile._allow_skipped_files = allow_skipped_files
    FakeFile._availability_cache = {}

  @staticmethod
  def SetAllowedModule(name):
    """Allow the use of a module based on where it is located.

    Meant to be used by use_library() so that it has a link back into the
    trusted part of the interpreter.

    Args:
      name: Name of the module to allow.
    """
    stream, pathname, description = imp.find_module(name)
    pathname = os.path.normcase(os.path.abspath(pathname))
    if stream:
      stream.close()
      FakeFile.ALLOWED_FILES.add(pathname)
      FakeFile.ALLOWED_FILES.add(os.path.realpath(pathname))
    else:
      assert description[2] == imp.PKG_DIRECTORY
      if pathname.startswith(SITE_PACKAGES):
        FakeFile.ALLOWED_SITE_PACKAGE_DIRS.add(pathname)
        FakeFile.ALLOWED_SITE_PACKAGE_DIRS.add(os.path.realpath(pathname))
      else:
        FakeFile.ALLOWED_DIRS.add(pathname)
        FakeFile.ALLOWED_DIRS.add(os.path.realpath(pathname))

  @staticmethod
  def SetSkippedFiles(skip_files):
    """Sets which files in the application directory are to be ignored.

    Must be called at least once before any file objects are created in the
    hardened environment.

    Must be called whenever the configuration was updated.

    Args:
      skip_files: Object with .match() method (e.g. compiled regexp).
    """
    FakeFile._skip_files = skip_files
    FakeFile._availability_cache = {}

  @staticmethod
  def SetStaticFileConfigMatcher(static_file_config_matcher):
    """Sets StaticFileConfigMatcher instance for checking if a file is static.

    Must be called at least once before any file objects are created in the
    hardened environment.

    Must be called whenever the configuration was updated.

    Args:
      static_file_config_matcher: StaticFileConfigMatcher instance.
    """
    FakeFile._static_file_config_matcher = static_file_config_matcher
    FakeFile._availability_cache = {}

  @staticmethod
  def IsFileAccessible(filename, normcase=os.path.normcase):
    """Determines if a file's path is accessible.

    SetAllowedPaths(), SetSkippedFiles() and SetStaticFileConfigMatcher() must
    be called before this method or else all file accesses will raise an error.

    Args:
      filename: Path of the file to check (relative or absolute). May be a
        directory, in which case access for files inside that directory will
        be checked.
      normcase: Used for dependency injection.

    Returns:
      True if the file is accessible, False otherwise.
    """



    logical_filename = normcase(os.path.abspath(filename))







    result = FakeFile._availability_cache.get(logical_filename)
    if result is None:
      result = FakeFile._IsFileAccessibleNoCache(logical_filename,
                                                 normcase=normcase)
      FakeFile._availability_cache[logical_filename] = result
    return result

  @staticmethod
  def _IsFileAccessibleNoCache(logical_filename, normcase=os.path.normcase):
    """Determines if a file's path is accessible.

    This is an internal part of the IsFileAccessible implementation.

    Args:
      logical_filename: Absolute path of the file to check.
      normcase: Used for dependency injection.

    Returns:
      True if the file is accessible, False otherwise.
    """




    logical_dirfakefile = logical_filename
    if os.path.isdir(logical_filename):
      logical_dirfakefile = os.path.join(logical_filename, 'foo')


    if IsPathInSubdirectories(logical_dirfakefile, [FakeFile._root_path],
                              normcase=normcase):

      relative_filename = logical_dirfakefile[len(FakeFile._root_path):]

      if not FakeFile._allow_skipped_files:
        path = relative_filename
        while path != os.path.dirname(path):
          if FakeFile._skip_files.match(path):
            logging.warning('Blocking access to skipped file "%s"',
                            logical_filename)
            return False
          path = os.path.dirname(path)

      if FakeFile._static_file_config_matcher.IsStaticFile(relative_filename):
        logging.warning('Blocking access to static file "%s"',
                        logical_filename)
        return False

    if logical_filename in FakeFile.ALLOWED_FILES:
      return True

    if logical_filename in FakeFile.ALLOWED_SITE_PACKAGE_FILES:
      return True

    if IsPathInSubdirectories(logical_dirfakefile,
                              FakeFile.ALLOWED_SITE_PACKAGE_DIRS,
                              normcase=normcase):
      return True

    allowed_dirs = FakeFile._application_paths | FakeFile.ALLOWED_DIRS
    if (IsPathInSubdirectories(logical_dirfakefile,
                               allowed_dirs,
                               normcase=normcase) and
        not IsPathInSubdirectories(logical_dirfakefile,
                                   FakeFile.NOT_ALLOWED_DIRS,
                                   normcase=normcase)):
      return True

    return False

  def __init__(self, filename, mode='r', bufsize=-1, **kwargs):
    """Initializer. See file built-in documentation."""
    if mode not in FakeFile.ALLOWED_MODES:




      raise IOError('invalid mode: %s' % mode)

    if not FakeFile.IsFileAccessible(filename):
      raise IOError(errno.EACCES, 'file not accessible', filename)

    super(FakeFile, self).__init__(filename, mode, bufsize, **kwargs)




dist._library.SetAllowedModule = FakeFile.SetAllowedModule


class RestrictedPathFunction(object):
  """Enforces access restrictions for functions that have a file or
  directory path as their first argument."""

  _original_os = os

  def __init__(self, original_func):
    """Initializer.

    Args:
      original_func: Callable that takes as its first argument the path to a
        file or directory on disk; all subsequent arguments may be variable.
    """
    self._original_func = original_func

  def __call__(self, path, *args, **kwargs):
    """Enforces access permissions for the function passed to the constructor.
    """
    if not FakeFile.IsFileAccessible(path):
      raise OSError(errno.EACCES, 'path not accessible', path)

    return self._original_func(path, *args, **kwargs)


def GetSubmoduleName(fullname):
  """Determines the leaf submodule name of a full module name.

  Args:
    fullname: Fully qualified module name, e.g. 'foo.bar.baz'

  Returns:
    Submodule name, e.g. 'baz'. If the supplied module has no submodule (e.g.,
    'stuff'), the returned value will just be that module name ('stuff').
  """
  return fullname.rsplit('.', 1)[-1]


class CouldNotFindModuleError(ImportError):
  """Raised when a module could not be found.

  In contrast to when a module has been found, but cannot be loaded because of
  hardening restrictions.
  """


def Trace(func):
  """Call stack logging decorator for HardenedModulesHook class.

  This decorator logs the call stack of the HardenedModulesHook class as
  it executes, indenting logging messages based on the current stack depth.

  Args:
    func: the function to decorate.

  Returns:
    The decorated function.
  """

  def Decorate(self, *args, **kwargs):
    args_to_show = []
    if args is not None:
      args_to_show.extend(str(argument) for argument in args)
    if kwargs is not None:
      args_to_show.extend('%s=%s' % (key, value)
                          for key, value in kwargs.iteritems())

    args_string = ', '.join(args_to_show)

    self.log('Entering %s(%s)', func.func_name, args_string)
    self._indent_level += 1
    try:
      return func(self, *args, **kwargs)
    finally:
      self._indent_level -= 1
      self.log('Exiting %s(%s)', func.func_name, args_string)

  return Decorate


class HardenedModulesHook(object):
  """Meta import hook that restricts the modules used by applications to match
  the production environment.

  Module controls supported:
  - Disallow native/extension modules from being loaded
  - Disallow built-in and/or Python-distributed modules from being loaded
  - Replace modules with completely empty modules
  - Override specific module attributes
  - Replace one module with another

  After creation, this object should be added to the front of the sys.meta_path
  list (which may need to be created). The sys.path_importer_cache dictionary
  should also be cleared, to prevent loading any non-restricted modules.

  See PEP302 for more info on how this works:
    http://www.python.org/dev/peps/pep-0302/
  """



  ENABLE_LOGGING = False

  def log(self, message, *args):
    """Logs an import-related message to stderr, with indentation based on
    current call-stack depth.

    Args:
      message: Logging format string.
      args: Positional format parameters for the logging message.
    """
    if HardenedModulesHook.ENABLE_LOGGING:
      indent = self._indent_level * '  '
      print >>sys.__stderr__, indent + (message % args)






  _WHITE_LIST_C_MODULES = [
      'py_streamhtmlparser',
      'AES',
      'ARC2',
      'ARC4',
      'Blowfish',
      'CAST',
      'DES',
      'DES3',
      'MD2',
      'MD4',
      'RIPEMD',
      'SHA256',
      'XOR',

      '_Crypto_Cipher__AES',
      '_Crypto_Cipher__ARC2',
      '_Crypto_Cipher__ARC4',
      '_Crypto_Cipher__Blowfish',
      '_Crypto_Cipher__CAST',
      '_Crypto_Cipher__DES',
      '_Crypto_Cipher__DES3',
      '_Crypto_Cipher__XOR',
      '_Crypto_Hash__MD2',
      '_Crypto_Hash__MD4',
      '_Crypto_Hash__RIPEMD',
      '_Crypto_Hash__SHA256',
      'array',
      'binascii',
      'bz2',
      'cmath',
      'collections',
      'crypt',
      'cStringIO',
      'datetime',
      'errno',
      'exceptions',
      'gc',
      'itertools',
      'math',
      'md5',
      'operator',
      'posix',
      'posixpath',
      'pyexpat',
      'sha',
      'struct',
      'sys',
      'time',
      'timing',
      'unicodedata',
      'zlib',
      '_ast',
      '_bisect',
      '_codecs',
      '_codecs_cn',
      '_codecs_hk',
      '_codecs_iso2022',
      '_codecs_jp',
      '_codecs_kr',
      '_codecs_tw',
      '_collections',
      '_csv',
      '_elementtree',
      '_functools',
      '_hashlib',
      '_heapq',
      '_locale',
      '_lsprof',
      '_md5',
      '_multibytecodec',
      '_scproxy',
      '_random',
      '_sha',
      '_sha256',
      '_sha512',
      '_sre',
      '_struct',
      '_types',
      '_weakref',
      '__main__',
  ]




  _PY27_ALLOWED_MODULES = [
    '_bytesio',
    '_fileio',
    '_io',
    '_json',
    '_symtable',
    '_yaml',
    'parser',
    'strop',






  ]
















  __PY27_OPTIONAL_ALLOWED_MODULES = {

    'django': [],
    'jinja2': ['_speedups'],
    'lxml': ['etree', 'objectify'],
    'markupsafe': ['_speedups'],
    'numpy': [
      '_capi',
      '_compiled_base',
      '_dotblas',
      'fftpack_lite',
      'lapack_lite',
      'mtrand',
      'multiarray',
      'scalarmath',
      '_sort',
      'umath',
      'umath_tests',
    ],
    'PIL': ['_imaging', '_imagingcms', '_imagingft', '_imagingmath'],



    'setuptools': [],


  }

  __CRYPTO_CIPHER_ALLOWED_MODULES = [
      'MODE_CBC',
      'MODE_CFB',
      'MODE_CTR',
      'MODE_ECB',
      'MODE_OFB',
      'block_size',
      'key_size',
      'new',
  ]




  _WHITE_LIST_PARTIAL_MODULES = {
      'Crypto.Cipher.AES': __CRYPTO_CIPHER_ALLOWED_MODULES,
      'Crypto.Cipher.ARC2': __CRYPTO_CIPHER_ALLOWED_MODULES,
      'Crypto.Cipher.Blowfish': __CRYPTO_CIPHER_ALLOWED_MODULES,
      'Crypto.Cipher.CAST': __CRYPTO_CIPHER_ALLOWED_MODULES,
      'Crypto.Cipher.DES': __CRYPTO_CIPHER_ALLOWED_MODULES,
      'Crypto.Cipher.DES3': __CRYPTO_CIPHER_ALLOWED_MODULES,


      'gc': [
          'enable',
          'disable',
          'isenabled',
          'collect',
          'get_debug',
          'set_threshold',
          'get_threshold',
          'get_count'
      ],




      'os': [
          'access',
          'altsep',
          'curdir',
          'defpath',
          'devnull',
          'environ',
          'error',
          'extsep',
          'EX_NOHOST',
          'EX_NOINPUT',
          'EX_NOPERM',
          'EX_NOUSER',
          'EX_OK',
          'EX_OSERR',
          'EX_OSFILE',
          'EX_PROTOCOL',
          'EX_SOFTWARE',
          'EX_TEMPFAIL',
          'EX_UNAVAILABLE',
          'EX_USAGE',
          'F_OK',
          'getcwd',
          'getcwdu',
          'getenv',

          'listdir',
          'lstat',
          'name',
          'NGROUPS_MAX',
          'O_APPEND',
          'O_CREAT',
          'O_DIRECT',
          'O_DIRECTORY',
          'O_DSYNC',
          'O_EXCL',
          'O_LARGEFILE',
          'O_NDELAY',
          'O_NOCTTY',
          'O_NOFOLLOW',
          'O_NONBLOCK',
          'O_RDONLY',
          'O_RDWR',
          'O_RSYNC',
          'O_SYNC',
          'O_TRUNC',
          'O_WRONLY',
          'open',
          'pardir',
          'path',
          'pathsep',
          'R_OK',
          'readlink',
          'remove',
          'rename',
          'SEEK_CUR',
          'SEEK_END',
          'SEEK_SET',
          'sep',
          'stat',
          'stat_float_times',
          'stat_result',
          'strerror',
          'TMP_MAX',
          'unlink',
          'urandom',
          'utime',
          'walk',
          'WCOREDUMP',
          'WEXITSTATUS',
          'WIFEXITED',
          'WIFSIGNALED',
          'WIFSTOPPED',
          'WNOHANG',
          'WSTOPSIG',
          'WTERMSIG',
          'WUNTRACED',
          'W_OK',
          'X_OK',
      ],


      'signal': [
      ],

      'socket': [

          '_GLOBAL_DEFAULT_TIMEOUT',


          'AF_INET',

          'SOCK_STREAM',
          'SOCK_DGRAM',





































































          'error',
          'gaierror',
          'herror',
          'timeout',























          'ssl',




          '_fileobject',

      ],

      'select': [





      ],

      'ssl': [
      ],
  }









  _MODULE_OVERRIDES = {
      'locale': {
          'setlocale': FakeSetLocale,
      },

      'os': {
          'access': FakeAccess,
          'listdir': RestrictedPathFunction(os.listdir),

          'lstat': RestrictedPathFunction(os.stat),
          'open': FakeOpen,
          'readlink': FakeReadlink,
          'remove': FakeUnlink,
          'rename': FakeRename,
          'stat': RestrictedPathFunction(os.stat),
          'uname': FakeUname,
          'unlink': FakeUnlink,
          'urandom': FakeURandom,
          'utime': FakeUTime,
      },

      'signal': {

          '__doc__': None,
      },

      'socket': {
          '_fileobject': FakeFileObject,
          'ssl': None,











      },

      'distutils.util': {
          'get_platform': FakeGetPlatform,
      },
  }


  _ENABLED_FILE_TYPES = (
      imp.PKG_DIRECTORY,
      imp.PY_SOURCE,
      imp.PY_COMPILED,
      imp.C_BUILTIN,
  )

  def __init__(self,
               config,
               module_dict,
               app_code_path,
               imp_module=imp,
               os_module=os,
               dummy_thread_module=dummy_thread,
               pickle_module=pickle,
               socket_module=socket,
               select_module=select):
    """Initializer.

    Args:
      config: AppInfoExternal instance representing the parsed app.yaml file.
      module_dict: Module dictionary to use for managing system modules.
        Should be sys.modules.
      app_code_path: The absolute path to the application code on disk.
      imp_module, os_module, dummy_thread_module, etc.: References to
        modules that exist in the dev_appserver that must be used by this class
        in order to function, even if these modules have been unloaded from
        sys.modules.
    """
    self._config = config
    self._module_dict = module_dict
    self._imp = imp_module
    self._os = os_module
    self._dummy_thread = dummy_thread_module
    self._pickle = pickle
    self._socket = socket_module

    self._socket.buffer = buffer
    self._select = select_module
    self._indent_level = 0
    self._app_code_path = app_code_path
    self._white_list_c_modules = list(self._WHITE_LIST_C_MODULES)
    self._white_list_partial_modules = dict(self._WHITE_LIST_PARTIAL_MODULES)
    self._enabled_modules = []

    if self._config and self._config.runtime == 'python27':
      self._white_list_c_modules.extend(self._PY27_ALLOWED_MODULES)



      self._white_list_partial_modules['os'] = (
        list(self._white_list_partial_modules['os']) + ['getpid', 'getuid'])

      if self._config.libraries:
        for libentry in self._config.libraries:
          self._enabled_modules.append(libentry.name)
          extra = self.__PY27_OPTIONAL_ALLOWED_MODULES.get(libentry.name)
          logging.debug('Enabling %s: %r', libentry.name, extra)
          if extra:
            self._white_list_c_modules.extend(extra)
          if libentry.name == 'django':




            if 'django' not in self._module_dict:
              version = libentry.version
              if version == 'latest':
                version = '1.2'
              sitedir = os.path.join(SDK_ROOT,
                                     'lib',
                                     'django_%s' % version.replace('.', '_'))
              if os.path.isdir(sitedir):
                logging.debug('Enabling Django version %s at %s',
                              version, sitedir)
                sys.path[:] = [dirname
                               for dirname in sys.path
                               if not dirname.startswith(os.path.join(
                                 SDK_ROOT, 'lib', 'django'))]
                sys.path.insert(1, sitedir)
              else:
                logging.warn('Enabling Django version %s (no directory found)',
                             version)


  @Trace
  def find_module(self, fullname, path=None):
    """See PEP 302."""




    if fullname in ('cPickle', 'thread'):
      return self

    search_path = path
    all_modules = fullname.split('.')
    try:
      for index, current_module in enumerate(all_modules):
        current_module_fullname = '.'.join(all_modules[:index + 1])
        if (current_module_fullname == fullname and not
            self.StubModuleExists(fullname)):






          self.FindModuleRestricted(current_module,
                                    current_module_fullname,
                                    search_path)
        else:



          if current_module_fullname in self._module_dict:
            module = self._module_dict[current_module_fullname]
          else:

            module = self.FindAndLoadModule(current_module,
                                            current_module_fullname,
                                            search_path)







          if hasattr(module, '__path__'):
            search_path = module.__path__
    except CouldNotFindModuleError:









      return None



    return self

  def StubModuleExists(self, name):
    """Check if the named module has a stub replacement."""
    if name in sys.builtin_module_names:
      name = 'py_%s' % name
    if name in dist.__all__:
      return True
    return False

  def ImportStubModule(self, name):
    """Import the stub module replacement for the specified module."""
    if name in sys.builtin_module_names:
      name = 'py_%s' % name



    module = __import__(dist.__name__, {}, {}, [name])
    return getattr(module, name)

  @Trace
  def FixModule(self, module):
    """Prunes and overrides restricted module attributes.

    Args:
      module: The module to prune. This should be a new module whose attributes
        reference back to the real module's __dict__ members.
    """

    if module.__name__ in self._white_list_partial_modules:
      allowed_symbols = self._white_list_partial_modules[module.__name__]
      for symbol in set(module.__dict__) - set(allowed_symbols):
        if not (symbol.startswith('__') and symbol.endswith('__')):
          del module.__dict__[symbol]


    if module.__name__ in self._MODULE_OVERRIDES:
      module.__dict__.update(self._MODULE_OVERRIDES[module.__name__])

    if module.__name__ == 'urllib' and NeedsMacOSXProxyFakes():
      module.__dict__.update(
          {'proxy_bypass_macosx_sysconf': FakeProxyBypassMacOSXSysconf,
           'getproxies_macosx_sysconf': FakeGetProxiesMacOSXSysconf})

  @Trace
  def FindModuleRestricted(self,
                           submodule,
                           submodule_fullname,
                           search_path):
    """Locates a module while enforcing module import restrictions.

    Args:
      submodule: The short name of the submodule (i.e., the last section of
        the fullname; for 'foo.bar' this would be 'bar').
      submodule_fullname: The fully qualified name of the module to find (e.g.,
        'foo.bar').
      search_path: List of paths to search for to find this module. Should be
        None if the current sys.path should be used.

    Returns:
      Tuple (source_file, pathname, description) where:
        source_file: File-like object that contains the module; in the case
          of packages, this will be None, which implies to look at __init__.py.
        pathname: String containing the full path of the module on disk.
        description: Tuple returned by imp.find_module().
      However, in the case of an import using a path hook (e.g. a zipfile),
      source_file will be a PEP-302-style loader object, pathname will be None,
      and description will be a tuple filled with None values.

    Raises:
      ImportError exception if the requested module was found, but importing
      it is disallowed.

      CouldNotFindModuleError exception if the request module could not even
      be found for import.
    """
    if search_path is None:


      search_path = [None] + sys.path

    module_import_ok = False
    if self._config and self._config.runtime == 'python27':





      topmodule = submodule_fullname.split('.')[0]
      if topmodule in self.__PY27_OPTIONAL_ALLOWED_MODULES:
        if topmodule in self._enabled_modules:




          module_import_ok = True



        else:
          msg = ('Third party package %s must be included in the '
                 '"libraries:" clause of your app.yaml file '
                 'in order to be imported.' % topmodule)
          logging.error(msg)


          raise ImportError(msg)






    import_error = None
    for path_entry in search_path:
      result = self.FindPathHook(submodule, submodule_fullname, path_entry)
      if result is not None:
        source_file, pathname, description = result
        if description == (None, None, None):

          return result




















        suffix, mode, file_type = description

        try:
          if (file_type not in (self._imp.C_BUILTIN, self._imp.C_EXTENSION) and
              not module_import_ok and
              not FakeFile.IsFileAccessible(pathname)):
            error_message = 'Access to module file denied: %s' % pathname
            logging.debug(error_message)
            raise ImportError(error_message)

          if (file_type not in self._ENABLED_FILE_TYPES and
              submodule not in self._white_list_c_modules):
            error_message = ('Could not import "%s": Disallowed C-extension '
                             'or built-in module' % submodule_fullname)
            logging.debug(error_message)
            raise ImportError(error_message)
          return source_file, pathname, description
        except ImportError, e:


          import_error = e

    if import_error:


      raise import_error


    self.log('Could not find module "%s"', submodule_fullname)
    raise CouldNotFindModuleError()


  def FindPathHook(self, submodule, submodule_fullname, path_entry):
    """Helper for FindModuleRestricted to find a module in a sys.path entry.

    Args:
      submodule:
      submodule_fullname:
      path_entry: A single sys.path entry, or None representing the builtins.

    Returns:
      Either None (if nothing was found), or a triple (source_file, path_name,
      description).  See the doc string for FindModuleRestricted() for the
      meaning of the latter.
    """
    if path_entry is None:

      if submodule_fullname in sys.builtin_module_names:
        try:
          result = self._imp.find_module(submodule)
        except ImportError:
          pass
        else:

          source_file, pathname, description = result
          suffix, mode, file_type = description
          if file_type == self._imp.C_BUILTIN:
            return result

      return None





    if path_entry in sys.path_importer_cache:
      importer = sys.path_importer_cache[path_entry]
    else:

      importer = None
      for hook in sys.path_hooks:
        try:
          importer = hook(path_entry)

          break
        except ImportError:

          pass

      sys.path_importer_cache[path_entry] = importer

    if importer is None:

      try:
        return self._imp.find_module(submodule, [path_entry])
      except ImportError:
        pass
    else:

      loader = importer.find_module(submodule)
      if loader is not None:




        return (loader, None, (None, None, None))


    return None

  @Trace
  def LoadModuleRestricted(self,
                           submodule_fullname,
                           source_file,
                           pathname,
                           description):
    """Loads a module while enforcing module import restrictions.

    As a byproduct, the new module will be added to the module dictionary.

    Args:
      submodule_fullname: The fully qualified name of the module to find (e.g.,
        'foo.bar').
      source_file: File-like object that contains the module's source code,
        or a PEP-302-style loader object.
      pathname: String containing the full path of the module on disk.
      description: Tuple returned by imp.find_module(), or (None, None, None)
        in case source_file is a PEP-302-style loader object.

    Returns:
      The new module.

    Raises:
      ImportError exception of the specified module could not be loaded for
      whatever reason.
    """
    if description == (None, None, None):


      return source_file.load_module(submodule_fullname)

    try:
      try:











        return self._imp.load_module(submodule_fullname,
                                     source_file,
                                     pathname,
                                     description)
      except:


        if submodule_fullname in self._module_dict:
          del self._module_dict[submodule_fullname]
        raise

    finally:
      if source_file is not None:
        source_file.close()

  @Trace
  def FindAndLoadModule(self,
                        submodule,
                        submodule_fullname,
                        search_path):
    """Finds and loads a module, loads it, and adds it to the module dictionary.

    Args:
      submodule: Name of the module to import (e.g., baz).
      submodule_fullname: Full name of the module to import (e.g., foo.bar.baz).
      search_path: Path to use for searching for this submodule. For top-level
        modules this should be None; otherwise it should be the __path__
        attribute from the parent package.

    Returns:
      A new module instance that has been inserted into the module dictionary
      supplied to __init__.

    Raises:
      ImportError exception if the module could not be loaded for whatever
      reason (e.g., missing, not allowed).
    """
    module = self._imp.new_module(submodule_fullname)

    if submodule_fullname == 'thread':
      module.__dict__.update(self._dummy_thread.__dict__)
      module.__name__ = 'thread'
    elif submodule_fullname == 'cPickle':
      module.__dict__.update(self._pickle.__dict__)
      module.__name__ = 'cPickle'
    elif submodule_fullname == 'os':
      module.__dict__.update(self._os.__dict__)
    elif submodule_fullname == 'socket':
      module.__dict__.update(self._socket.__dict__)
    elif submodule_fullname == 'select':
      module.__dict__.update(self._select.__dict__)
    elif submodule_fullname == 'ssl':
      pass
    elif self.StubModuleExists(submodule_fullname):
      module = self.ImportStubModule(submodule_fullname)
    else:
      source_file, pathname, description = self.FindModuleRestricted(submodule, submodule_fullname, search_path)
      module = self.LoadModuleRestricted(submodule_fullname,
                                         source_file,
                                         pathname,
                                         description)




    if (getattr(module, '__path__', None) is not None and
        search_path != self._app_code_path):
      try:
        app_search_path = os.path.join(self._app_code_path,
                                       *(submodule_fullname.split('.')[:-1]))
        source_file, pathname, description = self.FindModuleRestricted(submodule,
                                    submodule_fullname,
                                    [app_search_path])


        module.__path__.append(pathname)
      except ImportError, e:
        pass



    module.__loader__ = self
    self.FixModule(module)
    if submodule_fullname not in self._module_dict:
      self._module_dict[submodule_fullname] = module

    if submodule_fullname == 'os':








      os_path_name = module.path.__name__
      os_path = self.FindAndLoadModule(os_path_name, os_path_name, search_path)


      self._module_dict['os.path'] = os_path
      module.__dict__['path'] = os_path

    return module

  @Trace
  def GetParentPackage(self, fullname):
    """Retrieves the parent package of a fully qualified module name.

    Args:
      fullname: Full name of the module whose parent should be retrieved (e.g.,
        foo.bar).

    Returns:
      Module instance for the parent or None if there is no parent module.

    Raise:
      ImportError exception if the module's parent could not be found.
    """
    all_modules = fullname.split('.')
    parent_module_fullname = '.'.join(all_modules[:-1])
    if parent_module_fullname:

      if self.find_module(fullname) is None:
        raise ImportError('Could not find module %s' % fullname)

      return self._module_dict[parent_module_fullname]
    return None

  @Trace
  def GetParentSearchPath(self, fullname):
    """Determines the search path of a module's parent package.

    Args:
      fullname: Full name of the module to look up (e.g., foo.bar).

    Returns:
      Tuple (submodule, search_path) where:
        submodule: The last portion of the module name from fullname (e.g.,
          if fullname is foo.bar, then this is bar).
        search_path: List of paths that belong to the parent package's search
          path or None if there is no parent package.

    Raises:
      ImportError exception if the module or its parent could not be found.
    """
    submodule = GetSubmoduleName(fullname)
    parent_package = self.GetParentPackage(fullname)
    search_path = None
    if parent_package is not None and hasattr(parent_package, '__path__'):
      search_path = parent_package.__path__
    return submodule, search_path

  @Trace
  def GetModuleInfo(self, fullname):
    """Determines the path on disk and the search path of a module or package.

    Args:
      fullname: Full name of the module to look up (e.g., foo.bar).

    Returns:
      Tuple (pathname, search_path, submodule) where:
        pathname: String containing the full path of the module on disk,
          or None if the module wasn't loaded from disk (e.g. from a zipfile).
        search_path: List of paths that belong to the found package's search
          path or None if found module is not a package.
        submodule: The relative name of the submodule that's being imported.
    """
    submodule, search_path = self.GetParentSearchPath(fullname)
    source_file, pathname, description = self.FindModuleRestricted(submodule, fullname, search_path)
    suffix, mode, file_type = description
    module_search_path = None
    if file_type == self._imp.PKG_DIRECTORY:
      module_search_path = [pathname]
      pathname = os.path.join(pathname, '__init__%spy' % os.extsep)
    return pathname, module_search_path, submodule

  @Trace
  def load_module(self, fullname):
    """See PEP 302."""
    all_modules = fullname.split('.')
    submodule = all_modules[-1]
    parent_module_fullname = '.'.join(all_modules[:-1])
    search_path = None
    if parent_module_fullname and parent_module_fullname in self._module_dict:
      parent_module = self._module_dict[parent_module_fullname]
      if hasattr(parent_module, '__path__'):
        search_path = parent_module.__path__

    return self.FindAndLoadModule(submodule, fullname, search_path)

  @Trace
  def is_package(self, fullname):
    """See PEP 302 extensions."""
    submodule, search_path = self.GetParentSearchPath(fullname)
    source_file, pathname, description = self.FindModuleRestricted(submodule, fullname, search_path)
    suffix, mode, file_type = description
    if file_type == self._imp.PKG_DIRECTORY:
      return True
    return False

  @Trace
  def get_source(self, fullname):
    """See PEP 302 extensions."""
    full_path, search_path, submodule = self.GetModuleInfo(fullname)
    if full_path is None:
      return None
    source_file = open(full_path)
    try:
      return source_file.read()
    finally:
      source_file.close()

  @Trace
  def get_code(self, fullname):
    """See PEP 302 extensions."""
    full_path, search_path, submodule = self.GetModuleInfo(fullname)
    if full_path is None:
      return None
    source_file = open(full_path)
    try:
      source_code = source_file.read()
    finally:
      source_file.close()




    source_code = source_code.replace('\r\n', '\n')
    if not source_code.endswith('\n'):
      source_code += '\n'




    encoding = DEFAULT_ENCODING
    for line in source_code.split('\n', 2)[:2]:
      matches = CODING_COOKIE_RE.findall(line)
      if matches:
        encoding = matches[0].lower()


    source_code.decode(encoding)

    return compile(source_code, full_path, 'exec')
