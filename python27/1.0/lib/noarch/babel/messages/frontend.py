# -*- coding: utf-8 -*-
"""
    babel.messages.frontend
    ~~~~~~~~~~~~~~~~~~~~~~~

    Frontends for the message extraction functionality.

    :copyright: (c) 2013 by the Babel Team.
    :license: BSD, see LICENSE for more details.
"""

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser
from datetime import datetime
from distutils import log
from distutils.cmd import Command
from distutils.errors import DistutilsOptionError, DistutilsSetupError
from locale import getpreferredencoding
import logging
from optparse import OptionParser
import os
import re
import shutil
import sys
import tempfile

from babel import __version__ as VERSION
from babel import Locale, localedata
from babel.core import UnknownLocaleError
from babel.messages.catalog import Catalog
from babel.messages.extract import extract_from_dir, DEFAULT_KEYWORDS, \
                                   DEFAULT_MAPPING
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po
from babel.util import odict, LOCALTZ
from babel._compat import string_types, BytesIO, PY2


class compile_catalog(Command):
    """Catalog compilation command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.frontend import compile_catalog

        setup(
            ...
            cmdclass = {'compile_catalog': compile_catalog}
        )

    .. versionadded:: 0.9
    """

    description = 'compile message catalogs to binary MO files'
    user_options = [
        ('domain=', 'D',
         "domain of PO file (default 'messages')"),
        ('directory=', 'd',
         'path to base directory containing the catalogs'),
        ('input-file=', 'i',
         'name of the input file'),
        ('output-file=', 'o',
         "name of the output file (default "
         "'<output_dir>/<locale>/LC_MESSAGES/<domain>.mo')"),
        ('locale=', 'l',
         'locale of the catalog to compile'),
        ('use-fuzzy', 'f',
         'also include fuzzy translations'),
        ('statistics', None,
         'print statistics about translations')
    ]
    boolean_options = ['use-fuzzy', 'statistics']

    def initialize_options(self):
        self.domain = 'messages'
        self.directory = None
        self.input_file = None
        self.output_file = None
        self.locale = None
        self.use_fuzzy = False
        self.statistics = False

    def finalize_options(self):
        if not self.input_file and not self.directory:
            raise DistutilsOptionError('you must specify either the input file '
                                       'or the base directory')
        if not self.output_file and not self.directory:
            raise DistutilsOptionError('you must specify either the output file '
                                       'or the base directory')

    def run(self):
        po_files = []
        mo_files = []

        if not self.input_file:
            if self.locale:
                po_files.append((self.locale,
                                 os.path.join(self.directory, self.locale,
                                              'LC_MESSAGES',
                                              self.domain + '.po')))
                mo_files.append(os.path.join(self.directory, self.locale,
                                             'LC_MESSAGES',
                                             self.domain + '.mo'))
            else:
                for locale in os.listdir(self.directory):
                    po_file = os.path.join(self.directory, locale,
                                           'LC_MESSAGES', self.domain + '.po')
                    if os.path.exists(po_file):
                        po_files.append((locale, po_file))
                        mo_files.append(os.path.join(self.directory, locale,
                                                     'LC_MESSAGES',
                                                     self.domain + '.mo'))
        else:
            po_files.append((self.locale, self.input_file))
            if self.output_file:
                mo_files.append(self.output_file)
            else:
                mo_files.append(os.path.join(self.directory, self.locale,
                                             'LC_MESSAGES',
                                             self.domain + '.mo'))

        if not po_files:
            raise DistutilsOptionError('no message catalogs found')

        for idx, (locale, po_file) in enumerate(po_files):
            mo_file = mo_files[idx]
            infile = open(po_file, 'rb')
            try:
                catalog = read_po(infile, locale)
            finally:
                infile.close()

            if self.statistics:
                translated = 0
                for message in list(catalog)[1:]:
                    if message.string:
                        translated +=1
                percentage = 0
                if len(catalog):
                    percentage = translated * 100 // len(catalog)
                log.info('%d of %d messages (%d%%) translated in %r',
                         translated, len(catalog), percentage, po_file)

            if catalog.fuzzy and not self.use_fuzzy:
                log.warn('catalog %r is marked as fuzzy, skipping', po_file)
                continue

            for message, errors in catalog.check():
                for error in errors:
                    log.error('error: %s:%d: %s', po_file, message.lineno,
                              error)

            log.info('compiling catalog %r to %r', po_file, mo_file)

            outfile = open(mo_file, 'wb')
            try:
                write_mo(outfile, catalog, use_fuzzy=self.use_fuzzy)
            finally:
                outfile.close()


