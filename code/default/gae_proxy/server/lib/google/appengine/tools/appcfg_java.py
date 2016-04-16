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
"""Appcfg logic specific to Java apps."""
from __future__ import with_statement

import collections
import os.path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

from google.appengine.datastore import datastore_index
from google.appengine.datastore import datastore_index_xml
from google.appengine.tools import app_engine_web_xml_parser
from google.appengine.tools import backends_xml_parser
from google.appengine.tools import cron_xml_parser
from google.appengine.tools import dispatch_xml_parser
from google.appengine.tools import dos_xml_parser
from google.appengine.tools import jarfile
from google.appengine.tools import java_quickstart
from google.appengine.tools import java_utils
from google.appengine.tools import queue_xml_parser
from google.appengine.tools import web_xml_parser
from google.appengine.tools import xml_parser_utils
from google.appengine.tools import yaml_translator


_CLASSES_JAR_NAME_PREFIX = '_ah_webinf_classes'
_COMPILED_JSP_JAR_NAME_PREFIX = '_ah_compiled_jsps'
_LOCAL_JSPC_CLASS = 'com.google.appengine.tools.development.LocalJspC'
_MAX_COMPILED_JSP_JAR_SIZE = 1024 * 1024 * 5


class Error(Exception):
  pass


class ConfigurationError(Error):
  """There was a configuration error in the application being uploaded."""
  pass


class CompileError(Error):
  """There was a compilation error in a JSP file or its generated Java code."""
  pass


def IsWarFileWithoutYaml(dir_path):
  if os.path.isfile(os.path.join(dir_path, 'app.yaml')):
    return False
  web_inf = os.path.join(dir_path, 'WEB-INF')
  return (os.path.isdir(web_inf) and
          set(['appengine-web.xml', 'web.xml']).issubset(os.listdir(web_inf)))


def AddUpdateOptions(parser):
  """Adds options specific to the 'update' command on Java apps to 'parser'.

  Args:
    parser: An instance of OptionsParser.
  """
  parser.add_option('--retain_upload_dir', action='store_true',
                    dest='retain_upload_dir', default=False,
                    help='Do not delete temporary (staging) directory used '
                    'in uploading Java apps')
  parser.add_option('--no_symlinks', action='store_true',
                    dest='no_symlinks', default=False,
                    help='Do not use symbolic links when making the temporary '
                    '(staging) directory for uploading Java apps')
  parser.add_option('--compile_encoding', action='store',
                    dest='compile_encoding', default='UTF-8',
                    help='Set the encoding to be used when compiling Java '
                    'source files (default "UTF-8").')
  parser.add_option('--disable_jar_jsps', action='store_false',
                    dest='jar_jsps', default=True,
                    help='Do not jar the classes generated from JSPs.')
  parser.add_option('--delete_jsps', action='store_true',
                    dest='delete_jsps', default=False,
                    help='Delete the JSP source files after compilation.')
  parser.add_option('--enable_jar_classes', action='store_true',
                    dest='do_jar_classes', default=False,
                    help='Jar the WEB-INF/classes content.')
  parser.add_option('--enable_jar_splitting', action='store_true',
                    dest='do_jar_splitting', default=False,
                    help='Split large jar files (> 32M) into smaller '
                    'fragments.')
  parser.add_option('--jar_splitting_excludes', action='store',
                    dest='jar_splitting_exclude_suffixes', default='',
                    help='When --enable_jar_splitting is specified and '
                    '--jar_splitting_excludes specifies a comma-separated list '
                    'of suffixes, a file in a jar whose name ends with one '
                    'of the suffixes will not be included in the split jar '
                    'fragments.')


