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




"""AppInfo tools.

Library for working with AppInfo records in memory, store and load from
configuration files.
"""









import logging
import re

from google.appengine.api import appinfo_errors
from google.appengine.api import backendinfo
from google.appengine.api import validation
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_object




_URL_REGEX = r'(?!\^)/|\.|(\(.).*(?!\$).'
_FILES_REGEX = r'(?!\^).*(?!\$).'
_URL_ROOT_REGEX = r'/.*'


_DELTA_REGEX = r'([0-9]+)([DdHhMm]|[sS]?)'
_EXPIRATION_REGEX = r'\s*(%s)(\s+%s)*\s*' % (_DELTA_REGEX, _DELTA_REGEX)
_START_PATH = '/_ah/start'




_ALLOWED_SERVICES = ['mail', 'xmpp_message', 'xmpp_subscribe', 'xmpp_presence',
                     'xmpp_error', 'channel_presence', 'rest', 'warmup']
_SERVICE_RE_STRING = '(' + '|'.join(_ALLOWED_SERVICES) + ')'


_PAGE_NAME_REGEX = r'^.+$'


_EXPIRATION_CONVERSIONS = {
    'd': 60 * 60 * 24,
    'h': 60 * 60,
    'm': 60,
    's': 1,
}



APP_ID_MAX_LEN = 100
MAJOR_VERSION_ID_MAX_LEN = 100
MAX_URL_MAPS = 100


PARTITION_SEPARATOR = '~'


DOMAIN_SEPARATOR = ':'



PARTITION_RE_STRING = (r'[a-z\d\-]{1,%d}\%s' %
                       (APP_ID_MAX_LEN, PARTITION_SEPARATOR))
DOMAIN_RE_STRING = (r'(?!\-)[a-z\d\-\.]{1,%d}%s' %
                    (APP_ID_MAX_LEN, DOMAIN_SEPARATOR))
DISPLAY_APP_ID_RE_STRING = (r'(?!-)[a-z\d\-]{1,%d}' % (APP_ID_MAX_LEN))
APPLICATION_RE_STRING = (r'(?:%s)?(?:%s)?%s' %
                         (PARTITION_RE_STRING,
                          DOMAIN_RE_STRING,
                          DISPLAY_APP_ID_RE_STRING))




VERSION_RE_STRING = r'(?!-)[a-z\d\-]{1,%d}' % MAJOR_VERSION_ID_MAX_LEN
ALTERNATE_HOSTNAME_SEPARATOR = '-dot-'


BUILTIN_NAME_PREFIX = 'ah-builtin'

RUNTIME_RE_STRING = r'[a-z][a-z0-9]{0,29}'

API_VERSION_RE_STRING = r'[\w.]{1,32}'

HANDLER_STATIC_FILES = 'static_files'
HANDLER_STATIC_DIR = 'static_dir'
HANDLER_SCRIPT = 'script'
HANDLER_API_ENDPOINT = 'api_endpoint'

LOGIN_OPTIONAL = 'optional'
LOGIN_REQUIRED = 'required'
LOGIN_ADMIN = 'admin'

AUTH_FAIL_ACTION_REDIRECT = 'redirect'
AUTH_FAIL_ACTION_UNAUTHORIZED = 'unauthorized'

SECURE_HTTP = 'never'
SECURE_HTTPS = 'always'
SECURE_HTTP_OR_HTTPS = 'optional'

SECURE_DEFAULT = 'default'

REQUIRE_MATCHING_FILE = 'require_matching_file'

DEFAULT_SKIP_FILES = (r'^(.*/)?('
                      r'(#.*#)|'
                      r'(.*~)|'
                      r'(.*\.py[co])|'
                      r'(.*/RCS/.*)|'
                      r'(\..*)|'
                      r')$')

DEFAULT_NOBUILD_FILES = (r'^$')


LOGIN = 'login'
AUTH_FAIL_ACTION = 'auth_fail_action'
SECURE = 'secure'
URL = 'url'
POSITION = 'position'
POSITION_HEAD = 'head'
POSITION_TAIL = 'tail'
STATIC_FILES = 'static_files'
UPLOAD = 'upload'
STATIC_DIR = 'static_dir'
MIME_TYPE = 'mime_type'
SCRIPT = 'script'
EXPIRATION = 'expiration'
API_ENDPOINT = 'api_endpoint'