class extract_messages(Command):
    """Message extraction command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.frontend import extract_messages

        setup(
            ...
            cmdclass = {'extract_messages': extract_messages}
        )
    """

    description = 'extract localizable strings from the project code'
    user_options = [
        ('charset=', None,
         'charset to use in the output file'),
        ('keywords=', 'k',
         'space-separated list of keywords to look for in addition to the '
         'defaults'),
        ('no-default-keywords', None,
         'do not include the default keywords'),
        ('mapping-file=', 'F',
         'path to the mapping configuration file'),
        ('no-location', None,
         'do not include location comments with filename and line number'),
        ('omit-header', None,
         'do not include msgid "" entry in header'),
        ('output-file=', 'o',
         'name of the output file'),
        ('width=', 'w',
         'set output line width (default 76)'),
        ('no-wrap', None,
         'do not break long message lines, longer than the output line width, '
         'into several lines'),
        ('sort-output', None,
         'generate sorted output (default False)'),
        ('sort-by-file', None,
         'sort output by file location (default False)'),
        ('msgid-bugs-address=', None,
         'set report address for msgid'),
        ('copyright-holder=', None,
         'set copyright holder in output'),
        ('add-comments=', 'c',
         'place comment block with TAG (or those preceding keyword lines) in '
         'output file. Separate multiple TAGs with commas(,)'),
        ('strip-comments', None,
         'strip the comment TAGs from the comments.'),
        ('input-dirs=', None,
         'directories that should be scanned for messages. Separate multiple '
         'directories with commas(,)'),
    ]
    boolean_options = [
        'no-default-keywords', 'no-location', 'omit-header', 'no-wrap',
        'sort-output', 'sort-by-file', 'strip-comments'
    ]

    def initialize_options(self):
        self.charset = 'utf-8'
        self.keywords = ''
        self._keywords = DEFAULT_KEYWORDS.copy()
        self.no_default_keywords = False
        self.mapping_file = None
        self.no_location = False
        self.omit_header = False
        self.output_file = None
        self.input_dirs = None
        self.width = None
        self.no_wrap = False
        self.sort_output = False
        self.sort_by_file = False
        self.msgid_bugs_address = None
        self.copyright_holder = None
        self.add_comments = None
        self._add_comments = []
        self.strip_comments = False

    def finalize_options(self):
        if self.no_default_keywords and not self.keywords:
            raise DistutilsOptionError('you must specify new keywords if you '
                                       'disable the default ones')
        if self.no_default_keywords:
            self._keywords = {}
        if self.keywords:
            self._keywords.update(parse_keywords(self.keywords.split()))

        if not self.output_file:
            raise DistutilsOptionError('no output file specified')
        if self.no_wrap and self.width:
            raise DistutilsOptionError("'--no-wrap' and '--width' are mutually "
                                       "exclusive")
        if not self.no_wrap and not self.width:
            self.width = 76
        elif self.width is not None:
            self.width = int(self.width)

        if self.sort_output and self.sort_by_file:
            raise DistutilsOptionError("'--sort-output' and '--sort-by-file' "
                                       "are mutually exclusive")

        if self.input_dirs:
            self.input_dirs = re.split(',\s*', self.input_dirs)
        else:
            self.input_dirs = dict.fromkeys([k.split('.',1)[0]
                for k in self.distribution.packages
            ]).keys()

        if self.add_comments:
            self._add_comments = self.add_comments.split(',')

    def run(self):
        mappings = self._get_mappings()
        outfile = open(self.output_file, 'wb')
        try:
            catalog = Catalog(project=self.distribution.get_name(),
                              version=self.distribution.get_version(),
                              msgid_bugs_address=self.msgid_bugs_address,
                              copyright_holder=self.copyright_holder,
                              charset=self.charset)

            for dirname, (method_map, options_map) in mappings.items():
                def callback(filename, method, options):
                    if method == 'ignore':
                        return
                    filepath = os.path.normpath(os.path.join(dirname, filename))
                    optstr = ''
                    if options:
                        optstr = ' (%s)' % ', '.join(['%s="%s"' % (k, v) for
                                                      k, v in options.items()])
                    log.info('extracting messages from %s%s', filepath, optstr)

                extracted = extract_from_dir(dirname, method_map, options_map,
                                             keywords=self._keywords,
                                             comment_tags=self._add_comments,
                                             callback=callback,
                                             strip_comment_tags=
                                                self.strip_comments)
                for filename, lineno, message, comments, context in extracted:
                    filepath = os.path.normpath(os.path.join(dirname, filename))
                    catalog.add(message, None, [(filepath, lineno)],
                                auto_comments=comments, context=context)

            log.info('writing PO template file to %s' % self.output_file)
            write_po(outfile, catalog, width=self.width,
                     no_location=self.no_location,
                     omit_header=self.omit_header,
                     sort_output=self.sort_output,
                     sort_by_file=self.sort_by_file)
        finally:
            outfile.close()

    def _get_mappings(self):
        mappings = {}

        if self.mapping_file:
            fileobj = open(self.mapping_file, 'U')
            try:
                method_map, options_map = parse_mapping(fileobj)
                for dirname in self.input_dirs:
                    mappings[dirname] = method_map, options_map
            finally:
                fileobj.close()

        elif getattr(self.distribution, 'message_extractors', None):
            message_extractors = self.distribution.message_extractors
            for dirname, mapping in message_extractors.items():
                if isinstance(mapping, string_types):
                    method_map, options_map = parse_mapping(BytesIO(mapping))
                else:
                    method_map, options_map = [], {}
                    for pattern, method, options in mapping:
                        method_map.append((pattern, method))
                        options_map[pattern] = options or {}
                mappings[dirname] = method_map, options_map

        else:
            for dirname in self.input_dirs:
                mappings[dirname] = DEFAULT_MAPPING, {}

        return mappings


