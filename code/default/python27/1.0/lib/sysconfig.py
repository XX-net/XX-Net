"""Provide access to Python's configuration information.

"""
import sys
import os
from os.path import pardir, realpath

_INSTALL_SCHEMES = {
    'posix_prefix': {
        'stdlib': '{base}/lib/python{py_version_short}',
        'platstdlib': '{platbase}/lib/python{py_version_short}',
        'purelib': '{base}/lib/python{py_version_short}/site-packages',
        'platlib': '{platbase}/lib/python{py_version_short}/site-packages',
        'include': '{base}/include/python{py_version_short}',
        'platinclude': '{platbase}/include/python{py_version_short}',
        'scripts': '{base}/bin',
        'data': '{base}',
        },
    'posix_home': {
        'stdlib': '{base}/lib/python',
        'platstdlib': '{base}/lib/python',
        'purelib': '{base}/lib/python',
        'platlib': '{base}/lib/python',
        'include': '{base}/include/python',
        'platinclude': '{base}/include/python',
        'scripts': '{base}/bin',
        'data'   : '{base}',
        },
    'nt': {
        'stdlib': '{base}/Lib',
        'platstdlib': '{base}/Lib',
        'purelib': '{base}/Lib/site-packages',
        'platlib': '{base}/Lib/site-packages',
        'include': '{base}/Include',
        'platinclude': '{base}/Include',
        'scripts': '{base}/Scripts',
        'data'   : '{base}',
        },
    'os2': {
        'stdlib': '{base}/Lib',
        'platstdlib': '{base}/Lib',
        'purelib': '{base}/Lib/site-packages',
        'platlib': '{base}/Lib/site-packages',
        'include': '{base}/Include',
        'platinclude': '{base}/Include',
        'scripts': '{base}/Scripts',
        'data'   : '{base}',
        },
    'os2_home': {
        'stdlib': '{userbase}/lib/python{py_version_short}',
        'platstdlib': '{userbase}/lib/python{py_version_short}',
        'purelib': '{userbase}/lib/python{py_version_short}/site-packages',
        'platlib': '{userbase}/lib/python{py_version_short}/site-packages',
        'include': '{userbase}/include/python{py_version_short}',
        'scripts': '{userbase}/bin',
        'data'   : '{userbase}',
        },
    'nt_user': {
        'stdlib': '{userbase}/Python{py_version_nodot}',
        'platstdlib': '{userbase}/Python{py_version_nodot}',
        'purelib': '{userbase}/Python{py_version_nodot}/site-packages',
        'platlib': '{userbase}/Python{py_version_nodot}/site-packages',
        'include': '{userbase}/Python{py_version_nodot}/Include',
        'scripts': '{userbase}/Scripts',
        'data'   : '{userbase}',
        },
    'posix_user': {
        'stdlib': '{userbase}/lib/python{py_version_short}',
        'platstdlib': '{userbase}/lib/python{py_version_short}',
        'purelib': '{userbase}/lib/python{py_version_short}/site-packages',
        'platlib': '{userbase}/lib/python{py_version_short}/site-packages',
        'include': '{userbase}/include/python{py_version_short}',
        'scripts': '{userbase}/bin',
        'data'   : '{userbase}',
        },
    'osx_framework_user': {
        'stdlib': '{userbase}/lib/python',
        'platstdlib': '{userbase}/lib/python',
        'purelib': '{userbase}/lib/python/site-packages',
        'platlib': '{userbase}/lib/python/site-packages',
        'include': '{userbase}/include',
        'scripts': '{userbase}/bin',
        'data'   : '{userbase}',
        },
    }

_SCHEME_KEYS = ('stdlib', 'platstdlib', 'purelib', 'platlib', 'include',
                'scripts', 'data')
_PY_VERSION = sys.version.split()[0]
_PY_VERSION_SHORT = sys.version[:3]
_PY_VERSION_SHORT_NO_DOT = _PY_VERSION[0] + _PY_VERSION[2]
_PREFIX = os.path.normpath(sys.prefix)
_EXEC_PREFIX = os.path.normpath(sys.exec_prefix)
_CONFIG_VARS = None
_USER_BASE = None

def _safe_realpath(path):
    try:
        return realpath(path)
    except OSError:
        return path

if sys.executable:
    _PROJECT_BASE = os.path.dirname(_safe_realpath(sys.executable))
else:
    # sys.executable can be empty if argv[0] has been changed and Python is
    # unable to retrieve the real program name
    _PROJECT_BASE = _safe_realpath(os.getcwd())