APPLICATION = 'application'
VERSION = 'version'
MAJOR_VERSION = 'major_version'
MINOR_VERSION = 'minor_version'
RUNTIME = 'runtime'
API_VERSION = 'api_version'
BUILTINS = 'builtins'
INCLUDES = 'includes'
HANDLERS = 'handlers'
LIBRARIES = 'libraries'
DEFAULT_EXPIRATION = 'default_expiration'
SKIP_FILES = 'skip_files'
NOBUILD_FILES = 'nobuild_files'
SERVICES = 'inbound_services'
DERIVED_FILE_TYPE = 'derived_file_type'
JAVA_PRECOMPILED = 'java_precompiled'
PYTHON_PRECOMPILED = 'python_precompiled'
ADMIN_CONSOLE = 'admin_console'
ERROR_HANDLERS = 'error_handlers'
BACKENDS = 'backends'
THREADSAFE = 'threadsafe'
API_CONFIG = 'api_config'
CODE_LOCK = 'code_lock'


PAGES = 'pages'
NAME = 'name'


ERROR_CODE = 'error_code'
FILE = 'file'
_ERROR_CODE_REGEX = r'(default|over_quota|dos_api_denial|timeout)'


ON = 'on'
ON_ALIASES = ['yes', 'y', 'True', 't', '1', 'true']
OFF = 'off'
OFF_ALIASES = ['no', 'n', 'False', 'f', '0', 'false']



SUPPORTED_LIBRARIES = {
    'django': ['1.2'],
    'jinja2': ['2.6'],
    'lxml': ['2.3'],
    'markupsafe': ['0.15'],
    'numpy': ['1.6.1'],
    'PIL': ['1.1.7'],
    'pycrypto': ['2.3'],
    'setuptools': ['0.6c11'],
    'webapp2': ['2.3'],
    'webob': ['1.1.1'],
    'yaml': ['3.10'],
}


class HandlerBase(validation.Validated):
  """Base class for URLMap and ApiConfigHandler."""
  ATTRIBUTES = {

      URL: validation.Optional(_URL_REGEX),
      LOGIN: validation.Options(LOGIN_OPTIONAL,
                                LOGIN_REQUIRED,
                                LOGIN_ADMIN,
                                default=LOGIN_OPTIONAL),

      AUTH_FAIL_ACTION: validation.Options(AUTH_FAIL_ACTION_REDIRECT,
                                           AUTH_FAIL_ACTION_UNAUTHORIZED,
                                           default=AUTH_FAIL_ACTION_REDIRECT),

      SECURE: validation.Options(SECURE_HTTP,
                                 SECURE_HTTPS,
                                 SECURE_HTTP_OR_HTTPS,
                                 SECURE_DEFAULT,
                                 default=SECURE_DEFAULT),


      HANDLER_SCRIPT: validation.Optional(_FILES_REGEX)
  }