def check_message_extractors(dist, name, value):
    """Validate the ``message_extractors`` keyword argument to ``setup()``.

    :param dist: the distutils/setuptools ``Distribution`` object
    :param name: the name of the keyword argument (should always be
                 "message_extractors")
    :param value: the value of the keyword argument
    :raise `DistutilsSetupError`: if the value is not valid
    """
    assert name == 'message_extractors'
    if not isinstance(value, dict):
        raise DistutilsSetupError('the value of the "message_extractors" '
                                  'parameter must be a dictionary')


class init_catalog(Command):
    """New catalog initialization command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.frontend import init_catalog

        setup(
            ...
            cmdclass = {'init_catalog': init_catalog}
        )
    """

    description = 'create a new catalog based on a POT file'
    user_options = [
        ('domain=', 'D',
         "domain of PO file (default 'messages')"),
        ('input-file=', 'i',
         'name of the input file'),
        ('output-dir=', 'd',
         'path to output directory'),
        ('output-file=', 'o',
         "name of the output file (default "
         "'<output_dir>/<locale>/LC_MESSAGES/<domain>.po')"),
        ('locale=', 'l',
         'locale for the new localized catalog'),
        ('width=', 'w',
         'set output line width (default 76)'),
        ('no-wrap', None,
         'do not break long message lines, longer than the output line width, '
         'into several lines'),
    ]
    boolean_options = ['no-wrap']

    def initialize_options(self):
        self.output_dir = None
        self.output_file = None
        self.input_file = None
        self.locale = None
        self.domain = 'messages'
        self.no_wrap = False
        self.width = None

    def finalize_options(self):
        if not self.input_file:
            raise DistutilsOptionError('you must specify the input file')

        if not self.locale:
            raise DistutilsOptionError('you must provide a locale for the '
                                       'new catalog')
        try:
            self._locale = Locale.parse(self.locale)
        except UnknownLocaleError as e:
            raise DistutilsOptionError(e)

        if not self.output_file and not self.output_dir:
            raise DistutilsOptionError('you must specify the output directory')
        if not self.output_file:
            self.output_file = os.path.join(self.output_dir, self.locale,
                                            'LC_MESSAGES', self.domain + '.po')

        if not os.path.exists(os.path.dirname(self.output_file)):
            os.makedirs(os.path.dirname(self.output_file))
        if self.no_wrap and self.width:
            raise DistutilsOptionError("'--no-wrap' and '--width' are mutually "
                                       "exclusive")
        if not self.no_wrap and not self.width:
            self.width = 76
        elif self.width is not None:
            self.width = int(self.width)

    def run(self):
        log.info('creating catalog %r based on %r', self.output_file,
                 self.input_file)

        infile = open(self.input_file, 'rb')
        try:
            # Although reading from the catalog template, read_po must be fed
            # the locale in order to correctly calculate plurals
            catalog = read_po(infile, locale=self.locale)
        finally:
            infile.close()

        catalog.locale = self._locale
        catalog.revision_date = datetime.now(LOCALTZ)
        catalog.fuzzy = False

        outfile = open(self.output_file, 'wb')
        try:
            write_po(outfile, catalog, width=self.width)
        finally:
            outfile.close()