class JavaAppUpdate(object):
  """Performs Java-specific update configurations."""

  _JSP_REGEX = re.compile('.*\\.jspx?')

  _xml_parser = collections.namedtuple(
      '_xml_parser', ['xml_name', 'yaml_name', 'xml_to_yaml_function'])

  _XML_PARSERS = [
      _xml_parser('backends.xml', 'backends.yaml',
                  backends_xml_parser.GetBackendsYaml),
      _xml_parser('cron.xml', 'cron.yaml', cron_xml_parser.GetCronYaml),
      _xml_parser('dispatch.xml', 'dispatch.yaml',
                  dispatch_xml_parser.GetDispatchYaml),
      _xml_parser('dos.xml', 'dos.yaml', dos_xml_parser.GetDosYaml),
      _xml_parser('queue.xml', 'queue.yaml', queue_xml_parser.GetQueueYaml),
  ]

  _XML_VALIDATOR_CLASS = 'com.google.appengine.tools.admin.XmlValidator'

  def __init__(self, basepath, options):
    self.basepath = os.path.abspath(basepath)
    self.options = options
    if not hasattr(self.options, 'no_symlinks'):

      self.options.no_symlinks = True



    java_home, exec_suffix = java_utils.JavaHomeAndSuffix()
    self.java_command = os.path.join(java_home, 'bin', 'java' + exec_suffix)
    self.javac_command = os.path.join(java_home, 'bin', 'javac' + exec_suffix)

    self._ValidateXmlFiles()

    self.app_engine_web_xml = self._ReadAppEngineWebXml()
    self.app_engine_web_xml.app_root = self.basepath
    if self.options.app_id:
      self.app_engine_web_xml.app_id = self.options.app_id
    if self.options.version:
      self.app_engine_web_xml.version_id = self.options.version
    quickstart = xml_parser_utils.BooleanValue(
        self.app_engine_web_xml.beta_settings.get('java_quickstart', 'false'))
    if quickstart:
      web_xml_str, _ = java_quickstart.quickstart_generator(self.basepath)
      webdefault_xml_str = java_quickstart.get_webdefault_xml()
      web_xml_str = java_quickstart.remove_mappings(
          web_xml_str, webdefault_xml_str)
      self.web_xml = web_xml_parser.WebXmlParser().ProcessXml(web_xml_str)
    else:
      self.web_xml = self._ReadWebXml()

  def _ValidateXmlFiles(self):








    sdk_dir = os.path.dirname(jarfile.__file__)
    xml_validator_jar = os.path.join(
        sdk_dir, 'java', 'lib', 'impl', 'libxmlvalidator.jar')
    if not os.path.exists(xml_validator_jar):

      print >>sys.stderr, ('Not validating XML files because %s does not '
                           'exist' % xml_validator_jar)
      return
    validator_args = []
    schema_dir = os.path.join(sdk_dir, 'java', 'docs')
    for schema_name in os.listdir(schema_dir):
      basename, extension = os.path.splitext(schema_name)
      if extension == '.xsd':
        schema_file = os.path.join(schema_dir, schema_name)
        xml_file = os.path.join(self.basepath, 'WEB-INF', basename + '.xml')
        if os.path.exists(xml_file):
          validator_args += [xml_file, schema_file]
    if validator_args:
      command_and_args = [
          self.java_command,
          '-classpath',
          xml_validator_jar,
          self._XML_VALIDATOR_CLASS,
      ] + validator_args
      status = subprocess.call(command_and_args)
      if status:

        raise ConfigurationError('XML validation failed')

  def _ReadAppEngineWebXml(self):
    return self._ReadAndParseXml(
        basepath=self.basepath,
        file_name='appengine-web.xml',
        parser=app_engine_web_xml_parser.AppEngineWebXmlParser)

  def _ReadWebXml(self, basepath=None):
    if not basepath:
      basepath = self.basepath
    return self._ReadAndParseXml(
        basepath=basepath,
        file_name='web.xml',
        parser=web_xml_parser.WebXmlParser)

  def _ReadAndParseXml(self, basepath, file_name, parser):
    with open(os.path.join(basepath, 'WEB-INF', file_name)) as file_handle:
      return parser().ProcessXml(file_handle.read())

  def CreateStagingDirectory(self, tools_dir):
    """Creates a staging directory for uploading.

    This is where we perform the necessary actions to create an application
    directory for the update command to work properly - files are organized
    into the static folder, and yaml files are generated where they can be
    found later.

    Args:
      tools_dir: Path to the SDK tools directory
        (typically .../google/appengine/tools)

    Returns:
      The path to a new temporary directory which contains generated yaml files
      and a static file directory. For the most part, the rest of the update and
      upload flow can resume identically to Python/PHP/Go applications.

    Raises:
      CompileError: if compilation of JSPs failed.
      ConfigurationError: if the app to be staged has a configuration error.
      IOError: if there was an I/O problem, for example when scanning jar files.
    """
    stage_dir = tempfile.mkdtemp(prefix='appcfgpy')
    static_dir = os.path.join(stage_dir, '__static__')
    os.mkdir(static_dir)
    self._CopyOrLink(self.basepath, stage_dir, static_dir, False)
    self.app_engine_web_xml.app_root = stage_dir

    if self.options.compile_jsps:
      self._CompileJspsIfAny(tools_dir, stage_dir)

    web_inf = os.path.join(stage_dir, 'WEB-INF')
    web_inf_lib = os.path.join(web_inf, 'lib')
    api_jar_dict = _FindApiJars(web_inf_lib)
    api_versions = set(api_jar_dict.values())
    if not api_versions:
      api_version = None
    elif len(api_versions) == 1:
      api_version = api_versions.pop()
    else:
      raise ConfigurationError('API jars have inconsistent versions: %s' %
                               api_jar_dict)


    for staged_api_jar in api_jar_dict:
      os.remove(staged_api_jar)

    appengine_generated = os.path.join(
        stage_dir, 'WEB-INF', 'appengine-generated')
    self._GenerateAppYaml(stage_dir, api_version, appengine_generated)

    app_id = self.options.app_id or self.app_engine_web_xml.app_id
    assert app_id, 'Missing app id'


    for parser in self._XML_PARSERS:
      xml_name = os.path.join(web_inf, parser.xml_name)
      if os.path.exists(xml_name):
        with open(xml_name) as xml_file:
          xml_string = xml_file.read()
        yaml_string = parser.xml_to_yaml_function(app_id, xml_string)
        yaml_file = os.path.join(appengine_generated, parser.yaml_name)
        with open(yaml_file, 'w') as yaml:
          yaml.write(yaml_string)






    indexes = []
    for xml_name in (
        'datastore-indexes.xml',
        os.path.join('appengine-generated', 'datastore-indexes-auto.xml')):
      xml_name = os.path.join(self.basepath, 'WEB-INF', xml_name)
      if os.path.exists(xml_name):
        with open(xml_name) as xml_file:
          xml_string = xml_file.read()
        index_definitions = datastore_index_xml.IndexesXmlToIndexDefinitions(
            xml_string)
        indexes.extend(index_definitions.indexes)
    if indexes:
      yaml_string = datastore_index.IndexDefinitions(indexes=indexes).ToYAML()
      yaml_file = os.path.join(appengine_generated, 'index.yaml')
      with open(yaml_file, 'w') as yaml:
        yaml.write(yaml_string)

    return stage_dir

  def GenerateAppYamlString(self, static_file_list, api_version=None):
    """Constructs an app.yaml string equivalent to the XML files under WEB-INF.

    Args:
      static_file_list: a list of strings that are the absolute path names of
        static file resources.
      api_version: a string that is the Java API version number, or None if
        not known or relevant.

    Returns:
      A string that would have the same effect as the XML files under WEB-INF
      if it were the contents of an app.yaml file.
    """
    return yaml_translator.AppYamlTranslator(
        self.app_engine_web_xml,
        self.web_xml,
        static_file_list,
        api_version).GetYaml()

  def _GenerateAppYaml(self, stage_dir, api_version, appengine_generated):
    """Creates the app.yaml file in WEB-INF/appengine-generated/.

    Returns:
      The path to the WEB-INF/appengine-generated directory.
    """
    static_file_list = self._GetStaticFileList(stage_dir)
    yaml_str = self.GenerateAppYamlString(static_file_list, api_version)
    if not os.path.isdir(appengine_generated):
      os.mkdir(appengine_generated)
    with open(os.path.join(appengine_generated, 'app.yaml'), 'w') as handle:
      handle.write(yaml_str)

  def _CopyOrLink(self, source_dir, stage_dir, static_dir, inside_web_inf):
    source_dir = os.path.abspath(source_dir)
    stage_dir = os.path.abspath(stage_dir)
    static_dir = os.path.abspath(static_dir)
    for file_name in os.listdir(source_dir):
      file_path = os.path.join(source_dir, file_name)

      if file_name.startswith('.') or file_name == 'appengine-generated':
        continue

      if os.path.isdir(file_path):
        self._CopyOrLink(
            file_path,
            os.path.join(stage_dir, file_name),
            os.path.join(static_dir, file_name),
            inside_web_inf or file_name == 'WEB-INF')
      else:
        if (inside_web_inf
            or self.app_engine_web_xml.IncludesResource(file_path)
            or (self.options.compile_jsps
                and file_path.lower().endswith('.jsp'))):
          self._CopyOrLinkFile(file_path, os.path.join(stage_dir, file_name))
        if (not inside_web_inf
            and self.app_engine_web_xml.IncludesStatic(file_path)):
          self._CopyOrLinkFile(file_path, os.path.join(static_dir, file_name))

  def _CopyOrLinkFile(self, source, dest):

    destdir = os.path.dirname(dest)
    if not os.path.exists(destdir):
      os.makedirs(destdir)
    if self._ShouldSplitJar(source):
      self._SplitJar(source, destdir)
    elif source.endswith('web.xml'):
      shutil.copy(source, dest)
      os.chmod(dest, os.stat(dest).st_mode | stat.S_IWRITE)

    elif self.options.no_symlinks:
      shutil.copy(source, dest)
    else:
      os.symlink(source, dest)

  def _MoveDirectoryContents(self, source_dir, dest_dir):
    """Move the contents of source_dir to dest_dir, which might not exist.

    Raises:
      IOError: if the dest_dir hierarchy already contains a file where the
        source_dir hierarchy has a file or directory of the same name, or if
        the dest_dir hierarchy already contains a directory where the source_dir
        hierarchy has a file of the same name.
    """
    if not os.path.exists(dest_dir):
      os.mkdir(dest_dir)
    for entry in os.listdir(source_dir):
      source_entry = os.path.join(source_dir, entry)
      dest_entry = os.path.join(dest_dir, entry)
      if os.path.exists(dest_entry):
        if os.path.isdir(source_entry) and os.path.isdir(dest_entry):
          self._MoveDirectoryContents(source_entry, dest_entry)
        else:
          raise IOError('Cannot overwrite existing %s' % dest_entry)
      else:
        shutil.move(source_entry, dest_entry)

  _MAX_SIZE = 32 * 1000 * 1000


  def _ShouldSplitJar(self, path):
    return (path.lower().endswith('.jar') and self.options.do_jar_splitting and
            os.path.getsize(path) >= self._MAX_SIZE)

  def _SplitJar(self, jar_path, dest_dir):
    """Split a source jar into two or more jars in the given dest_dir.

    Args:
      jar_path: string that is the path to jar to be split. The contents of this
        jar will be copied into the output jars, but the jar itself will not be
        affected.
      dest_dir: directory into which to put the jars that result from splitting
        the input jar.

    Raises:
      IOError: if the jar cannot be split.
    """

    exclude_suffixes = (
        set(self.options.jar_splitting_exclude_suffixes.split(',')) - set(['']))
    include = lambda name: not any(name.endswith(s) for s in exclude_suffixes)
    jarfile.SplitJar(jar_path, dest_dir, self._MAX_SIZE, include)

  @staticmethod
  def _GetStaticFileList(staging_dir):
    return _FilesMatching(os.path.join(staging_dir, '__static__'))

  def _CompileJspsIfAny(self, tools_dir, staging_dir):
    """Compiles JSP files, if any, into .class files.."""
    if self._MatchingFileExists(self._JSP_REGEX, staging_dir):
      gen_dir = tempfile.mkdtemp()
      try:
        self._CompileJspsWithGenDir(tools_dir, staging_dir, gen_dir)
      finally:
        shutil.rmtree(gen_dir)

  def _CompileJspsWithGenDir(self, tools_dir, staging_dir, gen_dir):
    staging_web_inf = os.path.join(staging_dir, 'WEB-INF')
    lib_dir = os.path.join(staging_web_inf, 'lib')

    for jar_file in GetUserJspLibFiles(tools_dir):
      self._CopyOrLinkFile(
          jar_file, os.path.join(lib_dir, os.path.basename(jar_file)))
    for jar_file in GetSharedJspLibFiles(tools_dir):
      self._CopyOrLinkFile(
          jar_file, os.path.join(lib_dir, os.path.basename(jar_file)))

    classes_dir = os.path.join(staging_web_inf, 'classes')
    generated_web_xml = os.path.join(staging_web_inf, 'generated_web.xml')

    classpath = self._GetJspClasspath(tools_dir, classes_dir, gen_dir)

    command_and_args = [
        self.java_command,
        '-classpath', classpath,
        _LOCAL_JSPC_CLASS,
        '-uriroot', staging_dir,
        '-p', 'org.apache.jsp',
        '-l',
        '-v',
        '-webinc', generated_web_xml,
        '-d', gen_dir,
        '-javaEncoding', self.options.compile_encoding,
    ]

    status = subprocess.call(command_and_args)
    if status:
      raise CompileError(
          'Compilation of JSPs exited with status %d' % status)

    self._CompileJavaFiles(classpath, staging_web_inf, gen_dir)


    self.web_xml = self._ReadWebXml(staging_dir)

  def _CompileJavaFiles(self, classpath, web_inf, jsp_class_dir):
    """Compile all *.java files found under jsp_class_dir."""
    java_files = _FilesMatching(jsp_class_dir, lambda f: f.endswith('.java'))
    if not java_files:
      return

    command_and_args = [
        self.javac_command,
        '-classpath', classpath,
        '-d', jsp_class_dir,
        '-source', '7',
        '-target', '7',
        '-encoding', self.options.compile_encoding,
    ] + java_files

    status = subprocess.call(command_and_args)
    if status:
      raise CompileError(
          'Compilation of JSP-generated code exited with status %d' % status)

    if self.options.jar_jsps:
      self._ZipJasperGeneratedFiles(web_inf, jsp_class_dir)
    else:
      web_inf_classes = os.path.join(web_inf, 'classes')
      self._MoveDirectoryContents(jsp_class_dir, web_inf_classes)

    if self.options.delete_jsps:
      jsps = _FilesMatching(os.path.dirname(web_inf),
                            lambda f: f.endswith('.jsp'))
      for f in jsps:
        os.remove(f)

    if self.options.do_jar_classes:
      self._ZipWebInfClassesFiles(web_inf)

  @staticmethod
  def _ZipJasperGeneratedFiles(web_inf, jsp_class_dir):
    lib_dir = os.path.join(web_inf, 'lib')
    jarfile.Make(jsp_class_dir, lib_dir, _COMPILED_JSP_JAR_NAME_PREFIX,
                 maximum_size=_MAX_COMPILED_JSP_JAR_SIZE,
                 include_predicate=lambda name: not name.endswith('.java'))

  @staticmethod
  def _ZipWebInfClassesFiles(web_inf):


    lib_dir = os.path.join(web_inf, 'lib')
    classes_dir = os.path.join(web_inf, 'classes')
    jarfile.Make(classes_dir, lib_dir, _CLASSES_JAR_NAME_PREFIX,
                 maximum_size=_MAX_COMPILED_JSP_JAR_SIZE)
    shutil.rmtree(classes_dir)

    os.mkdir(classes_dir)

  @staticmethod
  def _GetJspClasspath(tools_dir, classes_dir, gen_dir):
    """Builds the classpath for the JSP Compilation system call."""
    lib_dir = os.path.join(os.path.dirname(classes_dir), 'lib')
    elements = (
        GetImplLibs(tools_dir) + GetSharedLibFiles(tools_dir) +
        [classes_dir, gen_dir] +
        _FilesMatching(
            lib_dir, lambda f: f.endswith('.jar') or f.endswith('.zip')))

    return (os.pathsep).join(elements)

  @staticmethod
  def _MatchingFileExists(regex, dir_path):
    for _, _, files in os.walk(dir_path):
      for f in files:
        if re.search(regex, f):
          return True
    return False