class URLMap(HandlerBase):
  """Mapping from URLs to handlers.

  This class acts like something of a union type.  Its purpose is to
  describe a mapping between a set of URLs and their handlers.  What
  handler type a given instance has is determined by which handler-id
  attribute is used.

  Each mapping can have one and only one handler type.  Attempting to
  use more than one handler-id attribute will cause an UnknownHandlerType
  to be raised during validation.  Failure to provide any handler-id
  attributes will cause MissingHandlerType to be raised during validation.

  The regular expression used by the url field will be used to match against
  the entire URL path and query string of the request.  This means that
  partial maps will not be matched.  Specifying a url, say /admin, is the
  same as matching against the regular expression '^/admin$'.  Don't begin
  your matching url with ^ or end them with $.  These regular expressions
  won't be accepted and will raise ValueError.

  Attributes:
    login: Whether or not login is required to access URL.  Defaults to
      'optional'.
    secure: Restriction on the protocol which can be used to serve
            this URL/handler (HTTP, HTTPS or either).
    url: Regular expression used to fully match against the request URLs path.
      See Special Cases for using static_dir.
    static_files: Handler id attribute that maps URL to the appropriate
      file.  Can use back regex references to the string matched to url.
    upload: Regular expression used by the application configuration
      program to know which files are uploaded as blobs.  It's very
      difficult to determine this using just the url and static_files
      so this attribute must be included.  Required when defining a
      static_files mapping.
      A matching file name must fully match against the upload regex, similar
      to how url is matched against the request path.  Do not begin upload
      with ^ or end it with $.
    static_dir: Handler id that maps the provided url to a sub-directory
      within the application directory.  See Special Cases.
    mime_type: When used with static_files and static_dir the mime-type
      of files served from those directories are overridden with this
      value.
    script: Handler id that maps URLs to scipt handler within the application
      directory that will run using CGI.
    position: Used in AppInclude objects to specify whether a handler
      should be inserted at the beginning of the primary handler list or at the
      end.  If 'tail' is specified, the handler is inserted at the end,
      otherwise, the handler is inserted at the beginning.  This means that
      'head' is the effective default.
    expiration: When used with static files and directories, the time delta to
      use for cache expiration. Has the form '4d 5h 30m 15s', where each letter
      signifies days, hours, minutes, and seconds, respectively. The 's' for
      seconds may be omitted. Only one amount must be specified, combining
      multiple amounts is optional. Example good values: '10', '1d 6h',
      '1h 30m', '7d 7d 7d', '5m 30'.
    api_endpoint: Handler id that identifies endpoint as an API endpoint,
      calls that terminate here will be handled by the api serving framework.

  Special cases:
    When defining a static_dir handler, do not use a regular expression
    in the url attribute.  Both the url and static_dir attributes are
    automatically mapped to these equivalents:

      <url>/(.*)
      <static_dir>/\1

    For example:

      url: /images
      static_dir: images_folder

    Is the same as this static_files declaration:

      url: /images/(.*)
      static_files: images_folder/\1
      upload: images_folder/(.*)
  """
  ATTRIBUTES = {


      HANDLER_STATIC_FILES: validation.Optional(_FILES_REGEX),
      UPLOAD: validation.Optional(_FILES_REGEX),


      HANDLER_STATIC_DIR: validation.Optional(_FILES_REGEX),


      MIME_TYPE: validation.Optional(str),
      EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      REQUIRE_MATCHING_FILE: validation.Optional(bool),


      POSITION: validation.Optional(validation.Options(POSITION_HEAD,
                                                       POSITION_TAIL)),


      HANDLER_API_ENDPOINT: validation.Optional(validation.Options(
          (ON, ON_ALIASES),
          (OFF, OFF_ALIASES))),
  }
  ATTRIBUTES.update(HandlerBase.ATTRIBUTES)

  COMMON_FIELDS = set([URL, LOGIN, AUTH_FAIL_ACTION, SECURE])



  ALLOWED_FIELDS = {
      HANDLER_STATIC_FILES: (MIME_TYPE, UPLOAD, EXPIRATION,
                             REQUIRE_MATCHING_FILE),
      HANDLER_STATIC_DIR: (MIME_TYPE, EXPIRATION, REQUIRE_MATCHING_FILE),
      HANDLER_SCRIPT: (POSITION),
      HANDLER_API_ENDPOINT: (POSITION, SCRIPT),
  }

  def GetHandler(self):
    """Get handler for mapping.

    Returns:
      Value of the handler (determined by handler id attribute).
    """
    return getattr(self, self.GetHandlerType())

  def GetHandlerType(self):
    """Get handler type of mapping.

    Returns:
      Handler type determined by which handler id attribute is set.

    Raises:
      UnknownHandlerType: when none of the no handler id attributes are set.

      UnexpectedHandlerAttribute: when an unexpected attribute is set for the
        discovered handler type.

      HandlerTypeMissingAttribute: when the handler is missing a required
        attribute for its handler type.
    """
    for id_field in URLMap.ALLOWED_FIELDS.iterkeys():

      if getattr(self, id_field) is not None:

        mapping_type = id_field
        break
    else:

      raise appinfo_errors.UnknownHandlerType(
          'Unknown url handler type.\n%s' % str(self))

    allowed_fields = URLMap.ALLOWED_FIELDS[mapping_type]



    for attribute in self.ATTRIBUTES.iterkeys():
      if (getattr(self, attribute) is not None and
          not (attribute in allowed_fields or
               attribute in URLMap.COMMON_FIELDS or
               attribute == mapping_type)):
        raise appinfo_errors.UnexpectedHandlerAttribute(
            'Unexpected attribute "%s" for mapping type %s.' %
            (attribute, mapping_type))




    if mapping_type == HANDLER_STATIC_FILES and not self.upload:
      raise appinfo_errors.MissingHandlerAttribute(
          'Missing "%s" attribute for URL "%s".' % (UPLOAD, self.url))

    return mapping_type

  def CheckInitialized(self):
    """Adds additional checking to make sure handler has correct fields.

    In addition to normal ValidatedCheck calls GetHandlerType
    which validates all the handler fields are configured
    properly.

    Raises:
      UnknownHandlerType when none of the no handler id attributes
      are set.

      UnexpectedHandlerAttribute when an unexpected attribute
      is set for the discovered handler type.

      HandlerTypeMissingAttribute when the handler is missing a
      required attribute for its handler type.
    """
    super(URLMap, self).CheckInitialized()
    self.GetHandlerType()

  def FixSecureDefaults(self):
    """Force omitted 'secure: ...' handler fields to 'secure: optional'.

    The effect is that handler.secure is never equal to the (nominal)
    default.

    See http://b/issue?id=2073962.
    """
    if self.secure == SECURE_DEFAULT:
      self.secure = SECURE_HTTP_OR_HTTPS

  def WarnReservedURLs(self):
    """Generates a warning for reserved URLs.

    See:
    http://code.google.com/appengine/docs/python/config/appconfig.html#Reserved_URLs
    """
    if self.url == '/form':
      logging.warning(
          'The URL path "/form" is reserved and will not be matched.')

  def ErrorOnPositionForAppInfo(self):
    """Raises an error if position is specified outside of AppInclude objects.
    """
    if self.position:
      raise appinfo_errors.PositionUsedInAppYamlHandler(
          'The position attribute was specified for this handler, but this is '
          'an app.yaml file.  Position attribute is only valid for '
          'include.yaml files.')


