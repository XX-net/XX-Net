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





"""Classes for common kinds, including Contact, Message, and Event.

Most of these kinds are based on the gd namespace "kinds" from GData:

  http://code.google.com/apis/gdata/common-elements.html
"""











import types
import urlparse
from xml.sax import saxutils
from google.appengine.datastore import datastore_pb
from google.appengine.api import datastore
from google.appengine.api import datastore_errors
from google.appengine.api import datastore_types

class GdKind(datastore.Entity):
  """ A base class for gd namespace kinds.

  This class contains common logic for all gd namespace kinds. For example,
  this class translates datastore (app id, kind, key) tuples to tag:
  URIs appropriate for use in <key> tags.
  """

  HEADER = u"""<entry xmlns:gd='http://schemas.google.com/g/2005'>
  <category scheme='http://schemas.google.com/g/2005#kind'
            term='http://schemas.google.com/g/2005#%s' />"""
  FOOTER = u"""
</entry>"""

  _kind_properties = set()
  _contact_properties = set()

  def __init__(self, kind, title, kind_properties, contact_properties=[]):
    """ Ctor.

    title is the name of this particular entity, e.g. Bob Jones or Mom's
    Birthday Party.

    kind_properties is a list of property names that should be included in
    this entity's XML encoding as first-class XML elements, instead of
    <property> elements. 'title' and 'content' are added to kind_properties
    automatically, and may not appear in contact_properties.

    contact_properties is a list of property names that are Keys that point to
    Contact entities, and should be included in this entity's XML encoding as
    <gd:who> elements. If a property name is included in both kind_properties
    and contact_properties, it is treated as a Contact property.

    Args:
    kind: string
    title: string
    kind_properties: list of strings
    contact_properties: list of string
    """
    datastore.Entity.__init__(self, kind)

    if not isinstance(title, types.StringTypes):
      raise datastore_errors.BadValueError(
        'Expected a string for title; received %s (a %s).' %
        (title, datastore_types.typename(title)))
    self['title'] = title
    self['content'] = ''


    self._contact_properties = set(contact_properties)
    assert not self._contact_properties.intersection(self.keys())

    self._kind_properties = set(kind_properties) - self._contact_properties
    self._kind_properties.add('title')
    self._kind_properties.add('content')

  def _KindPropertiesToXml(self):
    """ Convert the properties that are part of this gd kind to XML. For
    testability, the XML elements in the output are sorted alphabetically
    by property name.

    Returns:
    string  # the XML representation of the gd kind properties
    """
    properties = self._kind_properties.intersection(set(self.keys()))

    xml = u''
    for prop in sorted(properties):
      prop_xml = saxutils.quoteattr(prop)[1:-1]

      value = self[prop]
      has_toxml = (hasattr(value, 'ToXml') or
                   isinstance(value, list) and hasattr(value[0], 'ToXml'))

      for val in self._XmlEscapeValues(prop):


        if has_toxml:
          xml += '\n  %s' % val
        else:
          xml += '\n  <%s>%s</%s>' % (prop_xml, val, prop_xml)

    return xml


  def _ContactPropertiesToXml(self):
    """ Convert this kind's Contact properties kind to XML. For testability,
    the XML elements in the output are sorted alphabetically by property name.

    Returns:
    string  # the XML representation of the Contact properties
    """
    properties = self._contact_properties.intersection(set(self.keys()))

    xml = u''
    for prop in sorted(properties):
      values = self[prop]
      if not isinstance(values, list):
        values = [values]

      for value in values:
        assert isinstance(value, datastore_types.Key)
        xml += """
  <gd:who rel="http://schemas.google.com/g/2005#%s.%s>
    <gd:entryLink href="%s" />
  </gd:who>""" % (self.kind().lower(), prop, value.ToTagUri())

    return xml


  def _LeftoverPropertiesToXml(self):
    """ Convert all of this entity's properties that *aren't* part of this gd
    kind to XML.

    Returns:
    string  # the XML representation of the leftover properties
    """
    leftovers = set(self.keys())
    leftovers -= self._kind_properties
    leftovers -= self._contact_properties
    if leftovers:
      return u'\n  ' + '\n  '.join(self._PropertiesToXml(leftovers))
    else:
      return u''

  def ToXml(self):
    """ Returns an XML representation of this entity, as a string.
    """
    xml = GdKind.HEADER % self.kind().lower()
    xml += self._KindPropertiesToXml()
    xml += self._ContactPropertiesToXml()
    xml += self._LeftoverPropertiesToXml()
    xml += GdKind.FOOTER
    return xml


class Message(GdKind):
  """A message, such as an email, a discussion group posting, or a comment.

  Includes the message title, contents, participants, and other properties.

  This is the gd Message kind. See:
  http://code.google.com/apis/gdata/common-elements.html#gdMessageKind

  These properties are meaningful. They are all optional.

  property name  property type    meaning
  -------------------------------------
  title          string         message subject
  content        string         message body
  from           Contact*       sender
  to             Contact*       primary recipient
  cc             Contact*       CC recipient
  bcc            Contact*       BCC recipient
  reply-to       Contact*       intended recipient of replies
  link           Link*          attachment
  category       Category*      tag or label associated with this message
  geoPt          GeoPt*         geographic location the message was posted from
  rating         Rating*        message rating, as defined by the application

  * means this property may be repeated.

  The Contact properties should be Keys of Contact entities. They are
  represented in the XML encoding as linked <gd:who> elements.
  """
  KIND_PROPERTIES = ['title', 'content', 'link', 'category', 'geoPt', 'rating']
  CONTACT_PROPERTIES = ['from', 'to', 'cc', 'bcc', 'reply-to']

  def __init__(self, title, kind='Message'):
    GdKind.__init__(self, kind, title, Message.KIND_PROPERTIES,
                    Message.CONTACT_PROPERTIES)