class update_catalog(Command):
    """Catalog merging command for use in ``setup.py`` scripts.

    If correctly installed, this command is available to Setuptools-using
    setup scripts automatically. For projects using plain old ``distutils``,
    the command needs to be registered explicitly in ``setup.py``::

        from babel.messages.frontend import update_catalog

        setup(
            ...
            cmdclass = {'update_catalog': update_catalog}
        )

    .. versionadded:: 0.9
    """

    description = 'update message catalogs from a POT file'
    user_options = [
        ('domain=', 'D',
         "domain of PO file (default 'messages')"),
        ('input-file=', 'i',
         'name of the input file'),
        ('output-dir=', 'd',
         'path to base directory containing the catalogs'),
        ('output-file=', 'o',
         "name of the output file (default "
         "'<output_dir>/<locale>/LC_MESSAGES/<domain>.po')"),
        ('locale=', 'l',
         'locale of the catalog to compile'),
        ('width=', 'w',
         'set output line width (default 76)'),
        ('no-wrap', None,
         'do not break long message lines, longer than the output line width, '
         'into several lines'),
        ('ignore-obsolete=', None,
         'whether to omit obsolete messages from the output'),
        ('no-fuzzy-matching', 'N',
         'do not use fuzzy matching'),
        ('previous', None,
         'keep previous msgids of translated messages')
    ]
    boolean_options = ['ignore_obsolete', 'no_fuzzy_matching', 'previous']

    def initialize_options(self):
        self.domain = 'messages'
        self.input_file = None
        self.output_dir = None
        self.output_file = None
        self.locale = None
        self.width = None
        self.no_wrap = False
        self.ignore_obsolete = False
        self.no_fuzzy_matching = False
        self.previous = False

    def finalize_options(self):
        if not self.input_file:
            raise DistutilsOptionError('you must specify the input file')
        if not self.output_file and not self.output_dir:
            raise DistutilsOptionError('you must specify the output file or '
                                       'directory')
        if self.output_file and not self.locale:
            raise DistutilsOptionError('you must specify the locale')
        if self.no_wrap and self.width:
            raise DistutilsOptionError("'--no-wrap' and '--width' are mutually "
                                       "exclusive")
        if not self.no_wrap and not self.width:
            self.width = 76
        elif self.width is not None:
            self.width = int(self.width)
        if self.no_fuzzy_matching and self.previous:
            self.previous = False

    def run(self):
        po_files = []
        if not self.output_file:
            if self.locale:
                po_files.append((self.locale,
                                 os.path.join(self.output_dir, self.locale,
                                              'LC_MESSAGES',
                                              self.domain + '.po')))
            else:
                for locale in os.listdir(self.output_dir):
                    po_file = os.path.join(self.output_dir, locale,
                                           'LC_MESSAGES',
                                           self.domain + '.po')
                    if os.path.exists(po_file):
                        po_files.append((locale, po_file))
        else:
            po_files.append((self.locale, self.output_file))

        domain = self.domain
        if not domain:
            domain = os.path.splitext(os.path.basename(self.input_file))[0]

        infile = open(self.input_file, 'rb')
        try:
            template = read_po(infile)
        finally:
            infile.close()

        if not po_files:
            raise DistutilsOptionError('no message catalogs found')

        for locale, filename in po_files:
            log.info('updating catalog %r based on %r', filename,
                     self.input_file)
            infile = open(filename, 'rb')
            try:
                catalog = read_po(infile, locale=locale, domain=domain)
            finally:
                infile.close()

            catalog.update(template, self.no_fuzzy_matching)

            tmpname = os.path.join(os.path.dirname(filename),
                                   tempfile.gettempprefix() +
                                   os.path.basename(filename))
            tmpfile = open(tmpname, 'wb')
            try:
                try:
                    write_po(tmpfile, catalog,
                             ignore_obsolete=self.ignore_obsolete,
                             include_previous=self.previous, width=self.width)
                finally:
                    tmpfile.close()
            except:
                os.remove(tmpname)
                raise

            try:
                os.rename(tmpname, filename)
            except OSError:
                # We're probably on Windows, which doesn't support atomic
                # renames, at least not through Python
                # If the error is in fact due to a permissions problem, that
                # same error is going to be raised from one of the following
                # operations
                os.remove(filename)
                shutil.copy(tmpname, filename)
                os.remove(tmpname)