class AdminConsolePage(validation.Validated):
  """Class representing admin console page in AdminConsole object.
  """
  ATTRIBUTES = {
      URL: _URL_REGEX,
      NAME: _PAGE_NAME_REGEX,
  }


class AdminConsole(validation.Validated):
  """Class representing admin console directives in application info.
  """
  ATTRIBUTES = {
      PAGES: validation.Optional(validation.Repeated(AdminConsolePage)),
  }

  @classmethod
  def Merge(cls, adminconsole_one, adminconsole_two):
    """Return the result of merging two AdminConsole objects."""








    if not adminconsole_one or not adminconsole_two:
      return adminconsole_one or adminconsole_two

    if adminconsole_one.pages:
      if adminconsole_two.pages:
        adminconsole_one.pages.extend(adminconsole_two.pages)
    else:
      adminconsole_one.pages = adminconsole_two.pages

    return adminconsole_one


class ErrorHandlers(validation.Validated):
  """Class representing error handler directives in application info.
  """
  ATTRIBUTES = {
      ERROR_CODE: validation.Optional(_ERROR_CODE_REGEX),
      FILE: _FILES_REGEX,
      MIME_TYPE: validation.Optional(str),
  }


class BuiltinHandler(validation.Validated):
  """Class representing builtin handler directives in application info.

  Permits arbitrary keys but their values must be described by the
  validation.Options object returned by ATTRIBUTES.
  """






































  class DynamicAttributes(dict):
    """Provide a dictionary object that will always claim to have a key.

    This dictionary returns a fixed value for any get operation.  The fixed
    value passed in as a constructor parameter should be a
    validation.Validated object.
    """

    def __init__(self, return_value, **parameters):
      self.__return_value = return_value
      dict.__init__(self, parameters)

    def __contains__(self, _):
      return True

    def __getitem__(self, _):
      return self.__return_value

  ATTRIBUTES = DynamicAttributes(
      validation.Optional(validation.Options((ON, ON_ALIASES),
                                             (OFF, OFF_ALIASES))))

  def __init__(self, **attributes):
    """Ensure that all BuiltinHandler objects at least have attribute 'default'.
    """
    self.ATTRIBUTES.clear()
    self.builtin_name = ''
    super(BuiltinHandler, self).__init__(**attributes)

  def __setattr__(self, key, value):
    """Permit ATTRIBUTES.iteritems() to return set of items that have values.

    Whenever validate calls iteritems(), it is always called on ATTRIBUTES,
    not on __dict__, so this override is important to ensure that functions
    such as ToYAML() return the correct set of keys.
    """
    if key == 'builtin_name':
      object.__setattr__(self, key, value)
    elif not self.builtin_name:
      self.ATTRIBUTES[key] = ''
      self.builtin_name = key
      super(BuiltinHandler, self).__setattr__(key, value)
    else:




      raise appinfo_errors.MultipleBuiltinsSpecified(
          'More than one builtin defined in list element.  Each new builtin '
          'should be prefixed by "-".')

  def ToDict(self):
    """Convert BuiltinHander object to a dictionary.

    Returns:
      dictionary of the form: {builtin_handler_name: on/off}
    """
    return {self.builtin_name: getattr(self, self.builtin_name)}

  @classmethod
  def IsDefined(cls, builtins_list, builtin_name):
    """Find if a builtin is defined in a given list of builtin handler objects.

    Args:
      builtins_list: list of BuiltinHandler objects (typically yaml.builtins)
      builtin_name: name of builtin to find whether or not it is defined

    Returns:
      true if builtin_name is defined by a member of builtins_list,
      false otherwise
    """
    for b in builtins_list:
      if b.builtin_name == builtin_name:
        return True
    return False

  @classmethod
  def ListToTuples(cls, builtins_list):
    """Converts a list of BuiltinHandler objects to a list of (name, status)."""
    return [(b.builtin_name, getattr(b, b.builtin_name)) for b in builtins_list]

  @classmethod
  def Validate(cls, builtins_list):
    """Verify that all BuiltinHandler objects are valid and not repeated.

    Args:
      builtins_list: list of BuiltinHandler objects to validate.

    Raises:
      InvalidBuiltinFormat if the name of a Builtinhandler object
          cannot be determined.
      DuplicateBuiltinSpecified if a builtin handler name is used
          more than once in the list.
    """
    seen = set()
    for b in builtins_list:
      if not b.builtin_name:
        raise appinfo_errors.InvalidBuiltinFormat(
            'Name of builtin for list object %s could not be determined.'
            % b)
      if b.builtin_name in seen:
        raise appinfo_errors.DuplicateBuiltinsSpecified(
            'Builtin %s was specified more than once in one yaml file.'
            % b.builtin_name)
      seen.add(b.builtin_name)


