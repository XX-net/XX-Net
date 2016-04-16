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
"""Code for representing and manipulating handlers in app.yaml.

App.yaml requires developers to list handlers - specifications for how URL
requests in their app are handled. This module contains classes for
representing handlers, as well as functions for creating handlers from
specifications in appengine-web.xml and web.xml, manipulating and matching
paths, and ordering them correctly so that the yaml file preserves the semantics
of the user-specified xml.

In this module:
  Handler: Ancestor class that provides pattern matching and other utilities.
  SimpleHandler: A representation of path handling specified in XML - a path
    along with properties detailing how it is handled.
  OverlappedHandler: A representation of combinations of paths specified by
    users in Xml. OverlappedHandlers combine properties, such as security
    settings, from the SimpleHandlers that they are made up of.
  GetOrderedIntersection: Returns an ordered list of Handlers that can be
    written directly to Yaml.
"""

import fnmatch
import itertools
import re


class Handler(object):
  """Ancestor class for Handler manipulation. Patterns are globs.

  (http://en.wikipedia.org/wiki/Glob_(programming)).
  """

  ALL_PROPERTIES = [
      'expiration',
      'http_headers',
      'required_role',
      'transport_guarantee',
      'type',
      'welcome'
      ]

  def __init__(self, pattern):
    self.pattern = pattern

  def _GetPattern(self):
    return self._pattern

  def _SetPattern(self, the_pattern):
    self._pattern = the_pattern
    self._regex = re.compile(re.escape(the_pattern).replace('\\*', '.*') + '$')
    self.is_literal = '*' not in the_pattern

  pattern = property(_GetPattern, _SetPattern)

  @property
  def regex(self):
    return self._regex

  def Regexify(self):
    """Returns a regex-looking string to write to Yaml."""

    return self.pattern.replace('.', '\\.').replace('*', '.*')

  def MatchesString(self, pattern_str):
    """Returns true if input path string is matched by glob pattern."""
    return self._regex.match(pattern_str) is not None

  def MatchesAll(self, other_glob):
    """Returns True if self matches everything other_glob matches."""


















    return self.MatchesString(other_glob.pattern)

  def HasMoreSpecificPatternThan(self, other_handler):
    """Returns True if self is more specific than other_handler.

    Priority in determining specificity is first determined by literal-ness,
    second by length. This is according to the Java servlet spec for
    mapping URL paths.

    Args:
      other_handler: another handler to compare against.

    Returns:
      True if self.pattern is a literal and other_handler.pattern is not,
      False if vice versa, and otherwise True if self.pattern is longer.
    """

    if self.is_literal != other_handler.is_literal:
      return self.is_literal

    return len(self.pattern) > len(other_handler.pattern)

  def __eq__(self, other_handler):
    return (isinstance(other_handler, Handler) and
            self.__dict__ == other_handler.__dict__)

  def IsFullyHandledBy(self, other_handler):
    """Returns True if self specifies something unique.

    For example, If we have a Handler with pattern "foo*bar"
    which has properties {'type': 'static'}, and other_handler
    has pattern "foo*" with the same properties, then
    other_handler does everything that self does.

    Args:
      other_handler: other handler to be matched against
    Returns:
      Boolean value of whether other_handler fully handles self.
    """
    return (other_handler.MatchesAll(self) and
            self._PropertiesMatch(other_handler))

  def _PropertiesMatch(self, other):
    """Returns True if other.properties is superset of self.properties."""
    for prop in Handler.ALL_PROPERTIES:
      if self.GetProperty(prop) not in (None, other.GetProperty(prop)):
        return False
    return True


def _MakeHandlerList(*pattern_strings):
  return [SimpleHandler(a) for a in pattern_strings]


class SimpleHandler(Handler):
  """Subclass of Handler which includes user-defined settings with urls.

  SimpleHandlers should be treated as immutable.
  """

  def __init__(self, pattern, properties=None):
    super(SimpleHandler, self).__init__(pattern)
    if properties:
      self.properties = properties
    else:
      self.properties = {}

  def __hash__(self):
    return hash((self.pattern, tuple(sorted(self.properties.items()))))

  def GetProperty(self, prop, default=None):
    return self.properties.get(prop, default)

  def CreateOverlappedHandler(self):
    """Creates a Combined Handler with self's pattern and self as a child."""
    return OverlappedHandler(self.pattern, matchers=[self])