def GetImplLibs(tools_dir):
  return _GetLibsShallow(os.path.join(tools_dir, 'java', 'lib', 'impl'))


def GetSharedLibFiles(tools_dir):
  return _GetLibsRecursive(os.path.join(tools_dir, 'java', 'lib', 'shared'))


def GetUserJspLibFiles(tools_dir):
  return _GetLibsRecursive(
      os.path.join(tools_dir, 'java', 'lib', 'tools', 'jsp'))


def GetSharedJspLibFiles(tools_dir):
  return _GetLibsRecursive(
      os.path.join(tools_dir, 'java', 'lib', 'shared', 'jsp'))


def _GetLibsRecursive(dir_path):
  return _FilesMatching(dir_path, lambda f: f.endswith('.jar'))


def _GetLibsShallow(dir_path):
  libs = []
  for f in os.listdir(dir_path):
    if os.path.isfile(os.path.join(dir_path, f)) and f.endswith('.jar'):
      libs.append(os.path.join(dir_path, f))
  return libs


def _FilesMatching(root, predicate=lambda f: True):
  """Finds all files under the given root that match the given predicate.

  Args:
    root: a string that is the absolute or relative path to a directory.
    predicate: a function that takes a file name (without a directory) and
      returns a truth value.

  Returns:
    A list of strings that are the paths of every file under the given root
    that satisfies the given predicate. The paths are absolute if and only if
    the input root is absolute.
  """
  matches = []
  for path, _, files in os.walk(root):
    matches += [os.path.join(path, f) for f in files if predicate(f)]
  return matches


def _FindApiJars(lib_dir):
  """Find the appengine-api-*.jar and its version.

  The version of an appengine-api-*.jar is the Specification-Version attribute
  in the jar's manifest section whose Name is 'com/google/appengine/api/'.

  Args:
    lib_dir: the base directory under which jars are to be found.

  Returns:
    A dict from string to string, mapping all found API jars to their
    corresponding versions.

  Raises:
    IOError: if there was a problem reading the jars.
  """
  result = {}
  for jar_file in _FilesMatching(lib_dir, lambda f: f.endswith('.jar')):
    manifest = jarfile.ReadManifest(jar_file)
    if manifest:
      section = manifest.sections.get('com/google/appengine/api/')
      if section and 'Specification-Version' in section:
        result[jar_file] = section['Specification-Version']
  return result