class ApiConfigHandler(HandlerBase):
  """Class representing api_config handler directives in application info."""
  ATTRIBUTES = HandlerBase.ATTRIBUTES
  ATTRIBUTES.update({

      URL: validation.Regex(_URL_REGEX),
      HANDLER_SCRIPT: validation.Regex(_FILES_REGEX)
  })


class Library(validation.Validated):
  """Class representing the configuration of a single library."""

  ATTRIBUTES = {'name': validation.Type(str),
                'version': validation.Type(str)}

  def CheckInitialized(self):
    """Raises if the library configuration is not valid."""
    super(Library, self).CheckInitialized()
    if self.name not in SUPPORTED_LIBRARIES:
      raise appinfo_errors.InvalidLibraryName(
          'the library "%s" is not supported' % self.name)
    if self.version != 'latest':
      if self.version not in SUPPORTED_LIBRARIES[self.name]:
        raise appinfo_errors.InvalidLibraryVersion(
            '%s version "%s" is not supported, '
            'use one of: "%s" or "latest"' % (
                self.name,
                self.version,
                '", "'.join(SUPPORTED_LIBRARIES[self.name])))


class AppInclude(validation.Validated):
  """Class representing the contents of an included app.yaml file.

  Used for both builtins and includes directives.
  """

  ATTRIBUTES = {
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap)),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),


  }

  @classmethod
  def MergeAppYamlAppInclude(cls, appyaml, appinclude):
    """This function merges an app.yaml file with referenced builtins/includes.
    """




    if not appinclude:
      return appyaml


    if appinclude.handlers:
      tail = appyaml.handlers or []
      appyaml.handlers = []

      for h in appinclude.handlers:
        if not h.position or h.position == 'head':
          appyaml.handlers.append(h)
        else:
          tail.append(h)

      appyaml.handlers.extend(tail)


    appyaml.admin_console = AdminConsole.Merge(appyaml.admin_console,
                                               appinclude.admin_console)

    return appyaml

  @classmethod
  def MergeAppIncludes(cls, appinclude_one, appinclude_two):
    """This function merges the non-referential state of the provided AppInclude
    objects.  That is, builtins and includes directives are not preserved, but
    any static objects are copied into an aggregate AppInclude object that
    preserves the directives of both provided AppInclude objects.

    Args:
      appinclude_one: object one to merge
      appinclude_two: object two to merge

    Returns:
      AppInclude object that is the result of merging the static directives of
      appinclude_one and appinclude_two.
    """



    if not appinclude_one or not appinclude_two:
      return appinclude_one or appinclude_two


    if appinclude_one.handlers:
      if appinclude_two.handlers:
        appinclude_one.handlers.extend(appinclude_two.handlers)
    else:
      appinclude_one.handlers = appinclude_two.handlers


    appinclude_one.admin_console = (
        AdminConsole.Merge(appinclude_one.admin_console,
                           appinclude_two.admin_console))

    return appinclude_one


