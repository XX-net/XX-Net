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
"""Code for handling Java jar files.

Jar files are just zip files with a particular interpretation for certain files
in the zip under the META-INF/ directory. So we can read and write them using
the standard zipfile module.

The specification for jar files is at
http://docs.oracle.com/javase/7/docs/technotes/guides/jar/jar.html
"""
from __future__ import with_statement



import os
import re
import sys
import zipfile


_MANIFEST_NAME = 'META-INF/MANIFEST.MF'


class Error(Exception):
  pass


class InvalidJarError(Error):
  pass


class JarWriteError(Error):
  pass


class Manifest(object):
  """The parsed manifest from a jar file.

  Attributes:
    main_section: a dict representing the main (first) section of the manifest.
      Each key is a string that is an attribute, such as 'Manifest-Version', and
      the corresponding value is a string that is the value of the attribute,
      such as '1.0'.
    sections: a dict representing the other sections of the manifest. Each key
      is a string that is the value of the 'Name' attribute for the section,
      and the corresponding value is a dict like the main_section one, for the
      other attributes.
  """

  def __init__(self, main_section, sections):
    self.main_section = main_section
    self.sections = sections


def ReadManifest(jar_file_name):
  """Read and parse the manifest out of the given jar.

  Args:
    jar_file_name: the name of the jar from which the manifest is to be read.

  Returns:
    A parsed Manifest object, or None if the jar has no manifest.

  Raises:
    IOError: if the jar does not exist or cannot be read.
  """
  with zipfile.ZipFile(jar_file_name) as jar:
    try:
      manifest_string = jar.read(_MANIFEST_NAME)
    except KeyError:
      return None
    return _ParseManifest(manifest_string, jar_file_name)


def _ParseManifest(manifest_string, jar_file_name):
  """Parse a Manifest object out of the given string.

  Args:
    manifest_string: a str or unicode that is the manifest contents.
    jar_file_name: a str that is the path of the jar, for use in exception
      messages.

  Returns:
    A Manifest object parsed out of the string.

  Raises:
    InvalidJarError: if the manifest is not well-formed.
  """

  manifest_string = '\n'.join(manifest_string.splitlines()).rstrip('\n')
  section_strings = re.split('\n{2,}', manifest_string)
  parsed_sections = [_ParseManifestSection(s, jar_file_name)
                     for s in section_strings]
  main_section = parsed_sections[0]
  sections = {}
  for entry in parsed_sections[1:]:
    name = entry.get('Name')
    if name is None:
      raise InvalidJarError('%s: Manifest entry has no Name attribute: %r' %
                            (jar_file_name, entry))
    else:
      sections[name] = entry
  return Manifest(main_section, sections)


def _ParseManifestSection(section, jar_file_name):
  """Parse a dict out of the given manifest section string.

  Args:
    section: a str or unicode that is the manifest section. It looks something
      like this (without the >):
      > Name: section-name
      > Some-Attribute: some value
      > Another-Attribute: another value
    jar_file_name: a str that is the path of the jar, for use in exception
      messages.

  Returns:
    A dict where the keys are the attributes (here, 'Name', 'Some-Attribute',
    'Another-Attribute'), and the values are the corresponding attribute values.

  Raises:
    InvalidJarError: if the manifest section is not well-formed.
  """

  section = section.replace('\n ', '').rstrip('\n')
  if not section:
    return {}
  try:
    return dict(line.split(': ', 1) for line in section.split('\n'))
  except ValueError:
    raise InvalidJarError('%s: Invalid manifest %r' % (jar_file_name, section))


def Make(input_directory, output_directory, base_name, maximum_size=sys.maxint,
         include_predicate=lambda name: True):
  """Makes one or more jars from a directory hierarchy.

  Args:
    input_directory: a string that is the root of the directory hierarchy from
      which files will be put in the jar.
    output_directory: a string that is the directory to put the output jars.
    base_name: the name to be used for each output jar. If the name is 'foo'
      then each jar will be called 'foo-nnnn.jar', where nnnn is a sequence of
      digits.
    maximum_size: the maximum allowed total uncompressed size of the files in
      any given jar.
    include_predicate: a function that is called once for each file in the
      directory hierarchy. It is given the name that the file will have in the
      output jar(s), and it must return a true value if the file is to be
      included.

  Raises:
    IOError: if input files cannot be read or output jars cannot be written.
    JarWriteError: if an input file is bigger than maximum_size.
  """
  zip_names = []
  abs_dir = os.path.abspath(input_directory)
  for dirpath, _, files in os.walk(abs_dir):
    if dirpath == abs_dir:
      prefix = ''
    else:
      assert dirpath.startswith(abs_dir)
      prefix = dirpath[len(abs_dir) + 1:].replace(os.sep, '/') + '/'


    zip_names.extend([prefix + f for f in files])

  with _Maker(output_directory, base_name, maximum_size) as maker:
    for name in sorted(zip_names):
      abs_fs_name = os.path.join(abs_dir, os.path.normpath(name))

      if include_predicate(name):
        size = os.path.getsize(abs_fs_name)
        if size > maximum_size:
          raise JarWriteError(
              'File %s has size %d which is bigger than the maximum '
              'jar size %d' % (abs_fs_name, size, maximum_size))
        maker.Write(name, abs_fs_name)