if os.name == "nt" and "pcbuild" in _PROJECT_BASE[-8:].lower():
    _PROJECT_BASE = _safe_realpath(os.path.join(_PROJECT_BASE, pardir))
# PC/VS7.1
if os.name == "nt" and "\\pc\\v" in _PROJECT_BASE[-10:].lower():
    _PROJECT_BASE = _safe_realpath(os.path.join(_PROJECT_BASE, pardir, pardir))
# PC/AMD64
if os.name == "nt" and "\\pcbuild\\amd64" in _PROJECT_BASE[-14:].lower():
    _PROJECT_BASE = _safe_realpath(os.path.join(_PROJECT_BASE, pardir, pardir))

# set for cross builds
if "_PYTHON_PROJECT_BASE" in os.environ:
    # the build directory for posix builds
    _PROJECT_BASE = os.path.normpath(os.path.abspath("."))
def is_python_build():
    for fn in ("Setup.dist", "Setup.local"):
        if os.path.isfile(os.path.join(_PROJECT_BASE, "Modules", fn)):
            return True
    return False

_PYTHON_BUILD = is_python_build()

if _PYTHON_BUILD:
    for scheme in ('posix_prefix', 'posix_home'):
        _INSTALL_SCHEMES[scheme]['include'] = '{projectbase}/Include'
        _INSTALL_SCHEMES[scheme]['platinclude'] = '{srcdir}'

def _subst_vars(s, local_vars):
    try:
        return s.format(**local_vars)
    except KeyError:
        try:
            return s.format(**os.environ)
        except KeyError, var:
            raise AttributeError('{%s}' % var)

def _extend_dict(target_dict, other_dict):
    target_keys = target_dict.keys()
    for key, value in other_dict.items():
        if key in target_keys:
            continue
        target_dict[key] = value

def _expand_vars(scheme, vars):
    res = {}
    if vars is None:
        vars = {}
    _extend_dict(vars, get_config_vars())

    for key, value in _INSTALL_SCHEMES[scheme].items():
        if os.name in ('posix', 'nt'):
            value = os.path.expanduser(value)
        res[key] = os.path.normpath(_subst_vars(value, vars))
    return res

def _get_default_scheme():
    if os.name == 'posix':
        # the default scheme for posix is posix_prefix
        return 'posix_prefix'
    return os.name

def _getuserbase():
    env_base = os.environ.get("PYTHONUSERBASE", None)
    def joinuser(*args):
        return os.path.expanduser(os.path.join(*args))

    # what about 'os2emx', 'riscos' ?
    if os.name == "nt":
        base = os.environ.get("APPDATA") or "~"
        return env_base if env_base else joinuser(base, "Python")

    if sys.platform == "darwin":
        framework = get_config_var("PYTHONFRAMEWORK")
        if framework:
            return env_base if env_base else \
                               joinuser("~", "Library", framework, "%d.%d"
                                            % (sys.version_info[:2]))

    return env_base if env_base else joinuser("~", ".local")


def _parse_makefile(filename, vars=None):
    """Parse a Makefile-style file.

    A dictionary containing name/value pairs is returned.  If an
    optional dictionary is passed in as the second argument, it is
    used instead of a new dictionary.
    """
    import re
    # Regexes needed for parsing Makefile (and similar syntaxes,
    # like old-style Setup files).
    _variable_rx = re.compile("([a-zA-Z][a-zA-Z0-9_]+)\s*=\s*(.*)")
    _findvar1_rx = re.compile(r"\$\(([A-Za-z][A-Za-z0-9_]*)\)")
    _findvar2_rx = re.compile(r"\${([A-Za-z][A-Za-z0-9_]*)}")

    if vars is None:
        vars = {}
    done = {}
    notdone = {}

    with open(filename) as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('#') or line.strip() == '':
            continue
        m = _variable_rx.match(line)
        if m:
            n, v = m.group(1, 2)
            v = v.strip()
            # `$$' is a literal `$' in make
            tmpv = v.replace('$$', '')

            if "$" in tmpv:
                notdone[n] = v
            else:
                try:
                    v = int(v)
                except ValueError:
                    # insert literal `$'
                    done[n] = v.replace('$$', '$')
                else:
                    done[n] = v

    # do variable interpolation here
    while notdone:
        for name in notdone.keys():
            value = notdone[name]
            m = _findvar1_rx.search(value) or _findvar2_rx.search(value)
            if m:
                n = m.group(1)
                found = True
                if n in done:
                    item = str(done[n])
                elif n in notdone:
                    # get it on a subsequent round
                    found = False
                elif n in os.environ:
                    # do it like make: fall back to environment
                    item = os.environ[n]
                else:
                    done[n] = item = ""
                if found:
                    after = value[m.end():]
                    value = value[:m.start()] + item + after
                    if "$" in after:
                        notdone[name] = value
                    else:
                        try: value = int(value)
                        except ValueError:
                            done[name] = value.strip()
                        else:
                            done[name] = value
                        del notdone[name]
            else:
                # bogus variable reference; just drop it since we can't deal
                del notdone[name]
    # strip spurious spaces
    for k, v in done.items():
        if isinstance(v, str):
            done[k] = v.strip()

    # save the results in the global dictionary
    vars.update(done)
    return vars