class AppInfoExternal(validation.Validated):
  """Class representing users application info.

  This class is passed to a yaml_object builder to provide the validation
  for the application information file format parser.

  Attributes:
    application: Unique identifier for application.
    version: Application's major version.
    runtime: Runtime used by application.
    api_version: Which version of APIs to use.
    handlers: List of URL handlers.
    default_expiration: Default time delta to use for cache expiration for
      all static files, unless they have their own specific 'expiration' set.
      See the URLMap.expiration field's documentation for more information.
    skip_files: An re object.  Files that match this regular expression will
      not be uploaded by appcfg.py.  For example:
        skip_files: |
          .svn.*|
          #.*#
    nobuild_files: An re object.  Files that match this regular expression will
      not be built into the app.  Go only.
    api_config: URL root and script/servlet path for enhanced api serving
  """

  ATTRIBUTES = {


      APPLICATION: APPLICATION_RE_STRING,
      VERSION: validation.Optional(VERSION_RE_STRING),
      RUNTIME: RUNTIME_RE_STRING,


      API_VERSION: API_VERSION_RE_STRING,
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap)),
      LIBRARIES: validation.Optional(validation.Repeated(Library)),

      SERVICES: validation.Optional(validation.Repeated(
          validation.Regex(_SERVICE_RE_STRING))),
      DEFAULT_EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      SKIP_FILES: validation.RegexStr(default=DEFAULT_SKIP_FILES),
      NOBUILD_FILES: validation.RegexStr(default=DEFAULT_NOBUILD_FILES),
      DERIVED_FILE_TYPE: validation.Optional(validation.Repeated(
          validation.Options(JAVA_PRECOMPILED, PYTHON_PRECOMPILED))),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),
      ERROR_HANDLERS: validation.Optional(validation.Repeated(ErrorHandlers)),
      BACKENDS: validation.Optional(validation.Repeated(
          backendinfo.BackendEntry)),
      THREADSAFE: validation.Optional(bool),
      API_CONFIG: validation.Optional(ApiConfigHandler),
      CODE_LOCK: validation.Optional(bool),
  }

  def CheckInitialized(self):
    """Performs non-regex-based validation.

    The following are verified:
      - At least one url mapping is provided in the URL mappers.
      - Number of url mappers doesn't exceed MAX_URL_MAPS.
      - Major version does not contain the string -dot-.
      - If api_endpoints are defined, an api_config stanza must be defined.
      - If the runtime is python27 and threadsafe is set, then no CGI handlers
        can be used.
      - That the version name doesn't start with BUILTIN_NAME_PREFIX

    Raises:
      MissingURLMapping: if no URLMap object is present in the object.
      TooManyURLMappings: if there are too many URLMap entries.
      MissingApiConfig: if api_endpoints exist without an api_config.
      MissingThreadsafe: if threadsafe is not set but the runtime requires it.
      ThreadsafeWithCgiHandler: if the runtime is python27, threadsafe is set
          and CGI handlers are specified.
    """
    super(AppInfoExternal, self).CheckInitialized()
    if not self.handlers and not self.builtins and not self.includes:
      raise appinfo_errors.MissingURLMapping(
          'No URLMap entries found in application configuration')
    if self.handlers and len(self.handlers) > MAX_URL_MAPS:
      raise appinfo_errors.TooManyURLMappings(
          'Found more than %d URLMap entries in application configuration' %
          MAX_URL_MAPS)

    if self.threadsafe is None and self.runtime == 'python27':
      raise appinfo_errors.MissingThreadsafe(
          'threadsafe must be present and set to either "yes" or "no"')

    if self.libraries:
      if self.runtime != 'python27':
        raise appinfo_errors.RuntimeDoesNotSupportLibraries(
            'libraries entries are only supported by the "python27" runtime')

      library_names = [library.name for library in self.libraries]
      for library_name in library_names:
        if library_names.count(library_name) > 1:
          raise appinfo_errors.DuplicateLibrary(
              'Duplicate library entry for %s' % library_name)

    if self.version and self.version.find(ALTERNATE_HOSTNAME_SEPARATOR) != -1:
      raise validation.ValidationError(
          'Version "%s" cannot contain the string "%s"' % (
              self.version, ALTERNATE_HOSTNAME_SEPARATOR))
    if self.version and self.version.startswith(BUILTIN_NAME_PREFIX):
      raise validation.ValidationError(
          ('Version "%s" cannot start with "%s" because it is a '
           'reserved version name prefix.') % (self.version,
                                               BUILTIN_NAME_PREFIX))
    if self.handlers:
      api_endpoints = [handler.url for handler in self.handlers
                       if handler.GetHandlerType() == HANDLER_API_ENDPOINT]
      if api_endpoints and not self.api_config:
        raise appinfo_errors.MissingApiConfig(
            'An api_endpoint handler was specified, but the required '
            'api_config stanza was not configured.')
      if self.threadsafe and self.runtime == 'python27':
        for handler in self.handlers:
          if (handler.script and (handler.script.endswith('.py') or
                                  '/' in handler.script)):
            raise appinfo_errors.ThreadsafeWithCgiHandler(
                'threadsafe cannot be enabled with CGI handler: %s' %
                handler.script)

  def ApplyBackendSettings(self, backend_name):
    """Applies settings from the indicated backend to the AppInfoExternal.

    Backend entries may contain directives that modify other parts of the
    app.yaml, such as the 'start' directive, which adds a handler for the start
    request.  This method performs those modifications.

    Args:
      backend_name: The name of a backend defined in 'backends'.

    Raises:
      BackendNotFound: If the indicated backend was not listed in 'backends'.
    """
    if backend_name is None:
      return

    if self.backends is None:
      raise appinfo_errors.BackendNotFound

    self.version = backend_name

    match = None
    for backend in self.backends:
      if backend.name != backend_name:
        continue
      if match:
        raise appinfo_errors.DuplicateBackend
      else:
        match = backend

    if match is None:
      raise appinfo_errors.BackendNotFound

    if match.start is None:
      return

    start_handler = URLMap(url=_START_PATH, script=match.start)
    self.handlers.insert(0, start_handler)


