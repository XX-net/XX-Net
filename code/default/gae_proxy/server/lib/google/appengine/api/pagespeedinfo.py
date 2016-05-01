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




"""PageSpeed configuration tools.

Library for parsing pagespeed configuration data from app.yaml and working
with these in memory.
"""








import google

from google.appengine.api import validation
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_object

_URL_BLACKLIST_REGEX = r'http(s)?://\S{0,499}'
_REWRITER_NAME_REGEX = r'[a-zA-Z0-9_]+'
_DOMAINS_TO_REWRITE_REGEX = r'(http(s)?://)?[-a-zA-Z0-9_.*]+(:\d+)?'

URL_BLACKLIST = 'url_blacklist'
ENABLED_REWRITERS = 'enabled_rewriters'
DISABLED_REWRITERS = 'disabled_rewriters'
DOMAINS_TO_REWRITE = 'domains_to_rewrite'


class MalformedPagespeedConfiguration(Exception):
  """Configuration file for PageSpeed API is malformed."""






class PagespeedEntry(validation.Validated):
  """Describes the format of a pagespeed configuration from a yaml file.

  URL blacklist entries are patterns (with '?' and '*' as wildcards).  Any URLs
  that match a pattern on the blacklist will not be optimized by PageSpeed.

  Rewriter names are strings (like 'CombineCss' or 'RemoveComments') describing
  individual PageSpeed rewriters.  A full list of valid rewriter names can be
  found in the PageSpeed documentation.

  The domains-to-rewrite list is a whitelist of domain name patterns with '*' as
  a wildcard, optionally starting with 'http://' or 'https://'.  If no protocol
  is given, 'http://' is assumed.  A resource will only be rewritten if it is on
  the same domain as the HTML that references it, or if its domain is on the
  domains-to-rewrite list.
  """
  ATTRIBUTES = {
      URL_BLACKLIST: validation.Optional(
          validation.Repeated(validation.Regex(_URL_BLACKLIST_REGEX))),
      ENABLED_REWRITERS: validation.Optional(
          validation.Repeated(validation.Regex(_REWRITER_NAME_REGEX))),
      DISABLED_REWRITERS: validation.Optional(
          validation.Repeated(validation.Regex(_REWRITER_NAME_REGEX))),
      DOMAINS_TO_REWRITE: validation.Optional(
          validation.Repeated(validation.Regex(_DOMAINS_TO_REWRITE_REGEX))),
  }


def LoadPagespeedEntry(pagespeed_entry, open_fn=None):
  """Load a yaml file or string and return a PagespeedEntry.

  Args:
    pagespeed_entry: The contents of a pagespeed entry from a yaml file
      as a string, or an open file object.
    open_fn: Function for opening files. Unused.

  Returns:
    A PagespeedEntry instance which represents the contents of the parsed yaml.

  Raises:
    yaml_errors.EventError: An error occured while parsing the yaml.
    MalformedPagespeedConfiguration: The configuration is parseable but invalid.
  """
  builder = yaml_object.ObjectBuilder(PagespeedEntry)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(pagespeed_entry)

  parsed_yaml = handler.GetResults()
  if not parsed_yaml:
    return PagespeedEntry()

  if len(parsed_yaml) > 1:
    raise MalformedPagespeedConfiguration(
        'Multiple configuration sections in the yaml')

  return parsed_yaml[0]