def get_makefile_filename():
    """Return the path of the Makefile."""
    if _PYTHON_BUILD:
        return os.path.join(_PROJECT_BASE, "Makefile")
    return os.path.join(get_path('platstdlib'), "config", "Makefile")

# Issue #22199: retain undocumented private name for compatibility
_get_makefile_filename = get_makefile_filename

def _generate_posix_vars():
    """Generate the Python module containing build-time variables."""
    import pprint
    vars = {}
    # load the installed Makefile:
    makefile = get_makefile_filename()
    try:
        _parse_makefile(makefile, vars)
    except IOError, e:
        msg = "invalid Python installation: unable to open %s" % makefile
        if hasattr(e, "strerror"):
            msg = msg + " (%s)" % e.strerror
        raise IOError(msg)

    # load the installed pyconfig.h:
    config_h = get_config_h_filename()
    try:
        with open(config_h) as f:
            parse_config_h(f, vars)
    except IOError, e:
        msg = "invalid Python installation: unable to open %s" % config_h
        if hasattr(e, "strerror"):
            msg = msg + " (%s)" % e.strerror
        raise IOError(msg)

    # On AIX, there are wrong paths to the linker scripts in the Makefile
    # -- these paths are relative to the Python source, but when installed
    # the scripts are in another directory.
    if _PYTHON_BUILD:
        vars['LDSHARED'] = vars['BLDSHARED']

    # There's a chicken-and-egg situation on OS X with regards to the
    # _sysconfigdata module after the changes introduced by #15298:
    # get_config_vars() is called by get_platform() as part of the
    # `make pybuilddir.txt` target -- which is a precursor to the
    # _sysconfigdata.py module being constructed.  Unfortunately,
    # get_config_vars() eventually calls _init_posix(), which attempts
    # to import _sysconfigdata, which we won't have built yet.  In order
    # for _init_posix() to work, if we're on Darwin, just mock up the
    # _sysconfigdata module manually and populate it with the build vars.
    # This is more than sufficient for ensuring the subsequent call to
    # get_platform() succeeds.
    name = '_sysconfigdata'
    if 'darwin' in sys.platform:
        import imp
        module = imp.new_module(name)
        module.build_time_vars = vars
        sys.modules[name] = module

    pybuilddir = 'build/lib.%s-%s' % (get_platform(), sys.version[:3])
    if hasattr(sys, "gettotalrefcount"):
        pybuilddir += '-pydebug'
    try:
        os.makedirs(pybuilddir)
    except OSError:
        pass
    destfile = os.path.join(pybuilddir, name + '.py')

    with open(destfile, 'wb') as f:
        f.write('# system configuration generated and used by'
                ' the sysconfig module\n')
        f.write('build_time_vars = ')
        pprint.pprint(vars, stream=f)

    # Create file used for sys.path fixup -- see Modules/getpath.c
    with open('pybuilddir.txt', 'w') as f:
        f.write(pybuilddir)

def _init_posix(vars):
    """Initialize the module as appropriate for POSIX systems."""
    # _sysconfigdata is generated at build time, see _generate_posix_vars()
    from _sysconfigdata import build_time_vars
    vars.update(build_time_vars)

def _init_non_posix(vars):
    """Initialize the module as appropriate for NT"""
    # set basic install directories
    vars['LIBDEST'] = get_path('stdlib')
    vars['BINLIBDEST'] = get_path('platstdlib')
    vars['INCLUDEPY'] = get_path('include')
    vars['SO'] = '.pyd'
    vars['EXE'] = '.exe'
    vars['VERSION'] = _PY_VERSION_SHORT_NO_DOT
    vars['BINDIR'] = os.path.dirname(_safe_realpath(sys.executable))

#
# public APIs
#