def ValidateHandlers(handlers, is_include_file=False):
  """Validates a list of handler (URLMap) objects.

  Args:
    handlers: A list of a handler (URLMap) objects.
    is_include_file: If true, indicates the we are performing validation
      for handlers in an AppInclude file, which may contain special directives.
  """
  if not handlers:
    return

  for handler in handlers:
    handler.FixSecureDefaults()
    handler.WarnReservedURLs()
    if not is_include_file:
      handler.ErrorOnPositionForAppInfo()


def LoadSingleAppInfo(app_info):
  """Load a single AppInfo object where one and only one is expected.

  Args:
    app_info: A file-like object or string.  If it is a string, parse it as
    a configuration file.  If it is a file-like object, read in data and
    parse.

  Returns:
    An instance of AppInfoExternal as loaded from a YAML file.

  Raises:
    ValueError: if a specified service is not valid.
    EmptyConfigurationFile: when there are no documents in YAML file.
    MultipleConfigurationFile: when there is more than one document in YAML
    file.
  """
  builder = yaml_object.ObjectBuilder(AppInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_info)

  app_infos = handler.GetResults()
  if len(app_infos) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(app_infos) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  appyaml = app_infos[0]
  ValidateHandlers(appyaml.handlers)
  if appyaml.builtins:
    BuiltinHandler.Validate(appyaml.builtins)

  return appyaml