class CommandLineInterface(object):
    """Command-line interface.

    This class provides a simple command-line interface to the message
    extraction and PO file generation functionality.
    """

    usage = '%%prog %s [options] %s'
    version = '%%prog %s' % VERSION
    commands = {
        'compile': 'compile message catalogs to MO files',
        'extract': 'extract messages from source files and generate a POT file',
        'init':    'create new message catalogs from a POT file',
        'update':  'update existing message catalogs from a POT file'
    }

    def run(self, argv=sys.argv):
        """Main entry point of the command-line interface.

        :param argv: list of arguments passed on the command-line
        """
        self.parser = OptionParser(usage=self.usage % ('command', '[args]'),
                                   version=self.version)
        self.parser.disable_interspersed_args()
        self.parser.print_help = self._help
        self.parser.add_option('--list-locales', dest='list_locales',
                               action='store_true',
                               help="print all known locales and exit")
        self.parser.add_option('-v', '--verbose', action='store_const',
                               dest='loglevel', const=logging.DEBUG,
                               help='print as much as possible')
        self.parser.add_option('-q', '--quiet', action='store_const',
                               dest='loglevel', const=logging.ERROR,
                               help='print as little as possible')
        self.parser.set_defaults(list_locales=False, loglevel=logging.INFO)

        options, args = self.parser.parse_args(argv[1:])

        self._configure_logging(options.loglevel)
        if options.list_locales:
            identifiers = localedata.locale_identifiers()
            longest = max([len(identifier) for identifier in identifiers])
            identifiers.sort()
            format = u'%%-%ds %%s' % (longest + 1)
            for identifier in identifiers:
                locale = Locale.parse(identifier)
                output = format % (identifier, locale.english_name)
                print(output.encode(sys.stdout.encoding or
                                    getpreferredencoding() or
                                    'ascii', 'replace'))
            return 0

        if not args:
            self.parser.error('no valid command or option passed. '
                              'Try the -h/--help option for more information.')

        cmdname = args[0]
        if cmdname not in self.commands:
            self.parser.error('unknown command "%s"' % cmdname)

        return getattr(self, cmdname)(args[1:])

    def _configure_logging(self, loglevel):
        self.log = logging.getLogger('babel')
        self.log.setLevel(loglevel)
        # Don't add a new handler for every instance initialization (#227), this
        # would cause duplicated output when the CommandLineInterface as an
        # normal Python class.
        if self.log.handlers:
            handler = self.log.handlers[0]
        else:
            handler = logging.StreamHandler()
            self.log.addHandler(handler)
        handler.setLevel(loglevel)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

    def _help(self):
        print(self.parser.format_help())
        print("commands:")
        longest = max([len(command) for command in self.commands])
        format = "  %%-%ds %%s" % max(8, longest + 1)
        commands = sorted(self.commands.items())
        for name, description in commands:
            print(format % (name, description))

    def compile(self, argv):
        """Subcommand for compiling a message catalog to a MO file.

        :param argv: the command arguments
        :since: version 0.9
        """
        parser = OptionParser(usage=self.usage % ('compile', ''),
                              description=self.commands['compile'])
        parser.add_option('--domain', '-D', dest='domain',
                          help="domain of MO and PO files (default '%default')")
        parser.add_option('--directory', '-d', dest='directory',
                          metavar='DIR', help='base directory of catalog files')
        parser.add_option('--locale', '-l', dest='locale', metavar='LOCALE',
                          help='locale of the catalog')
        parser.add_option('--input-file', '-i', dest='input_file',
                          metavar='FILE', help='name of the input file')
        parser.add_option('--output-file', '-o', dest='output_file',
                          metavar='FILE',
                          help="name of the output file (default "
                               "'<output_dir>/<locale>/LC_MESSAGES/"
                               "<domain>.mo')")
        parser.add_option('--use-fuzzy', '-f', dest='use_fuzzy',
                          action='store_true',
                          help='also include fuzzy translations (default '
                               '%default)')
        parser.add_option('--statistics', dest='statistics',
                          action='store_true',
                          help='print statistics about translations')

        parser.set_defaults(domain='messages', use_fuzzy=False,
                            compile_all=False, statistics=False)
        options, args = parser.parse_args(argv)

        po_files = []
        mo_files = []
        if not options.input_file:
            if not options.directory:
                parser.error('you must specify either the input file or the '
                             'base directory')
            if options.locale:
                po_files.append((options.locale,
                                 os.path.join(options.directory,
                                              options.locale, 'LC_MESSAGES',
                                              options.domain + '.po')))
                mo_files.append(os.path.join(options.directory, options.locale,
                                             'LC_MESSAGES',
                                             options.domain + '.mo'))
            else:
                for locale in os.listdir(options.directory):
                    po_file = os.path.join(options.directory, locale,
                                           'LC_MESSAGES', options.domain + '.po')
                    if os.path.exists(po_file):
                        po_files.append((locale, po_file))
                        mo_files.append(os.path.join(options.directory, locale,
                                                     'LC_MESSAGES',
                                                     options.domain + '.mo'))
        else:
            po_files.append((options.locale, options.input_file))
            if options.output_file:
                mo_files.append(options.output_file)
            else:
                if not options.directory:
                    parser.error('you must specify either the output file or '
                                 'the base directory')
                mo_files.append(os.path.join(options.directory, options.locale,
                                             'LC_MESSAGES',
                                             options.domain + '.mo'))
        if not po_files:
            parser.error('no message catalogs found')

        for idx, (locale, po_file) in enumerate(po_files):
            mo_file = mo_files[idx]
            infile = open(po_file, 'rb')
            try:
                catalog = read_po(infile, locale)
            finally:
                infile.close()

            if options.statistics:
                translated = 0
                for message in list(catalog)[1:]:
                    if message.string:
                        translated +=1
                percentage = 0
                if len(catalog):
                    percentage = translated * 100 // len(catalog)
                self.log.info("%d of %d messages (%d%%) translated in %r",
                              translated, len(catalog), percentage, po_file)

            if catalog.fuzzy and not options.use_fuzzy:
                self.log.warning('catalog %r is marked as fuzzy, skipping',
                                 po_file)
                continue

            for message, errors in catalog.check():
                for error in errors:
                    self.log.error('error: %s:%d: %s', po_file, message.lineno,
                                   error)

            self.log.info('compiling catalog %r to %r', po_file, mo_file)

            outfile = open(mo_file, 'wb')
            try:
                write_mo(outfile, catalog, use_fuzzy=options.use_fuzzy)
            finally:
                outfile.close()

    def extract(self, argv):
        """Subcommand for extracting messages from source files and generating
        a POT file.

        :param argv: the command arguments
        """
        parser = OptionParser(usage=self.usage % ('extract', 'dir1 <dir2> ...'),
                              description=self.commands['extract'])
        parser.add_option('--charset', dest='charset',
                          help='charset to use in the output (default '
                               '"%default")')
        parser.add_option('-k', '--keyword', dest='keywords', action='append',
                          help='keywords to look for in addition to the '
                               'defaults. You can specify multiple -k flags on '
                               'the command line.')
        parser.add_option('--no-default-keywords', dest='no_default_keywords',
                          action='store_true',
                          help="do not include the default keywords")
        parser.add_option('--mapping', '-F', dest='mapping_file',
                          help='path to the extraction mapping file')
        parser.add_option('--no-location', dest='no_location',
                          action='store_true',
                          help='do not include location comments with filename '
                               'and line number')
        parser.add_option('--omit-header', dest='omit_header',
                          action='store_true',
                          help='do not include msgid "" entry in header')
        parser.add_option('-o', '--output', dest='output',
                          help='path to the output POT file')
        parser.add_option('-w', '--width', dest='width', type='int',
                          help="set output line width (default 76)")
        parser.add_option('--no-wrap', dest='no_wrap', action='store_true',
                          help='do not break long message lines, longer than '
                               'the output line width, into several lines')
        parser.add_option('--sort-output', dest='sort_output',
                          action='store_true',
                          help='generate sorted output (default False)')
        parser.add_option('--sort-by-file', dest='sort_by_file',
                          action='store_true',
                          help='sort output by file location (default False)')
        parser.add_option('--msgid-bugs-address', dest='msgid_bugs_address',
                          metavar='EMAIL@ADDRESS',
                          help='set report address for msgid')
        parser.add_option('--copyright-holder', dest='copyright_holder',
                          help='set copyright holder in output')
        parser.add_option('--project', dest='project',
                          help='set project name in output')
        parser.add_option('--version', dest='version',
                          help='set project version in output')
        parser.add_option('--add-comments', '-c', dest='comment_tags',
                          metavar='TAG', action='append',
                          help='place comment block with TAG (or those '
                               'preceding keyword lines) in output file. One '
                               'TAG per argument call')
        parser.add_option('--strip-comment-tags', '-s',
                          dest='strip_comment_tags', action='store_true',
                          help='Strip the comment tags from the comments.')

        parser.set_defaults(charset='utf-8', keywords=[],
                            no_default_keywords=False, no_location=False,
                            omit_header = False, width=None, no_wrap=False,
                            sort_output=False, sort_by_file=False,
                            comment_tags=[], strip_comment_tags=False)
        options, args = parser.parse_args(argv)
        if not args:
            parser.error('incorrect number of arguments')

        keywords = DEFAULT_KEYWORDS.copy()
        if options.no_default_keywords:
            if not options.keywords:
                parser.error('you must specify new keywords if you disable the '
                             'default ones')
            keywords = {}
        if options.keywords:
            keywords.update(parse_keywords(options.keywords))

        if options.mapping_file:
            fileobj = open(options.mapping_file, 'U')
            try:
                method_map, options_map = parse_mapping(fileobj)
            finally:
                fileobj.close()
        else:
            method_map = DEFAULT_MAPPING
            options_map = {}

        if options.width and options.no_wrap:
            parser.error("'--no-wrap' and '--width' are mutually exclusive.")
        elif not options.width and not options.no_wrap:
            options.width = 76

        if options.sort_output and options.sort_by_file:
            parser.error("'--sort-output' and '--sort-by-file' are mutually "
                         "exclusive")

        catalog = Catalog(project=options.project,
                          version=options.version,
                          msgid_bugs_address=options.msgid_bugs_address,
                          copyright_holder=options.copyright_holder,
                          charset=options.charset)

        for dirname in args:
            if not os.path.isdir(dirname):
                parser.error('%r is not a directory' % dirname)

            def callback(filename, method, options):
                if method == 'ignore':
                    return
                filepath = os.path.normpath(os.path.join(dirname, filename))
                optstr = ''
                if options:
                    optstr = ' (%s)' % ', '.join(['%s="%s"' % (k, v) for
                                                  k, v in options.items()])
                self.log.info('extracting messages from %s%s', filepath,
                              optstr)

            extracted = extract_from_dir(dirname, method_map, options_map,
                                         keywords, options.comment_tags,
                                         callback=callback,
                                         strip_comment_tags=
                                            options.strip_comment_tags)
            for filename, lineno, message, comments, context in extracted:
                filepath = os.path.normpath(os.path.join(dirname, filename))
                catalog.add(message, None, [(filepath, lineno)],
                            auto_comments=comments, context=context)

        catalog_charset = catalog.charset
        if options.output not in (None, '-'):
            self.log.info('writing PO template file to %s' % options.output)
            outfile = open(options.output, 'wb')
            close_output = True
        else:
            outfile = sys.stdout

            # This is a bit of a hack on Python 3.  stdout is a text stream so
            # we need to find the underlying file when we write the PO.  In
            # later versions of Babel we want the write_po function to accept
            # text or binary streams and automatically adjust the encoding.
            if not PY2 and hasattr(outfile, 'buffer'):
                catalog.charset = outfile.encoding
                outfile = outfile.buffer.raw

            close_output = False

        try:
            write_po(outfile, catalog, width=options.width,
                     no_location=options.no_location,
                     omit_header=options.omit_header,
                     sort_output=options.sort_output,
                     sort_by_file=options.sort_by_file)
        finally:
            if close_output:
                outfile.close()
            catalog.charset = catalog_charset

    def init(self, argv):
        """Subcommand for creating new message catalogs from a template.

        :param argv: the command arguments
        """
        parser = OptionParser(usage=self.usage % ('init', ''),
                              description=self.commands['init'])
        parser.add_option('--domain', '-D', dest='domain',
                          help="domain of PO file (default '%default')")
        parser.add_option('--input-file', '-i', dest='input_file',
                          metavar='FILE', help='name of the input file')
        parser.add_option('--output-dir', '-d', dest='output_dir',
                          metavar='DIR', help='path to output directory')
        parser.add_option('--output-file', '-o', dest='output_file',
                          metavar='FILE',
                          help="name of the output file (default "
                               "'<output_dir>/<locale>/LC_MESSAGES/"
                               "<domain>.po')")
        parser.add_option('--locale', '-l', dest='locale', metavar='LOCALE',
                          help='locale for the new localized catalog')
        parser.add_option('-w', '--width', dest='width', type='int',
                          help="set output line width (default 76)")
        parser.add_option('--no-wrap', dest='no_wrap', action='store_true',
                          help='do not break long message lines, longer than '
                               'the output line width, into several lines')

        parser.set_defaults(domain='messages')
        options, args = parser.parse_args(argv)

        if not options.locale:
            parser.error('you must provide a locale for the new catalog')
        try:
            locale = Locale.parse(options.locale)
        except UnknownLocaleError as e:
            parser.error(e)

        if not options.input_file:
            parser.error('you must specify the input file')

        if not options.output_file and not options.output_dir:
            parser.error('you must specify the output file or directory')

        if not options.output_file:
            options.output_file = os.path.join(options.output_dir,
                                               options.locale, 'LC_MESSAGES',
                                               options.domain + '.po')
        if not os.path.exists(os.path.dirname(options.output_file)):
            os.makedirs(os.path.dirname(options.output_file))
        if options.width and options.no_wrap:
            parser.error("'--no-wrap' and '--width' are mutually exclusive.")
        elif not options.width and not options.no_wrap:
            options.width = 76

        infile = open(options.input_file, 'r')
        try:
            # Although reading from the catalog template, read_po must be fed
            # the locale in order to correctly calculate plurals
            catalog = read_po(infile, locale=options.locale)
        finally:
            infile.close()

        catalog.locale = locale
        catalog.revision_date = datetime.now(LOCALTZ)

        self.log.info('creating catalog %r based on %r', options.output_file,
                      options.input_file)

        outfile = open(options.output_file, 'wb')
        try:
            write_po(outfile, catalog, width=options.width)
        finally:
            outfile.close()

    def update(self, argv):
        """Subcommand for updating existing message catalogs from a template.

        :param argv: the command arguments
        :since: version 0.9
        """
        parser = OptionParser(usage=self.usage % ('update', ''),
                              description=self.commands['update'])
        parser.add_option('--domain', '-D', dest='domain',
                          help="domain of PO file (default '%default')")
        parser.add_option('--input-file', '-i', dest='input_file',
                          metavar='FILE', help='name of the input file')
        parser.add_option('--output-dir', '-d', dest='output_dir',
                          metavar='DIR', help='path to output directory')
        parser.add_option('--output-file', '-o', dest='output_file',
                          metavar='FILE',
                          help="name of the output file (default "
                               "'<output_dir>/<locale>/LC_MESSAGES/"
                               "<domain>.po')")
        parser.add_option('--locale', '-l', dest='locale', metavar='LOCALE',
                          help='locale of the translations catalog')
        parser.add_option('-w', '--width', dest='width', type='int',
                          help="set output line width (default 76)")
        parser.add_option('--no-wrap', dest='no_wrap', action = 'store_true',
                          help='do not break long message lines, longer than '
                               'the output line width, into several lines')
        parser.add_option('--ignore-obsolete', dest='ignore_obsolete',
                          action='store_true',
                          help='do not include obsolete messages in the output '
                               '(default %default)')
        parser.add_option('--no-fuzzy-matching', '-N', dest='no_fuzzy_matching',
                          action='store_true',
                          help='do not use fuzzy matching (default %default)')
        parser.add_option('--previous', dest='previous', action='store_true',
                          help='keep previous msgids of translated messages '
                               '(default %default)')

        parser.set_defaults(domain='messages', ignore_obsolete=False,
                            no_fuzzy_matching=False, previous=False)
        options, args = parser.parse_args(argv)

        if not options.input_file:
            parser.error('you must specify the input file')
        if not options.output_file and not options.output_dir:
            parser.error('you must specify the output file or directory')
        if options.output_file and not options.locale:
            parser.error('you must specify the locale')
        if options.no_fuzzy_matching and options.previous:
            options.previous = False

        po_files = []
        if not options.output_file:
            if options.locale:
                po_files.append((options.locale,
                                 os.path.join(options.output_dir,
                                              options.locale, 'LC_MESSAGES',
                                              options.domain + '.po')))
            else:
                for locale in os.listdir(options.output_dir):
                    po_file = os.path.join(options.output_dir, locale,
                                           'LC_MESSAGES',
                                           options.domain + '.po')
                    if os.path.exists(po_file):
                        po_files.append((locale, po_file))
        else:
            po_files.append((options.locale, options.output_file))

        domain = options.domain
        if not domain:
            domain = os.path.splitext(os.path.basename(options.input_file))[0]

        infile = open(options.input_file, 'U')
        try:
            template = read_po(infile)
        finally:
            infile.close()

        if not po_files:
            parser.error('no message catalogs found')

        if options.width and options.no_wrap:
            parser.error("'--no-wrap' and '--width' are mutually exclusive.")
        elif not options.width and not options.no_wrap:
            options.width = 76
        for locale, filename in po_files:
            self.log.info('updating catalog %r based on %r', filename,
                          options.input_file)
            infile = open(filename, 'U')
            try:
                catalog = read_po(infile, locale=locale, domain=domain)
            finally:
                infile.close()

            catalog.update(template, options.no_fuzzy_matching)

            tmpname = os.path.join(os.path.dirname(filename),
                                   tempfile.gettempprefix() +
                                   os.path.basename(filename))
            tmpfile = open(tmpname, 'wb')
            try:
                try:
                    write_po(tmpfile, catalog,
                             ignore_obsolete=options.ignore_obsolete,
                             include_previous=options.previous,
                             width=options.width)
                finally:
                    tmpfile.close()
            except:
                os.remove(tmpname)
                raise

            try:
                os.rename(tmpname, filename)
            except OSError:
                # We're probably on Windows, which doesn't support atomic
                # renames, at least not through Python
                # If the error is in fact due to a permissions problem, that
                # same error is going to be raised from one of the following
                # operations
                os.remove(filename)
                shutil.copy(tmpname, filename)
                os.remove(tmpname)