def SplitJar(input_jar, output_directory, maximum_size=sys.maxint,
             include_predicate=lambda name: True):
  """Copies an input jar into a directory, splitting if necessary.

  If its size is > maximum_size, then new jars will be created in
  output_directory, called foo-0000.jar, foo-0001.jar, etc. The jar manifest
  (META-INF/MANIFEST.MF) is not included in the split jars, and neither is the
  index (INDEX.LIST) if any. Manifests are not heavily used at runtime, and
  it's not clear what the correct manifest would be in each individual jar.

  Args:
    input_jar: a string that is the path to the jar to be copied.
    output_directory: a string that is the directory to put the copy or copies.
    maximum_size: the maximum allowed total uncompressed size of the files in
      any given jar.
    include_predicate: a function that is called once for each entry in the
      input jar. It is given the name of the entry, and must return a true value
      if the entry is to be included in the output jar(s).

  Raises:
    IOError: if the input jar cannot be read or the output jars cannot be
      written.
    ValueError: if input_jar does not end with '.jar'.
    JarWriteError: if an entry in the input jar is bigger than maximum_size.
  """
  if not input_jar.lower().endswith('.jar'):
    raise ValueError('Does not end with .jar: %s' % input_jar)

  base_name = os.path.splitext(os.path.basename(input_jar))[0]
  with _Maker(output_directory, base_name, maximum_size) as maker:
    for name, contents in JarContents(input_jar):
      if (name != 'META-INF/MANIFEST.MF' and name != 'INDEX.LIST' and
          include_predicate(name)):
        size = len(contents)
        if size > maximum_size:
          raise JarWriteError(
              'Entry %s in %s has size %d which is bigger than the maximum jar '
              'size %d' % (name, input_jar, size, maximum_size))
        maker.WriteStr(name, contents)


def JarContents(jar_path):
  """Generates (name, contents) pairs for the given jar.

  Each generated tuple consists of the relative name within the jar of an entry,
  for example 'java/lang/Object.class', and a str that is the corresponding
  contents.

  Args:
    jar_path: a str that is the path to the jar.

  Yields:
    A (name, contents) pair.
  """
  with zipfile.ZipFile(jar_path) as jar:
    for name in jar.namelist():
      yield name, jar.read(name)


class _Maker(object):
  """Writes jars to contain the entries supplied to its Write method.

  This class is designed to be used in a with statement.
  """

  def __init__(self, output_directory, base_name, maximum_size=sys.maxint):
    self.base_name = base_name
    self.output_directory = os.path.normpath(output_directory)
    self.maximum_size = maximum_size

    if not os.path.exists(self.output_directory):
      os.makedirs(self.output_directory)
    elif not os.path.isdir(self.output_directory):
      raise JarWriteError('Not a directory: %s' % self.output_directory)




    self.current_jar = None
    self.current_jar_size = 0
    self.jar_suffix = 0

  def __enter__(self):
    return self

  def __exit__(self, t, value, traceback):
    if self.current_jar:
      self.current_jar.close()

  def WriteStr(self, name, content):
    """Write a str as an entry to a jar, creating a new one if necessary.

    If the total uncompressed size of all the entries written to the current jar
    excludes the maximum, the current jar will be closed and a new one created.

    Args:
      name: the relative name of the jar entry, for example
        'java/lang/String.class'.
      content: a str that is the bytes to be written to the jar entry.
    """
    self._WriteEntry(len(content),
                     lambda: self.current_jar.writestr(name, content))

  def Write(self, name, path):
    """Write file as an entry to a jar, creating a new one if necessary.

    If the total uncompressed size of all the entries written to the current jar
    excludes the maximum, the current jar will be closed and a new one created.

    Args:
      name: the relative name of the jar entry, for example
        'java/lang/String.class'.
      path: a str that is the path of the file to be written
    """
    self._WriteEntry(os.path.getsize(path),
                     lambda: self.current_jar.write(path, name))

  def _WriteEntry(self, size, write_func):
    """Write an entry to a jar, creating a new one if necessary.

    If the total uncompressed size of all the entries written to the current jar
    excludes the maximum, the current jar will be closed and a new one created.

    Args:
      size: the size in bytes of the new entry, uncompressed.
      write_func: a function that writes that entry to self.current_jar.
    """
    if self.current_jar_size + size > self.maximum_size:
      self.current_jar.close()
      self.current_jar = None
    if not self.current_jar:
      jar_name = '%s-%04d.jar' % (self.base_name, self.jar_suffix)
      self.jar_suffix += 1
      full_jar_name = os.path.join(self.output_directory, jar_name)
      self.current_jar = zipfile.ZipFile(
          full_jar_name, 'w', zipfile.ZIP_DEFLATED)
      self.current_jar_size = 0
    self.current_jar_size += size
    write_func()
