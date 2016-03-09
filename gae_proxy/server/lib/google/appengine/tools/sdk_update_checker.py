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
"""Checks for SDK updates."""

import datetime
import logging
import os
import socket
import ssl
import sys
import time
import urllib2

import google
import yaml

from google.appengine.api import validation
from google.appengine.api import yaml_object




VERSION_FILE = '../../VERSION'


UPDATE_CHECK_TIMEOUT = 3


NAG_FILE = '.appcfg_nag'


class NagFile(validation.Validated):
  """A validated YAML class to represent the user's nag preferences.

  Attributes:
    timestamp: The timestamp of the last nag.
    opt_in: True if the user wants to check for updates on dev_appserver
      start.  False if not.  May be None if we have not asked the user yet.
  """

  ATTRIBUTES = {
      'timestamp': validation.TYPE_FLOAT,
      'opt_in': validation.Optional(validation.TYPE_BOOL),
  }

  @staticmethod
  def Load(nag_file):
    """Load a single NagFile object where one and only one is expected.

    Args:
      nag_file: A file-like object or string containing the yaml data to parse.

    Returns:
      A NagFile instance.
    """
    return yaml_object.BuildSingleObject(NagFile, nag_file)


def GetVersionObject():
  """Gets the version of the SDK by parsing the VERSION file.

  Returns:
    A Yaml object or None if the VERSION file does not exist.
  """
  version_filename = os.path.join(os.path.dirname(google.appengine.__file__),
                                  VERSION_FILE)
  try:
    version_fh = open(version_filename)
  except IOError:
    logging.error('Could not find version file at %s', version_filename)
    return None
  try:
    version = yaml.safe_load(version_fh)
  finally:
    version_fh.close()

  return version


def _VersionList(release):
  """Parse a version string into a list of ints.

  Args:
    release: The 'release' version, e.g. '1.2.4'.
        (Due to YAML parsing this may also be an int or float.)

  Returns:
    A list of ints corresponding to the parts of the version string
    between periods.  Example:
      '1.2.4' -> [1, 2, 4]
      '1.2.3.4' -> [1, 2, 3, 4]

  Raises:
    ValueError if not all the parts are valid integers.
  """
  return [int(part) for part in str(release).split('.')]