class OverlappedHandler(Handler):
  """Subclass of Handler which allows for the combination of SimpleHandlers.

  An intuitive way to think about globbed patterns is as sets - for example, the
  pattern "admin/*" is the set of all paths that are in the admin/ directory,
  and the pattern "*.txt" is the set of all paths to text files. An
  OverlappedHandler is designed to describe the intersection of the sets
  of paths - ie the set of paths that is matched by EVERY one its
  handler patterns.

  In the Xml files, paths are specified in different places - in servlet
  patterns, in static files includes, in security constraint specifications,
  etc. There is often some overlap between the paths that are specified by
  these patterns. Since App.Yaml does not have separate places to specify how
  different paths are handled, but rather just lists paths along with a bunch
  of ways that the paths is handled, we need to make sure that these properties
  for various paths are being combined at some point in the translation process.

  Thus an OverlappedHandler holds a list of "matchers" - ie. handlers with more
  general patterns, to choose properties from. OverlappedHandlers do not
  explicitly specify properties but rather choose the value from the most
  specific "matcher" with the value of that property specified. The matchers
  are SimpleHandlers.

  Attributes:
    pattern: inherited from Handler.
    matchers: A list of SimpleHandlers. Matchers are handlers which happen to
      match OverlappedHandler's pattern and whose properties are thus necessary
      to track in order to make sure that OverlappedHandler's pattern is handled
      correctly.
  """

  def __init__(self, pattern, matchers=()):
    super(OverlappedHandler, self).__init__(pattern)
    self.matchers = []
    for sub_handler in matchers:
      self.AddMatchingHandler(sub_handler)

  def GetProperty(self, prop, default=None):
    """Returns the property value of matcher with most specific pattern."""

    largest_handler = None
    prop_value = default
    for sub_handler in self.matchers:
      if sub_handler.GetProperty(prop) is not None:
        if (not largest_handler or
            sub_handler.HasMoreSpecificPatternThan(largest_handler)):
          largest_handler = sub_handler
          prop_value = sub_handler.GetProperty(prop)
    return prop_value

  def __eq__(self, other_handler):
    return (isinstance(other_handler, OverlappedHandler) and
            self.pattern == other_handler.pattern and
            set(self.matchers) == set(other_handler.matchers))

  def AddMatchingHandler(self, matcher):
    """Flattens the handler if it is overlapped and adds to matchers."""
    if isinstance(matcher, SimpleHandler):
      self.matchers.append(matcher)
    else:
      self.matchers.extend(matcher.matchers)


def GetOrderedIntersection(handler_list):
  """Implements algorithm for combining and reordering Handlers.

  GetOrderedIntersection performs the heavy lifting of converting a randomly
  ordered list of Handlers (globbed patterns, each with various potentially
  conflicting properties attached), into an ordered list of handlers with
  property values resolved.

  The purpose of this process is to convert the Web.xml URL mapping scheme to
  that of app.yaml. In Web.xml the most specific path, according to
  literal-ness and length, is chosen. In app.yaml the first listed matching
  path is chosen. Thus to preserve user preferences through the translation
  process we order the patterns from specific to general.

  For example, if three handlers are given as input (in any order):

  "/admin/*" (security=admin)
  "/*.png" (type=static)
  "*" (type=dynamic, security=required)

  we want to get this ordered list as output:
  1. "/admin/*.png" (security=admin, type=static)
  2. "/admin/*" (security=admin, type=dynamic)
  3. "/*.png" (security=required, type=static)
  4. "*" (type=dynamic, security=required).

  so that the properties of any given path are those of the longest matching
  path. The SimpleHandler and OverlappedHandler classes provide the logic for
  attaching globbed patterns to the right properties and resolving potential
  property value conflicts.

  Args:
    handler_list: List of SimpleHandlers in arbitrary order.
  Returns:
    An ordered list of OverlappedHandlers and SimpleHandlers. See the above
    example for what this would look like.
  """
  results = _Intersect(handler_list)




  results = sorted(results, key=lambda h: h.pattern)
  _ReorderHandlers(results)
  _GivePropertiesFromGeneralToSpecific(results)
  return _RemoveRedundantHandlers(results)