def main():
    return CommandLineInterface().run(sys.argv)


def parse_mapping(fileobj, filename=None):
    """Parse an extraction method mapping from a file-like object.

    >>> buf = BytesIO(b'''
    ... [extractors]
    ... custom = mypackage.module:myfunc
    ...
    ... # Python source files
    ... [python: **.py]
    ...
    ... # Genshi templates
    ... [genshi: **/templates/**.html]
    ... include_attrs =
    ... [genshi: **/templates/**.txt]
    ... template_class = genshi.template:TextTemplate
    ... encoding = latin-1
    ...
    ... # Some custom extractor
    ... [custom: **/custom/*.*]
    ... ''')

    >>> method_map, options_map = parse_mapping(buf)
    >>> len(method_map)
    4

    >>> method_map[0]
    ('**.py', 'python')
    >>> options_map['**.py']
    {}
    >>> method_map[1]
    ('**/templates/**.html', 'genshi')
    >>> options_map['**/templates/**.html']['include_attrs']
    ''
    >>> method_map[2]
    ('**/templates/**.txt', 'genshi')
    >>> options_map['**/templates/**.txt']['template_class']
    'genshi.template:TextTemplate'
    >>> options_map['**/templates/**.txt']['encoding']
    'latin-1'

    >>> method_map[3]
    ('**/custom/*.*', 'mypackage.module:myfunc')
    >>> options_map['**/custom/*.*']
    {}

    :param fileobj: a readable file-like object containing the configuration
                    text to parse
    :see: `extract_from_directory`
    """
    extractors = {}
    method_map = []
    options_map = {}

    parser = RawConfigParser()
    parser._sections = odict(parser._sections) # We need ordered sections
    parser.readfp(fileobj, filename)
    for section in parser.sections():
        if section == 'extractors':
            extractors = dict(parser.items(section))
        else:
            method, pattern = [part.strip() for part in section.split(':', 1)]
            method_map.append((pattern, method))
            options_map[pattern] = dict(parser.items(section))

    if extractors:
        for idx, (pattern, method) in enumerate(method_map):
            if method in extractors:
                method = extractors[method]
            method_map[idx] = (pattern, method)

    return (method_map, options_map)


def parse_keywords(strings=[]):
    """Parse keywords specifications from the given list of strings.

    >>> kw = parse_keywords(['_', 'dgettext:2', 'dngettext:2,3', 'pgettext:1c,2']).items()
    >>> kw.sort()
    >>> for keyword, indices in kw:
    ...     print (keyword, indices)
    ('_', None)
    ('dgettext', (2,))
    ('dngettext', (2, 3))
    ('pgettext', ((1, 'c'), 2))
    """
    keywords = {}
    for string in strings:
        if ':' in string:
            funcname, indices = string.split(':')
        else:
            funcname, indices = string, None
        if funcname not in keywords:
            if indices:
                inds = []
                for x in indices.split(','):
                    if x[-1] == 'c':
                        inds.append((int(x[:-1]), 'c'))
                    else:
                        inds.append(int(x))
                indices = tuple(inds)
            keywords[funcname] = indices
    return keywords


if __name__ == '__main__':
    main()