def parse_config_h(fp, vars=None):
    """Parse a config.h-style file.

    A dictionary containing name/value pairs is returned.  If an
    optional dictionary is passed in as the second argument, it is
    used instead of a new dictionary.
    """
    import re
    if vars is None:
        vars = {}
    define_rx = re.compile("#define ([A-Z][A-Za-z0-9_]+) (.*)\n")
    undef_rx = re.compile("/[*] #undef ([A-Z][A-Za-z0-9_]+) [*]/\n")

    while True:
        line = fp.readline()
        if not line:
            break
        m = define_rx.match(line)
        if m:
            n, v = m.group(1, 2)
            try: v = int(v)
            except ValueError: pass
            vars[n] = v
        else:
            m = undef_rx.match(line)
            if m:
                vars[m.group(1)] = 0
    return vars

def get_config_h_filename():
    """Returns the path of pyconfig.h."""
    if _PYTHON_BUILD:
        if os.name == "nt":
            inc_dir = os.path.join(_PROJECT_BASE, "PC")
        else:
            inc_dir = _PROJECT_BASE
    else:
        inc_dir = get_path('platinclude')
    return os.path.join(inc_dir, 'pyconfig.h')

def get_scheme_names():
    """Returns a tuple containing the schemes names."""
    schemes = _INSTALL_SCHEMES.keys()
    schemes.sort()
    return tuple(schemes)

def get_path_names():
    """Returns a tuple containing the paths names."""
    return _SCHEME_KEYS

def get_paths(scheme=_get_default_scheme(), vars=None, expand=True):
    """Returns a mapping containing an install scheme.

    ``scheme`` is the install scheme name. If not provided, it will
    return the default scheme for the current platform.
    """
    if expand:
        return _expand_vars(scheme, vars)
    else:
        return _INSTALL_SCHEMES[scheme]

def get_path(name, scheme=_get_default_scheme(), vars=None, expand=True):
    """Returns a path corresponding to the scheme.

    ``scheme`` is the install scheme name.
    """
    return get_paths(scheme, vars, expand)[name]

def get_config_vars(*args):
    """With no arguments, return a dictionary of all configuration
    variables relevant for the current platform.

    On Unix, this means every variable defined in Python's installed Makefile;
    On Windows and Mac OS it's a much smaller set.

    With arguments, return a list of values that result from looking up
    each argument in the configuration variable dictionary.
    """
    import re
    global _CONFIG_VARS
    if _CONFIG_VARS is None:
        _CONFIG_VARS = {}
        # Normalized versions of prefix and exec_prefix are handy to have;
        # in fact, these are the standard versions used most places in the
        # Distutils.
        _CONFIG_VARS['prefix'] = _PREFIX
        _CONFIG_VARS['exec_prefix'] = _EXEC_PREFIX
        _CONFIG_VARS['py_version'] = _PY_VERSION
        _CONFIG_VARS['py_version_short'] = _PY_VERSION_SHORT
        _CONFIG_VARS['py_version_nodot'] = _PY_VERSION[0] + _PY_VERSION[2]
        _CONFIG_VARS['base'] = _PREFIX
        _CONFIG_VARS['platbase'] = _EXEC_PREFIX
        _CONFIG_VARS['projectbase'] = _PROJECT_BASE

        if os.name in ('nt', 'os2'):
            _init_non_posix(_CONFIG_VARS)
        if os.name == 'posix':
            _init_posix(_CONFIG_VARS)

        # Setting 'userbase' is done below the call to the
        # init function to enable using 'get_config_var' in
        # the init-function.
        _CONFIG_VARS['userbase'] = _getuserbase()

        if 'srcdir' not in _CONFIG_VARS:
            _CONFIG_VARS['srcdir'] = _PROJECT_BASE

        # Convert srcdir into an absolute path if it appears necessary.
        # Normally it is relative to the build directory.  However, during
        # testing, for example, we might be running a non-installed python
        # from a different directory.
        if _PYTHON_BUILD and os.name == "posix":
            base = _PROJECT_BASE
            try:
                cwd = os.getcwd()
            except OSError:
                cwd = None
            if (not os.path.isabs(_CONFIG_VARS['srcdir']) and
                base != cwd):
                # srcdir is relative and we are not in the same directory
                # as the executable. Assume executable is in the build
                # directory and make srcdir absolute.
                srcdir = os.path.join(base, _CONFIG_VARS['srcdir'])
                _CONFIG_VARS['srcdir'] = os.path.normpath(srcdir)

        # OS X platforms require special customization to handle
        # multi-architecture, multi-os-version installers
        if sys.platform == 'darwin':
            import _osx_support
            _osx_support.customize_config_vars(_CONFIG_VARS)

    if args:
        vals = []
        for name in args:
            vals.append(_CONFIG_VARS.get(name))
        return vals
    else:
        return _CONFIG_VARS