def _RemoveRedundantHandlers(handler_list):
  """Removes duplicated or unnecessary handlers from the list.

  If a handler's pattern and functionality are fully matched by another handler
  with a more general pattern, we do not need the  first handler. At the same
  time, we remove duplicates.

  Args:
    handler_list: list of ordered handlers with possibly redundant entries.
  Returns:
    new list which contains entries of handler_list, except redundant ones.
  """

  no_duplicates = []
  patterns_found_so_far = set()
  for i in xrange(len(handler_list)):
    current_handler = handler_list[i]
    matched_by_later = False
    for j in xrange(i + 1, len(handler_list)):
      if current_handler.IsFullyHandledBy(handler_list[j]):
        matched_by_later = True
        break

    if (not matched_by_later and
        current_handler.pattern not in patterns_found_so_far):
      no_duplicates.append(current_handler)
      patterns_found_so_far.add(current_handler.pattern)

  return no_duplicates


def _ReorderHandlers(handler_list):
  """Reorders handlers from specific to general for writing to yaml file.

  This is a topological sort - ie. it makes sure that elements related to
  each other are ordered correctly. In this case, we want to make sure that
  any Handler with a pattern that matches all of the Handlers of another pattern
  occurs later. Thus, we want to make sure that "foo*" occurs after "foo*bar",
  but it does not matter how it is ordered relative to "*baz", since they have
  an empty intersection of patterns.

  The problem with using Python's built-in sorted is that it relies on the
  class's less-than operator. We want an ordering such that
    (handler1 < handler2) iff (not handler1.MatchesAll(handler2))
  Then, since "foo*" and "*baz" do not contain each other, foo* < *baz == True
  and *baz < foo* == True. This is a problem because Python's sorted does not
  explicitly compare every pair of elements, but operates under the assumption
  that if a < b and b < c, then a < c. Therefore, if we have
    a = "foo*bar", b = "*baz", c = "foo*"
  then a < b == True and b < c == True, so a < c is assumed to be True. This
  often leads to wrong orderings.

  Therefore, this function performs a topological sort
  (http://en.wikipedia.org/wiki/Topological_sorting), reordering only those
  patterns where one matches all of the other.

  This is an in-place sort.

  Args:
    handler_list: Unordered list of handlers.
  """
  for i, j in itertools.combinations(xrange(len(handler_list)), 2):
    if handler_list[i].MatchesAll(handler_list[j]):
      handler_list[i], handler_list[j] = handler_list[j], handler_list[i]


def _GivePropertiesFromGeneralToSpecific(handler_list):
  """Makes sure that handlers have all properties of more general ones.

  Ex. Since "*" matches everything "admin/*" matches, we want everything
  matched by "admin/*" to have all the properties specified to "*".
  Therefore we give properties from the "*" handler to the "admin/*" handler.
  If the "*" handler is a SimpleHandler, it carries its own properties, so it
  becomes a child of the "admin/*" handler. Otherwise, its properties are
  define by its children, so its children are copied to the "admin/*"
  handler.

  This is an in-place mutation of the list.

  Args:
    handler_list: List of ordered Handlers.
  """
  for i, j in itertools.combinations(xrange(len(handler_list)), 2):
    if handler_list[j].MatchesAll(handler_list[i]):
      if isinstance(handler_list[i], SimpleHandler):
        handler_list[i] = handler_list[i].CreateOverlappedHandler()
      handler_list[i].AddMatchingHandler(handler_list[j])


def _Intersect(handler_list):
  """Returns an unordered list of all possible intersections of handlers."""
  if not handler_list:
    return set()

  handlers = set([handler_list[0]])




  for input_handler in handler_list[1:]:
    new_handlers = set()
    for g in handlers:
      new_handlers |= _IntersectTwoHandlers(input_handler, g)
    handlers = new_handlers
  return list(handlers)


def _IntersectTwoHandlers(first_handler, second_handler):
  """Returns intersections of first_handler and second_handler patterns."""
  shared_prefix = _SharedPrefix(first_handler.pattern, second_handler.pattern)

  if shared_prefix:
    return _HandleCommonPrefix(first_handler, second_handler, shared_prefix)


  shared_suffix = _SharedSuffix(first_handler.pattern, second_handler.pattern)
  if shared_suffix:
    return _HandleCommonSuffix(first_handler, second_handler, shared_suffix)

  handler_set = set()
  handler_set |= _HandleWildcardCases(first_handler, second_handler)


  handler_set |= _HandleWildcardCases(second_handler, first_handler)

  handler_set |= set([first_handler, second_handler])

  return handler_set