class Event(GdKind):
  """A calendar event.

  Includes the event title, description, location, organizer, start and end
  time, and other details.

  This is the gd Event kind. See:
  http://code.google.com/apis/gdata/common-elements.html#gdEventKind

  These properties are meaningful. They are all optional.

  property name  property type    meaning
  -------------------------------------
  title          string         event name
  content        string         event description
  author         string         the organizer's name
  where          string*        human-readable location (not a GeoPt)
  startTime      timestamp      start time
  endTime        timestamp      end time
  eventStatus    string         one of the Event.Status values
  link           Link*          page with more information
  category       Category*      tag or label associated with this event
  attendee       Contact*       attendees and other related people

  * means this property may be repeated.

  The Contact properties should be Keys of Contact entities. They are
  represented in the XML encoding as linked <gd:who> elements.
  """
  KIND_PROPERTIES = ['title', 'content', 'author', 'where', 'startTime',
                     'endTime', 'eventStatus', 'link', 'category']
  CONTACT_PROPERTIES = ['attendee']

  class Status:
    CONFIRMED = 'confirmed'
    TENTATIVE = 'tentative'
    CANCELED = 'canceled'

  def __init__(self, title, kind='Event'):
    GdKind.__init__(self, kind, title, Event.KIND_PROPERTIES,
                    Event.CONTACT_PROPERTIES)

  def ToXml(self):
    """ Override GdKind.ToXml() to special-case author, gd:where, gd:when, and
    gd:eventStatus.
    """
    xml = GdKind.HEADER % self.kind().lower()

    self._kind_properties = set(Contact.KIND_PROPERTIES)
    xml += self._KindPropertiesToXml()


    if 'author' in self:
      xml += """
  <author><name>%s</name></author>""" % self['author']


    if 'eventStatus' in self:
      xml += """
  <gd:eventStatus value="http://schemas.google.com/g/2005#event.%s" />""" % (
    self['eventStatus'])


    if 'where' in self:
      lines = ['<gd:where valueString="%s" />' % val
               for val in self._XmlEscapeValues('where')]
      xml += '\n  ' + '\n  '.join(lines)


    iso_format = '%Y-%m-%dT%H:%M:%S'
    xml += '\n  <gd:when'
    for key in ['startTime', 'endTime']:
      if key in self:
        xml += ' %s="%s"' % (key, self[key].isoformat())
    xml += ' />'

    self._kind_properties.update(['author', 'where', 'startTime', 'endTime',
                                  'eventStatus'])
    xml += self._ContactPropertiesToXml()
    xml += self._LeftoverPropertiesToXml()
    xml += GdKind.FOOTER
    return xml


class Contact(GdKind):
  """A contact: a person, a venue such as a club or a restaurant, or an
  organization.

  This is the gd Contact kind. See:
  http://code.google.com/apis/gdata/common-elements.html#gdContactKind

  Most of the information about the contact is in the <gd:contactSection>
  element; see the reference section for that element for details.

  These properties are meaningful. They are all optional.

  property name  property type    meaning
  -------------------------------------
  title          string         contact's name
  content        string         notes
  email          Email*         email address
  geoPt          GeoPt*         geographic location
  im             IM*            IM address
  phoneNumber    Phonenumber*   phone number
  postalAddress  PostalAddress* mailing address
  link           Link*          link to more information
  category       Category*      tag or label associated with this contact

  * means this property may be repeated.
  """
  CONTACT_SECTION_HEADER = """
  <gd:contactSection>"""
  CONTACT_SECTION_FOOTER = """
  </gd:contactSection>"""


  KIND_PROPERTIES = ['title', 'content', 'link', 'category']


  CONTACT_SECTION_PROPERTIES = ['email', 'geoPt', 'im', 'phoneNumber',
                                'postalAddress']

  def __init__(self, title, kind='Contact'):
    GdKind.__init__(self, kind, title, Contact.KIND_PROPERTIES)

  def ToXml(self):
    """ Override GdKind.ToXml() to put some properties inside a
    gd:contactSection.
    """
    xml = GdKind.HEADER % self.kind().lower()


    self._kind_properties = set(Contact.KIND_PROPERTIES)
    xml += self._KindPropertiesToXml()


    xml += Contact.CONTACT_SECTION_HEADER
    self._kind_properties = set(Contact.CONTACT_SECTION_PROPERTIES)
    xml += self._KindPropertiesToXml()
    xml += Contact.CONTACT_SECTION_FOOTER

    self._kind_properties.update(Contact.KIND_PROPERTIES)
    xml += self._LeftoverPropertiesToXml()
    xml += GdKind.FOOTER
    return xml