def get_config_var(name):
    """Return the value of a single variable using the dictionary returned by
    'get_config_vars()'.

    Equivalent to get_config_vars().get(name)
    """
    return get_config_vars().get(name)

def get_platform():
    """Return a string that identifies the current platform.

    This is used mainly to distinguish platform-specific build directories and
    platform-specific built distributions.  Typically includes the OS name
    and version and the architecture (as supplied by 'os.uname()'),
    although the exact information included depends on the OS; eg. for IRIX
    the architecture isn't particularly important (IRIX only runs on SGI
    hardware), but for Linux the kernel version isn't particularly
    important.

    Examples of returned values:
       linux-i586
       linux-alpha (?)
       solaris-2.6-sun4u
       irix-5.3
       irix64-6.2

    Windows will return one of:
       win-amd64 (64bit Windows on AMD64 (aka x86_64, Intel64, EM64T, etc)
       win-ia64 (64bit Windows on Itanium)
       win32 (all others - specifically, sys.platform is returned)

    For other non-POSIX platforms, currently just returns 'sys.platform'.
    """
    import re
    if os.name == 'nt':
        # sniff sys.version for architecture.
        prefix = " bit ("
        i = sys.version.find(prefix)
        if i == -1:
            return sys.platform
        j = sys.version.find(")", i)
        look = sys.version[i+len(prefix):j].lower()
        if look == 'amd64':
            return 'win-amd64'
        if look == 'itanium':
            return 'win-ia64'
        return sys.platform

    # Set for cross builds explicitly
    if "_PYTHON_HOST_PLATFORM" in os.environ:
        return os.environ["_PYTHON_HOST_PLATFORM"]

    if os.name != "posix" or not hasattr(os, 'uname'):
        # XXX what about the architecture? NT is Intel or Alpha,
        # Mac OS is M68k or PPC, etc.
        return sys.platform

    # Try to distinguish various flavours of Unix
    osname, host, release, version, machine = os.uname()

    # Convert the OS name to lowercase, remove '/' characters
    # (to accommodate BSD/OS), and translate spaces (for "Power Macintosh")
    osname = osname.lower().replace('/', '')
    machine = machine.replace(' ', '_')
    machine = machine.replace('/', '-')

    if osname[:5] == "linux":
        # At least on Linux/Intel, 'machine' is the processor --
        # i386, etc.
        # XXX what about Alpha, SPARC, etc?
        return  "%s-%s" % (osname, machine)
    elif osname[:5] == "sunos":
        if release[0] >= "5":           # SunOS 5 == Solaris 2
            osname = "solaris"
            release = "%d.%s" % (int(release[0]) - 3, release[2:])
            # We can't use "platform.architecture()[0]" because a
            # bootstrap problem. We use a dict to get an error
            # if some suspicious happens.
            bitness = {2147483647:"32bit", 9223372036854775807:"64bit"}
            machine += ".%s" % bitness[sys.maxint]
        # fall through to standard osname-release-machine representation
    elif osname[:4] == "irix":              # could be "irix64"!
        return "%s-%s" % (osname, release)
    elif osname[:3] == "aix":
        return "%s-%s.%s" % (osname, version, release)
    elif osname[:6] == "cygwin":
        osname = "cygwin"
        rel_re = re.compile (r'[\d.]+')
        m = rel_re.match(release)
        if m:
            release = m.group()
    elif osname[:6] == "darwin":
        import _osx_support
        osname, release, machine = _osx_support.get_platform_osx(
                                            get_config_vars(),
                                            osname, release, machine)

    return "%s-%s-%s" % (osname, release, machine)


def get_python_version():
    return _PY_VERSION_SHORT


def _print_dict(title, data):
    for index, (key, value) in enumerate(sorted(data.items())):
        if index == 0:
            print '%s: ' % (title)
        print '\t%s = "%s"' % (key, value)


def _main():
    """Display all information sysconfig detains."""
    if '--generate-posix-vars' in sys.argv:
        _generate_posix_vars()
        return
    print 'Platform: "%s"' % get_platform()
    print 'Python version: "%s"' % get_python_version()
    print 'Current installation scheme: "%s"' % _get_default_scheme()
    print
    _print_dict('Paths', get_paths())
    print
    _print_dict('Variables', get_config_vars())


if __name__ == '__main__':
    _main()