def _HandleWildcardCases(first_handler, second_handler):
  """Handle cases with trailing and leading wildcards.

  This function finds the set of intersections of two handlers where one has a
  leading wildcard (eg. *foo) in its pattern and at least one has a trailing
  wildcard (eg. baz*) in its pattern. The arguments are not symmetric.

  Args:
    first_handler: A SimpleHandler instance
    second_handler: A SimpleHandler instance
  Returns:
    A set of intersection patterns of the two Handlers. Example: If the
    pattern of first_handler is abc* and that of the second is *xyz, we return
    the intersection of the patterns, abc*xyz. Find more examples in the inline
    comments.
  """
  merged_handlers = set()

  if len(first_handler.pattern) <= 1 or len(second_handler.pattern) <= 1:
    return merged_handlers

  if (first_handler.pattern[-1], second_handler.pattern[0]) != ('*', '*'):
    return merged_handlers



  first_no_star = first_handler.pattern[:-1]
  merged_handlers.add(SimpleHandler(first_no_star + second_handler.pattern))
  if second_handler.MatchesString(first_no_star):


    merged_handlers.add(SimpleHandler(first_no_star))
  return merged_handlers


def _HandleCommonPrefix(first_handler, second_handler, common_prefix):
  """Strips common literal prefix from handlers and intersects the substrings.

  Ex. "abc" and "a*c" become "a | bc" and "a | *c". We find the set of
  intersections of "bc" and "*c" and prepend "a" onto each member of that set.
  By common literal prefix, we mean a prefix of the two patterns that contains
  no wildcard characters; any string matched by either of the patterns must
  begin with that prefix.

  Args:
    first_handler: A SimpleHandler.
    second_handler: A SimpleHandler.
    common_prefix: The shared literal prefix of the patterns of the two
    handlers.
  Returns:
    The set of intersections of first_handler and second_handler. This is done
    by stripping the common prefix to create new SimpleHandlers which we call
    _IntersectTwoHandlers on, and then prepend the prefix to each member of that
    set.
  """
  stripped_first_handler = SimpleHandler(
      first_handler.pattern[len(common_prefix):], first_handler.properties)
  stripped_second_handler = SimpleHandler(
      second_handler.pattern[len(common_prefix):], second_handler.properties)
  stripped_handlers = _IntersectTwoHandlers(stripped_first_handler,
                                            stripped_second_handler)
  handlers = set()
  for stripped_handler in stripped_handlers:
    handlers.add(SimpleHandler(common_prefix + stripped_handler.pattern,
                               stripped_handler.properties))
  return handlers


def _HandleCommonSuffix(first_handler, second_handler, common_suffix):
  """Strips matching suffix from handlers and intersects the substrings."""

  stripped_first_handler = SimpleHandler(
      first_handler.pattern[:-len(common_suffix)], first_handler.properties)
  stripped_second_handler = SimpleHandler(
      second_handler.pattern[:-len(common_suffix)], second_handler.properties)
  stripped_handlers = _IntersectTwoHandlers(
      stripped_first_handler, stripped_second_handler)
  handlers = set()
  for stripped_handler in stripped_handlers:
    handlers.add(SimpleHandler(stripped_handler.pattern + common_suffix,
                               stripped_handler.properties))
  return handlers


def _SharedPrefix(pattern1, pattern2):
  """Returns the shared prefix of two patterns.

  Args:
    pattern1: A handler's pattern string
    pattern2: A handler's pattern string
  Returns:
    The shared prefix of the two patterns, up to the index of the first
    wildcard of either pattern. For example, the shared prefix of "a*bd" and
    "ac*d" is a. The shared prefix of "*x" and "y" is the empty string. The
    shared prefix of "john" and "johnny" is the empty string, and the shared
    prefix of "bc*" and "c*" is also the empty string.
  """
  first_star1 = (pattern1 + '*').find('*')
  first_star2 = (pattern2 + '*').find('*')
  if (first_star1, first_star2) != (len(pattern1), len(pattern2)):
    min_star = min(first_star1, first_star2)
    if min_star and pattern1[:min_star] == pattern2[:min_star]:
      return pattern1[:min_star]
  return ''


def _SharedSuffix(pattern1, pattern2):
  """Returns the shared suffix of two patterns."""
  return _SharedPrefix(pattern1[::-1], pattern2[::-1])[::-1]