class SDKUpdateChecker(object):
  """Determines if the local SDK is the latest version.

  Nags the user when there are updates to the SDK.  As the SDK becomes
  more out of date, the language in the nagging gets stronger.  We
  store a little yaml file in the user's home directory so that we nag
  the user only once a week.

  The yaml file has the following field:
    'timestamp': Last time we nagged the user in seconds since the epoch.

  Attributes:
    rpcserver: An AbstractRpcServer instance used to check for the latest SDK.
    config: The app's AppInfoExternal.  Needed to determine which api_version
      the app is using.
  """

  def __init__(self,
               rpcserver,
               configs):
    """Create a new SDKUpdateChecker.

    Args:
      rpcserver: The AbstractRpcServer to use.
      configs: A list of yaml objects or a single yaml object that specify the
          configuration of this application.
    """
    if not isinstance(configs, list):
      configs = [configs]
    self.rpcserver = rpcserver
    self.runtimes = set(config.runtime for config in configs)
    self.runtime_to_api_version = {}
    for config in configs:
      self.runtime_to_api_version.setdefault(
          config.runtime, set()).add(config.api_version)

  @staticmethod
  def MakeNagFilename():
    """Returns the filename for the nag file for this user."""





    user_homedir = os.path.expanduser('~/')
    if not os.path.isdir(user_homedir):
      drive, unused_tail = os.path.splitdrive(os.__file__)
      if drive:
        os.environ['HOMEDRIVE'] = drive

    return os.path.expanduser('~/' + NAG_FILE)

  def _ParseVersionFile(self):
    """Parse the local VERSION file.

    Returns:
      A Yaml object or None if the file does not exist.
    """
    return GetVersionObject()

  def CheckSupportedVersion(self):
    """Determines if the app's api_version is supported by the SDK.

    Uses the api_version field from the AppInfoExternal to determine if
    the SDK supports that api_version.

    Raises:
      sys.exit if the api_version is not supported.
    """
    version = self._ParseVersionFile()
    if version is None:
      logging.error('Could not determine if the SDK supports the api_version '
                    'requested in app.yaml.')
      return
    unsupported_api_versions_found = False
    for runtime, api_versions in self.runtime_to_api_version.items():
      supported_api_versions = _GetSupportedApiVersions(version, runtime)
      unsupported_api_versions = sorted(api_versions -
                                        set(supported_api_versions))
      if unsupported_api_versions:
        unsupported_api_versions_found = True
        if len(unsupported_api_versions) == 1:
          logging.critical('The requested api_version (%s) is not supported by '
                           'the %s runtime in this release of the SDK. The '
                           'supported api_versions are %s.',
                           unsupported_api_versions[0], runtime,
                           supported_api_versions)
        else:
          logging.critical('The requested api_versions (%s) are not supported '
                           'by the %s runtime in this release of the SDK. The '
                           'supported api_versions are %s.',
                           unsupported_api_versions, runtime,
                           supported_api_versions)
    if unsupported_api_versions_found:
      sys.exit(1)

  def CheckForUpdates(self):
    """Queries the server for updates and nags the user if appropriate.

    Queries the server for the latest SDK version at the same time reporting
    the local SDK version.  The server will respond with a yaml document
    containing the fields:
      'release': The name of the release (e.g. 1.2).
      'timestamp': The time the release was created (YYYY-MM-DD HH:MM AM/PM TZ).
      'api_versions': A list of api_version strings (e.g. ['1', 'beta']).

    We will nag the user with increasing severity if:
    - There is a new release.
    - There is a new release with a new api_version.
    - There is a new release that does not support an api_version named in
      a configuration in self.configs.
    """
    version = self._ParseVersionFile()
    if version is None:
      logging.info('Skipping update check')
      return
    logging.info('Checking for updates to the SDK.')

    responses = {}



    try:
      for runtime in self.runtimes:
        responses[runtime] = yaml.safe_load(self.rpcserver.Send(
            '/api/updatecheck',
            timeout=UPDATE_CHECK_TIMEOUT,
            release=version['release'],
            timestamp=version['timestamp'],
            api_versions=version['api_versions'],
            runtime=runtime))
    except (urllib2.URLError, socket.error, ssl.SSLError), e:
      logging.info('Update check failed: %s', e)
      return



    try:
      latest = sorted(responses.values(), reverse=True,
                      key=lambda release: _VersionList(release['release']))[0]
    except ValueError:
      logging.warn('Could not parse this release version')

    if version['release'] == latest['release']:
      logging.info('The SDK is up to date.')
      return

    try:
      this_release = _VersionList(version['release'])
    except ValueError:
      logging.warn('Could not parse this release version (%r)',
                   version['release'])
    else:
      try:
        advertised_release = _VersionList(latest['release'])
      except ValueError:
        logging.warn('Could not parse advertised release version (%r)',
                     latest['release'])
      else:
        if this_release > advertised_release:
          logging.info('This SDK release is newer than the advertised release.')
          return

    for runtime, response in responses.items():
      api_versions = _GetSupportedApiVersions(response, runtime)
      obsolete_versions = sorted(
          self.runtime_to_api_version[runtime] - set(api_versions))
      if len(obsolete_versions) == 1:
        self._Nag(
            'The api version you are using (%s) is obsolete!  You should\n'
            'upgrade your SDK and test that your code works with the new\n'
            'api version.' % obsolete_versions[0],
            response, version, force=True)
      elif obsolete_versions:
        self._Nag(
            'The api versions you are using (%s) are obsolete!  You should\n'
            'upgrade your SDK and test that your code works with the new\n'
            'api version.' % obsolete_versions,
            response, version, force=True)

      deprecated_versions = sorted(
          self.runtime_to_api_version[runtime].intersection(api_versions[:-1]))
      if len(deprecated_versions) == 1:
        self._Nag(
            'The api version you are using (%s) is deprecated. You should\n'
            'upgrade your SDK to try the new functionality.' %
            deprecated_versions[0], response, version)
      elif deprecated_versions:
        self._Nag(
            'The api versions you are using (%s) are deprecated. You should\n'
            'upgrade your SDK to try the new functionality.' %
            deprecated_versions, response, version)

    self._Nag('There is a new release of the SDK available.',
              latest, version)

  def _ParseNagFile(self):
    """Parses the nag file.

    Returns:
      A NagFile if the file was present else None.
    """
    nag_filename = SDKUpdateChecker.MakeNagFilename()
    try:
      fh = open(nag_filename)
    except IOError:
      return None
    try:
      nag = NagFile.Load(fh)
    finally:
      fh.close()
    return nag

  def _WriteNagFile(self, nag):
    """Writes the NagFile to the user's nag file.

    If the destination path does not exist, this method will log an error
    and fail silently.

    Args:
      nag: The NagFile to write.
    """
    nagfilename = SDKUpdateChecker.MakeNagFilename()
    try:
      fh = open(nagfilename, 'w')
      try:
        fh.write(nag.ToYAML())
      finally:
        fh.close()
    except (OSError, IOError), e:
      logging.error('Could not write nag file to %s. Error: %s', nagfilename, e)

  def _Nag(self, msg, latest, version, force=False):
    """Prints a nag message and updates the nag file's timestamp.

    Because we don't want to nag the user everytime, we store a simple
    yaml document in the user's home directory.  If the timestamp in this
    doc is over a week old, we'll nag the user.  And when we nag the user,
    we update the timestamp in this doc.

    Args:
      msg: The formatted message to print to the user.
      latest: The yaml document received from the server.
      version: The local yaml version document.
      force: If True, always nag the user, ignoring the nag file.
    """
    nag = self._ParseNagFile()
    if nag and not force:
      last_nag = datetime.datetime.fromtimestamp(nag.timestamp)
      if datetime.datetime.now() - last_nag < datetime.timedelta(weeks=1):
        logging.debug('Skipping nag message')
        return

    if nag is None:
      nag = NagFile()
    nag.timestamp = time.time()
    self._WriteNagFile(nag)

    print '****************************************************************'
    print msg
    print '-----------'
    print 'Latest SDK:'
    print yaml.dump(latest)
    print '-----------'
    print 'Your SDK:'
    print yaml.dump(version)
    print '-----------'
    print 'Please visit https://developers.google.com/appengine/downloads'
    print 'for the latest SDK'
    print '****************************************************************'

  def AllowedToCheckForUpdates(self, input_fn=raw_input):
    """Determines if the user wants to check for updates.

    On startup, the dev_appserver wants to check for updates to the SDK.
    Because this action reports usage to Google when the user is not
    otherwise communicating with Google (e.g. pushing a new app version),
    the user must opt in.

    If the user does not have a nag file, we will query the user and
    save the response in the nag file.  Subsequent calls to this function
    will re-use that response.

    Args:
      input_fn: used to collect user input. This is for testing only.

    Returns:
      True if the user wants to check for updates.  False otherwise.
    """
    nag = self._ParseNagFile()
    if nag is None:
      nag = NagFile()
      nag.timestamp = 0.0

    if nag.opt_in is None:
      answer = input_fn('Allow dev_appserver to check for updates on startup? '
                        '(Y/n): ')
      answer = answer.strip().lower()
      if answer == 'n' or answer == 'no':
        print ('dev_appserver will not check for updates on startup.  To '
               'change this setting, edit %s' %
               SDKUpdateChecker.MakeNagFilename())
        nag.opt_in = False
      else:

        print ('dev_appserver will check for updates on startup.  To change '
               'this setting, edit %s' % SDKUpdateChecker.MakeNagFilename())
        nag.opt_in = True
      self._WriteNagFile(nag)
    return nag.opt_in


def _GetSupportedApiVersions(versions, runtime):
  """Returns the runtime-specific or general list of supported runtimes.

  The provided 'versions' dict contains a field called 'api_versions'
  which is the list of default versions supported.  This dict may also
  contain a 'supported_api_versions' dict which lists api_versions by
  runtime.  This function will prefer to return the runtime-specific
  api_versions list, but will default to the general list.

  Args:
    versions: dict of versions from app.yaml or /api/updatecheck server.
    runtime: string of current runtime (e.g. 'go').

  Returns:
    List of supported api_versions (e.g. ['go1']).
  """
  if 'supported_api_versions' in versions:
    return versions['supported_api_versions'].get(
        runtime, versions)['api_versions']
  return versions['api_versions']