class AppInfoSummary(validation.Validated):
  """This class contains only basic summary information about an app.

  It is used to pass back information about the newly created app to users
  after a new version has been created.
  """
  ATTRIBUTES = {
      APPLICATION: APPLICATION_RE_STRING,
      MAJOR_VERSION: VERSION_RE_STRING,
      MINOR_VERSION: validation.TYPE_LONG
  }


def LoadAppInclude(app_include):
  """Load a single AppInclude object where one and only one is expected.

  Args:
    app_include: A file-like object or string.  If it is a string, parse it as
    a configuration file.  If it is a file-like object, read in data and
    parse.

  Returns:
    An instance of AppInclude as loaded from a YAML file.

  Raises:
    EmptyConfigurationFile: when there are no documents in YAML file.
    MultipleConfigurationFile: when there is more than one document in YAML
    file.
  """
  builder = yaml_object.ObjectBuilder(AppInclude)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_include)

  includes = handler.GetResults()
  if len(includes) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(includes) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  includeyaml = includes[0]
  if includeyaml.handlers:
    for handler in includeyaml.handlers:
      handler.FixSecureDefaults()
      handler.WarnReservedURLs()
  if includeyaml.builtins:
    BuiltinHandler.Validate(includeyaml.builtins)

  return includeyaml


def ParseExpiration(expiration):
  """Parses an expiration delta string.

  Args:
    expiration: String that matches _DELTA_REGEX.

  Returns:
    Time delta in seconds.
  """
  delta = 0
  for match in re.finditer(_DELTA_REGEX, expiration):
    amount = int(match.group(1))
    units = _EXPIRATION_CONVERSIONS.get(match.group(2).lower(), 1)
    delta += amount * units
  return delta






_file_path_positive_re = re.compile(r'^[ 0-9a-zA-Z\._\+/\$-]{1,256}$')


_file_path_negative_1_re = re.compile(r'\.\.|^\./|\.$|/\./|^-|^_ah/')


_file_path_negative_2_re = re.compile(r'//|/$')



_file_path_negative_3_re = re.compile(r'^ | $|/ | /')


def ValidFilename(filename):
  """Determines if filename is valid.

  filename must be a valid pathname.
  - It must contain only letters, numbers, _, +, /, $, ., and -.
  - It must be less than 256 chars.
  - It must not contain "/./", "/../", or "//".
  - It must not end in "/".
  - All spaces must be in the middle of a directory or file name.

  Args:
    filename: The filename to validate.

  Returns:
    An error string if the filename is invalid.  Returns '' if the filename
    is valid.
  """
  if _file_path_positive_re.match(filename) is None:
    return 'Invalid character in filename: %s' % filename
  if _file_path_negative_1_re.search(filename) is not None:
    return ('Filename cannot contain "." or ".." '
            'or start with "-" or "_ah/": %s' %
            filename)
  if _file_path_negative_2_re.search(filename) is not None:
    return 'Filename cannot have trailing / or contain //: %s' % filename
  if _file_path_negative_3_re.search(filename) is not None:
    return 'Any spaces must be in the middle of a filename: %s' % filename
  return ''
