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




"""Sends email on behalf of application.

Provides functions for application developers to provide email services
for their applications.  Also provides a few utility methods.
"""











import email
from email import MIMEBase
from email import MIMEMultipart
from email import MIMEText
from email import Parser
import email.header
import logging

from google.appengine.api import api_base_pb
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import mail_service_pb
from google.appengine.api import users
from google.appengine.api.mail_errors import *
from google.appengine.runtime import apiproxy_errors









ERROR_MAP = {
    mail_service_pb.MailServiceError.BAD_REQUEST:
      BadRequestError,

    mail_service_pb.MailServiceError.UNAUTHORIZED_SENDER:
      InvalidSenderError,

    mail_service_pb.MailServiceError.INVALID_ATTACHMENT_TYPE:
      InvalidAttachmentTypeError,

    mail_service_pb.MailServiceError.INVALID_HEADER_NAME:
      InvalidHeaderNameError,
}







EXTENSION_MIME_MAP = {
    'aif': 'audio/x-aiff',
    'aifc': 'audio/x-aiff',
    'aiff': 'audio/x-aiff',
    'asc': 'text/plain',
    'au': 'audio/basic',
    'avi': 'video/x-msvideo',
    'bmp': 'image/x-ms-bmp',
    'css': 'text/css',
    'csv': 'text/csv',
    'doc': 'application/msword',
    'docx': 'application/msword',
    'diff': 'text/plain',
    'flac': 'audio/flac',
    'gif': 'image/gif',
    'gzip': 'application/x-gzip',
    'htm': 'text/html',
    'html': 'text/html',
    'ics': 'text/calendar',
    'jpe': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'kml': 'application/vnd.google-earth.kml+xml',
    'kmz': 'application/vnd.google-earth.kmz',
    'm4a': 'audio/mp4',
    'mid': 'audio/mid',
    'mov': 'video/quicktime',
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'mpe': 'video/mpeg',
    'mpeg': 'video/mpeg',
    'mpg': 'video/mpeg',
    'odp': 'application/vnd.oasis.opendocument.presentation',
    'ods': 'application/vnd.oasis.opendocument.spreadsheet',
    'odt': 'application/vnd.oasis.opendocument.text',
    'oga': 'audio/ogg',
    'ogg': 'audio/ogg',
    'ogv': 'video/ogg',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'pot': 'text/plain',
    'pps': 'application/vnd.ms-powerpoint',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.ms-powerpoint',
    'qt': 'video/quicktime',
    'rmi': 'audio/mid',
    'rss': 'text/rss+xml',
    'snd': 'audio/basic',
    'sxc': 'application/vnd.sun.xml.calc',
    'sxw': 'application/vnd.sun.xml.writer',
    'text': 'text/plain',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',
    'txt': 'text/plain',
    'vcf': 'text/directory',
    'wav': 'audio/x-wav',
    'wbmp': 'image/vnd.wap.wbmp',
    'webm': 'video/webm',
    'webp': 'image/webp',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.ms-excel',
    'zip': 'application/zip'
    }





EXTENSION_BLACKLIST = [
    'ade',
    'adp',
    'bat',
    'chm',
    'cmd',
    'com',
    'cpl',
    'exe',
    'hta',
    'ins',
    'isp',
    'jse',
    'lib',
    'mde',
    'msc',
    'msp',
    'mst',
    'pif',
    'scr',
    'sct',
    'shb',
    'sys',
    'vb',
    'vbe',
    'vbs',
    'vxd',
    'wsc',
    'wsf',
    'wsh',
    ]


HEADER_WHITELIST = frozenset([
    'Auto-Submitted',
    'In-Reply-To',
    'List-Id',
    'List-Unsubscribe',
    'On-Behalf-Of',
    'References',
    'Resent-Date',
    'Resent-From',
    'Resent-To',
    ])


def invalid_email_reason(email_address, field):
  """Determine reason why email is invalid.

  Args:
    email_address: Email to check.
    field: Field that is invalid.

  Returns:
    String indicating invalid email reason if there is one,
    else None.
  """
  if email_address is None:
    return 'None email address for %s.' % field

  if isinstance(email_address, users.User):
    email_address = email_address.email()
  if not isinstance(email_address, basestring):
    return 'Invalid email address type for %s.' % field
  stripped_address = email_address.strip()
  if not stripped_address:
    return 'Empty email address for %s.' % field
  return None


InvalidEmailReason = invalid_email_reason


def is_email_valid(email_address):
  """Determine if email is invalid.

  Args:
    email_address: Email to check.

  Returns:
    True if email is valid, else False.
  """
  return invalid_email_reason(email_address, '') is None


IsEmailValid = is_email_valid


def check_email_valid(email_address, field):
  """Check that email is valid.

  Args:
    email_address: Email to check.
    field: Field to check.

  Raises:
    InvalidEmailError if email_address is invalid.
  """
  reason = invalid_email_reason(email_address, field)
  if reason is not None:
    raise InvalidEmailError(reason)


CheckEmailValid = check_email_valid


def is_ascii(string):
  """Return whether a string is in ascii."""
  return all(ord(c) < 128 for c in string)


def invalid_headers_reason(headers):
  """Determine reason why headers is invalid.

  Args:
    headers: headers value to check.

  Returns:
    String indicating invalid headers reason if there is one,
    else None.
  """
  if headers is None:
    return 'Headers dictionary was None.'
  if not isinstance(headers, dict):
    return 'Invalid type for headers. Should be a dictionary.'
  for k, v in headers.iteritems():
    if not isinstance(k, basestring):
      return 'Header names should be strings.'
    if not isinstance(v, basestring):
      return 'Header values should be strings.'
    if not is_ascii(k):
      return 'Header name should be an ASCII string.'

    if k.strip() not in HEADER_WHITELIST:
      return 'Header "%s" is not allowed.' % k.strip()


def check_headers_valid(headers):
  """Check that headers is a valid dictionary for headers.

  Args:
    headers: the value to check for the headers.

  Raises:
    InvalidEmailError if headers is invalid.
  """
  reason = invalid_headers_reason(headers)
  if reason is not None:
    raise InvalidEmailError(reason)


def _email_sequence(emails):
  """Forces email to be sequenceable type.

  Iterable values are returned as is.  This function really just wraps the case
  where there is a single email string.

  Args:
    emails: Emails (or email) to coerce to sequence.

  Returns:
    Single tuple with email in it if only one email string provided,
    else returns emails as is.
  """
  if isinstance(emails, basestring):
    return emails,
  return emails


def _attachment_sequence(attachments):
  """Forces attachments to be sequenceable type.

  Iterable values are returned as is.  This function really just wraps the case
  where there is a single attachment.

  Args:
    attachments: Attachments (or attachment) to coerce to sequence.

  Returns:
    Single tuple with attachment tuple in it if only one attachment provided,
    else returns attachments as is.
  """
  if len(attachments) == 2 and isinstance(attachments[0], basestring):
    attachments = attachments,
  for attachment in attachments:
    if isinstance(attachment, Attachment):
      yield attachment
    else:
      yield Attachment(*attachment)

def _parse_mime_message(mime_message):
  """Helper function converts a mime_message in to email.Message.Message.

  Args:
    mime_message: MIME Message, string or file containing mime message.

  Returns:
    Instance of email.Message.Message.  Will return mime_message if already
    an instance.
  """
  if isinstance(mime_message, email.Message.Message):
    return mime_message
  elif isinstance(mime_message, basestring):
    return email.message_from_string(mime_message)
  else:

    return email.message_from_file(mime_message)


def send_mail(sender,
              to,
              subject,
              body,
              make_sync_call=apiproxy_stub_map.MakeSyncCall,
              **kw):
  """Sends mail on behalf of application.

  Args:
    sender: Sender email address as appears in the 'from' email line.
    to: List of 'to' addresses or a single address.
    subject: Message subject string.
    body: Body of type text/plain.
    make_sync_call: Function used to make sync call to API proxy.
    kw: Keyword arguments compatible with EmailMessage keyword based
      constructor.

  Raises:
    InvalidEmailError when invalid email address provided.
  """
  kw['sender'] = sender
  kw['to'] = to
  kw['subject'] = subject
  kw['body'] = body
  message = EmailMessage(**kw)
  message.send(make_sync_call=make_sync_call)


SendMail = send_mail


def send_mail_to_admins(sender,
                        subject,
                        body,
                        make_sync_call=apiproxy_stub_map.MakeSyncCall,
                        **kw):
  """Sends mail to admins on behalf of application.

  Args:
    sender: Sender email address as appears in the 'from' email line.
    subject: Message subject string.
    body: Body of type text/plain.
    make_sync_call: Function used to make sync call to API proxy.
    kw: Keyword arguments compatible with EmailMessage keyword based
      constructor.

  Raises:
    InvalidEmailError when invalid email address provided.
  """
  kw['sender'] = sender
  kw['subject'] = subject
  kw['body'] = body
  message = AdminEmailMessage(**kw)
  message.send(make_sync_call=make_sync_call)


SendMailToAdmins = send_mail_to_admins


def _GetMimeType(file_name):
  """Determine mime-type from file name.

  Parses file name and determines mime-type based on extension map.

  This method is not part of the public API and should not be used by
  applications.

  Args:
    file_name: File to determine extension for.

  Returns:
    Mime-type associated with file extension.

  Raises:
    InvalidAttachmentTypeError when the file name of an attachment.
  """
  extension_index = file_name.rfind('.')
  if extension_index == -1:
    extension = ''
  else:
    extension = file_name[extension_index + 1:].lower()
  if extension in EXTENSION_BLACKLIST:
    raise InvalidAttachmentTypeError(
        'Extension %s is not supported.' % extension)
  mime_type = EXTENSION_MIME_MAP.get(extension, None)
  if mime_type is None:
    mime_type = 'application/octet-stream'
  return mime_type


def _GuessCharset(text):
  """Guess the charset of a text.

  Args:
    text: a string (str) that is either a us-ascii string or a unicode that was
        encoded in utf-8.
  Returns:
    Charset needed by the string, either 'us-ascii' or 'utf-8'.
  """
  try:
    text.decode('us-ascii')
    return 'us-ascii'
  except UnicodeDecodeError:
    return 'utf-8'


def _I18nHeader(text):
  """Creates a header properly encoded even with unicode content.

  Args:
    text: a string (str) that is either a us-ascii string or a unicode that was
        encoded in utf-8.
  Returns:
    email.header.Header
  """
  charset = _GuessCharset(text)
  return email.header.Header(text, charset, maxlinelen=1e3000)


def mail_message_to_mime_message(protocol_message):
  """Generate a MIMEMultitype message from protocol buffer.

  Generates a complete MIME multi-part email object from a MailMessage
  protocol buffer.  The body fields are sent as individual alternatives
  if they are both present, otherwise, only one body part is sent.

  Multiple entry email fields such as 'To', 'Cc' and 'Bcc' are converted
  to a list of comma separated email addresses.

  Args:
    protocol_message: Message PB to convert to MIMEMultitype.

  Returns:
    MIMEMultitype representing the provided MailMessage.

  Raises:
    InvalidAttachmentTypeError when the file name of an attachment
  """
  parts = []
  if protocol_message.has_textbody():
    parts.append(MIMEText.MIMEText(
        protocol_message.textbody(),
        _charset=_GuessCharset(protocol_message.textbody())))
  if protocol_message.has_htmlbody():
    parts.append(MIMEText.MIMEText(
        protocol_message.htmlbody(), _subtype='html',
        _charset=_GuessCharset(protocol_message.htmlbody())))

  if len(parts) == 1:

    payload = parts
  else:

    payload = [MIMEMultipart.MIMEMultipart('alternative', _subparts=parts)]

  result = MIMEMultipart.MIMEMultipart(_subparts=payload)

  for attachment in protocol_message.attachment_list():
    file_name = attachment.filename()
    mime_type = _GetMimeType(file_name)
    maintype, subtype = mime_type.split('/')
    mime_attachment = MIMEBase.MIMEBase(maintype, subtype)
    mime_attachment.add_header('Content-Disposition',
                               'attachment',
                               filename=attachment.filename())
    mime_attachment.set_payload(attachment.data())
    if attachment.has_contentid():
      mime_attachment['content-id'] = attachment.contentid()
    result.attach(mime_attachment)


  if protocol_message.to_size():
    result['To'] = _I18nHeader(', '.join(protocol_message.to_list()))
  if protocol_message.cc_size():
    result['Cc'] = _I18nHeader(', '.join(protocol_message.cc_list()))
  if protocol_message.bcc_size():
    result['Bcc'] = _I18nHeader(', '.join(protocol_message.bcc_list()))

  result['From'] = _I18nHeader(protocol_message.sender())
  result['Reply-To'] = _I18nHeader(protocol_message.replyto())
  result['Subject'] = _I18nHeader(protocol_message.subject())

  for header in protocol_message.header_list():
    result[header.name()] = _I18nHeader(header.value())

  return result


MailMessageToMIMEMessage = mail_message_to_mime_message


def _to_str(value):
  """Helper function to make sure unicode values converted to utf-8.

  Args:
    value: str or unicode to convert to utf-8.

  Returns:
    UTF-8 encoded str of value, otherwise value unchanged.
  """
  if isinstance(value, unicode):
    return value.encode('utf-8')
  return value


def _decode_and_join_header(header, separator=u' '):
  """Helper function to decode RFC2047 encoded headers.

  Args:
    header: RFC2047 encoded str (or just a plain old str) to convert to unicode.
    separator: The separator to use when joining separately encoded pieces of
        the header.

  Returns:
    unicode of decoded header or just header if it was None or ''.
  """
  if not header:

    return header
  return separator.join(s.decode(charset or 'us-ascii', 'replace')
                        for s, charset in email.header.decode_header(header))


def _decode_address_list_field(address_list):
  """Helper function to decode (potentially RFC2047 encoded) address lists.

  Args:
    address_list: a single str header, or list of str headers.

  Returns:
    unicode of decoded header or list of str headers.
  """
  if not address_list:
    return None

  if len(address_list) == 1:
    return _decode_and_join_header(address_list[0])
  else:
    return map(_decode_and_join_header, address_list)



def wrapping(wrapped):




  def wrapping_wrapper(wrapper):
    try:
      wrapper.__wrapped__ = wrapped
      wrapper.__name__ = wrapped.__name__
      wrapper.__doc__ = wrapped.__doc__
      wrapper.__dict__.update(wrapped.__dict__)
    except Exception:
      pass
    return wrapper
  return wrapping_wrapper



def _positional(max_pos_args):
  """A decorator to declare that only the first N arguments may be positional.

  Note that for methods, n includes 'self'.
  """
  def positional_decorator(wrapped):
    @wrapping(wrapped)
    def positional_wrapper(*args, **kwds):
      if len(args) > max_pos_args:
        plural_s = ''
        if max_pos_args != 1:
          plural_s = 's'
        raise TypeError(
            '%s() takes at most %d positional argument%s (%d given)' %
            (wrapped.__name__, max_pos_args, plural_s, len(args)))
      return wrapped(*args, **kwds)
    return positional_wrapper
  return positional_decorator


class Attachment(object):
  """Attachment object.

  An Attachment object is largely interchangeable with a (filename, payload)
  tuple.

  Note that the behavior is a bit asymmetric with respect to unpacking and
  equality comparison. An Attachment object without a content ID will be
  equivalent to a (filename, payload) tuple. An Attachment with a content ID
  will unpack to a (filename, payload) tuple, but will compare unequally to
  that tuple.

  Thus, the following comparison will succeed:

      attachment = mail.Attachment('foo.jpg', 'data')
      filename, payload = attachment
      attachment == filename, payload

  ...while the following will fail:

      attachment = mail.Attachment('foo.jpg', 'data', content_id='<foo>')
      filename, payload = attachment
      attachment == filename, payload

   The following comparison will pass though:

      attachment = mail.Attachment('foo.jpg', 'data', content_id='<foo>')
      attachment == (attachment.filename,
                     attachment.payload,
                     attachment.content_id)

  Attributes:
    filename: The name of the attachment.
    payload: The attachment data.
    content_id: Optional. The content-id for this attachment. Keyword-only.
  """

  @_positional(3)
  def __init__(self, filename, payload, content_id=None):
    """Constructor.

    Arguments:
      filename: The name of the attachment
      payload: The attachment data.
      content_id: Optional. The content-id for this attachment.
    """
    self.filename = filename
    self.payload = payload
    self.content_id = content_id

  def __eq__(self, other):
    self_tuple = (self.filename, self.payload, self.content_id)
    if isinstance(other, Attachment):
      other_tuple = (other.filename, other.payload, other.content_id)


    elif not hasattr(other, '__len__'):
      return NotImplemented
    elif len(other) == 2:
      other_tuple = other + (None,)
    elif len(other) == 3:
      other_tuple = other
    else:
      return NotImplemented
    return self_tuple == other_tuple

  def __hash__(self):
    if self.content_id:
      return hash((self.filename, self.payload, self.content_id))
    else:
      return hash((self.filename, self.payload))

  def __ne__(self, other):
    return not self == other

  def __iter__(self):
    return iter((self.filename, self.payload))

  def __getitem__(self, i):
    return tuple(iter(self))[i]

  def __contains__(self, val):
    return val in (self.filename, self.payload)

  def __len__(self):
    return 2


class EncodedPayload(object):
  """Wrapper for a payload that contains encoding information.

  When an email is received, it is usually encoded using a certain
  character set, and then possibly further encoded using a transfer
  encoding in that character set.  Most of the times, it is possible
  to decode the encoded payload as is, however, in the case where it
  is not, the encoded payload and the original encoding information
  must be preserved.

  Attributes:
    payload: The original encoded payload.
    charset: The character set of the encoded payload.  None means use
      default character set.
    encoding: The transfer encoding of the encoded payload.  None means
      content not encoded.
  """

  def __init__(self, payload, charset=None, encoding=None):
    """Constructor.

    Args:
      payload: Maps to attribute of the same name.
      charset: Maps to attribute of the same name.
      encoding: Maps to attribute of the same name.
    """
    self.payload = payload
    self.charset = charset
    self.encoding = encoding

  def decode(self):
    """Attempt to decode the encoded data.

    Attempt to use pythons codec library to decode the payload.  All
    exceptions are passed back to the caller.

    Returns:
      Binary or unicode version of payload content.
    """
    payload = self.payload


    if self.encoding and self.encoding.lower() not in ('7bit', '8bit'):
      try:
        payload = payload.decode(self.encoding)
      except LookupError:
        raise UnknownEncodingError('Unknown decoding %s.' % self.encoding)
      except (Exception, Error), e:
        raise PayloadEncodingError('Could not decode payload: %s' % e)


    if self.charset and str(self.charset).lower() != '7bit':
      try:
        payload = payload.decode(str(self.charset))
      except LookupError:
        raise UnknownCharsetError('Unknown charset %s.' % self.charset)
      except (Exception, Error), e:
        raise PayloadEncodingError('Could read characters: %s' % e)

    return payload

  def __eq__(self, other):
    """Equality operator.

    Args:
      other: The other EncodedPayload object to compare with.  Comparison
        with other object types are not implemented.

    Returns:
      True of payload and encodings are equal, else false.
    """
    if isinstance(other, EncodedPayload):
      return (self.payload == other.payload and
              self.charset == other.charset and
              self.encoding == other.encoding)
    else:
      return NotImplemented

  def __hash__(self):
    """Hash an EncodedPayload."""
    return hash((self.payload, self.charset, self.encoding))

  def copy_to(self, mime_message):
    """Copy contents to MIME message payload.

    If no content transfer encoding is specified, and the character set does
    not equal the over-all message encoding, the payload will be base64
    encoded.

    Args:
      mime_message: Message instance to receive new payload.
    """
    if self.encoding:
      mime_message['content-transfer-encoding'] = self.encoding
    mime_message.set_payload(self.payload, self.charset)

  def to_mime_message(self):
    """Convert to MIME message.

    Returns:
      MIME message instance of payload.
    """
    mime_message = email.Message.Message()
    self.copy_to(mime_message)
    return mime_message

  def __str__(self):
    """String representation of encoded message.

    Returns:
      MIME encoded representation of encoded payload as an independent message.
    """
    return str(self.to_mime_message())

  def __repr__(self):
    """Basic representation of encoded payload.

    Returns:
      Payload itself is represented by its hash value.
    """
    result = '<EncodedPayload payload=#%d' % hash(self.payload)
    if self.charset:
      result += ' charset=%s' % self.charset
    if self.encoding:
      result += ' encoding=%s' % self.encoding
    return result + '>'


class _EmailMessageBase(object):
  """Base class for email API service objects.

  Subclasses must define a class variable called _API_CALL with the name
  of its underlying mail sending API call.
  """


  PROPERTIES = set([
      'sender',
      'reply_to',
      'subject',
      'body',
      'html',
      'attachments',
  ])

  ALLOWED_EMPTY_PROPERTIES = set([
      'subject',
      'body'
  ])



  PROPERTIES.update(('to', 'cc', 'bcc'))

  def __init__(self, mime_message=None, **kw):
    """Initialize Email message.

    Creates new MailMessage protocol buffer and initializes it with any
    keyword arguments.

    Args:
      mime_message: MIME message to initialize from.  If instance of
        email.Message.Message will take ownership as original message.
      kw: List of keyword properties as defined by PROPERTIES.
    """
    if mime_message:
      mime_message = _parse_mime_message(mime_message)
      self.update_from_mime_message(mime_message)
      self.__original = mime_message



    self.initialize(**kw)

  @property
  def original(self):
    """Get original MIME message from which values were set."""
    return self.__original

  def initialize(self, **kw):
    """Keyword initialization.

    Used to set all fields of the email message using keyword arguments.

    Args:
      kw: List of keyword properties as defined by PROPERTIES.
    """
    for name, value in kw.iteritems():
      setattr(self, name, value)


  def Initialize(self, **kw):
    self.initialize(**kw)

  def check_initialized(self):
    """Check if EmailMessage is properly initialized.

    Test used to determine if EmailMessage meets basic requirements
    for being used with the mail API.  This means that the following
    fields must be set or have at least one value in the case of
    multi value fields:

      - Subject must be set.
      - A recipient must be specified.
      - Must contain a body.
      - All bodies and attachments must decode properly.

    This check does not include determining if the sender is actually
    authorized to send email for the application.

    Raises:
      Appropriate exception for initialization failure.

        InvalidAttachmentTypeError: Use of incorrect attachment type.
        MissingRecipientsError:     No recipients specified in to, cc or bcc.
        MissingSenderError:         No sender specified.
        MissingSubjectError:        Subject is not specified.
        MissingBodyError:           No body specified.
        PayloadEncodingError:       Payload is not properly encoded.
        UnknownEncodingError:       Payload has unknown encoding.
        UnknownCharsetError:        Payload has unknown character set.
    """
    if not hasattr(self, 'sender'):
      raise MissingSenderError()


    found_body = False

    try:
      body = self.body
    except AttributeError:
      pass
    else:
      if isinstance(body, EncodedPayload):

        body.decode()
      found_body = True

    try:
      html = self.html
    except AttributeError:
      pass
    else:
      if isinstance(html, EncodedPayload):

        html.decode()
      found_body = True

    if hasattr(self, 'attachments'):
      for attachment in _attachment_sequence(self.attachments):


        _GetMimeType(attachment.filename)




        if isinstance(attachment.payload, EncodedPayload):
          attachment.payload.decode()


  def CheckInitialized(self):
    self.check_initialized()

  def is_initialized(self):
    """Determine if EmailMessage is properly initialized.

    Returns:
      True if message is properly initializes, otherwise False.
    """
    try:
      self.check_initialized()
      return True
    except Error:
      return False


  def IsInitialized(self):
    return self.is_initialized()

  def ToProto(self):
    """Convert mail message to protocol message.

    Unicode strings are converted to UTF-8 for all fields.

    This method is overriden by EmailMessage to support the sender fields.

    Returns:
      MailMessage protocol version of mail message.

    Raises:
      Passes through decoding errors that occur when using when decoding
      EncodedPayload objects.
    """
    self.check_initialized()
    message = mail_service_pb.MailMessage()
    message.set_sender(_to_str(self.sender))

    if hasattr(self, 'reply_to'):
      message.set_replyto(_to_str(self.reply_to))
    if hasattr(self, 'subject'):
      message.set_subject(_to_str(self.subject))
    else:
      message.set_subject('')

    if hasattr(self, 'body'):
      body = self.body
      if isinstance(body, EncodedPayload):
        body = body.decode()
      message.set_textbody(_to_str(body))

    if hasattr(self, 'html'):
      html = self.html
      if isinstance(html, EncodedPayload):
        html = html.decode()
      message.set_htmlbody(_to_str(html))

    if hasattr(self, 'attachments'):
      for attachment in _attachment_sequence(self.attachments):
        if isinstance(attachment.payload, EncodedPayload):
          attachment.payload = attachment.payload.decode()
        protoattachment = message.add_attachment()
        protoattachment.set_filename(_to_str(attachment.filename))
        protoattachment.set_data(_to_str(attachment.payload))
        if attachment.content_id:
          protoattachment.set_contentid(attachment.content_id)
    return message

  def to_mime_message(self):
    """Generate a MIMEMultitype message from EmailMessage.

    Calls MailMessageToMessage after converting self to protocol
    buffer.  Protocol buffer is better at handing corner cases
    than EmailMessage class.

    Returns:
      MIMEMultitype representing the provided MailMessage.

    Raises:
      Appropriate exception for initialization failure.

      InvalidAttachmentTypeError: Use of incorrect attachment type.
      MissingSenderError:         No sender specified.
      MissingSubjectError:        Subject is not specified.
      MissingBodyError:           No body specified.
    """
    return mail_message_to_mime_message(self.ToProto())


  def ToMIMEMessage(self):
    return self.to_mime_message()

  def send(self, make_sync_call=apiproxy_stub_map.MakeSyncCall):
    """Send email message.

    Send properly initialized email message via email API.

    Args:
      make_sync_call: Method which will make synchronous call to api proxy.

    Raises:
      Errors defined in this file above.
    """
    message = self.ToProto()
    response = api_base_pb.VoidProto()

    try:
      make_sync_call('mail', self._API_CALL, message, response)
    except apiproxy_errors.ApplicationError, e:
      if e.application_error in ERROR_MAP:
        raise ERROR_MAP[e.application_error](e.error_detail)
      raise e


  def Send(self, *args, **kwds):
    self.send(*args, **kwds)

  def _check_attachment(self, attachment):

    if not (isinstance(attachment.filename, basestring) or
            isinstance(attachment.payload, basestring)):
      raise TypeError()

  def _check_attachments(self, attachments):
    """Checks values going to attachment field.

    Mainly used to check type safety of the values.  Each value of the list
    must be a pair of the form (file_name, data), and both values a string
    type.

    Args:
      attachments: Collection of attachment tuples.

    Raises:
      TypeError if values are not string type.
    """
    attachments = _attachment_sequence(attachments)
    for attachment in attachments:
      self._check_attachment(attachment)

  def __setattr__(self, attr, value):
    """Property setting access control.

    Controls write access to email fields.

    Args:
      attr: Attribute to access.
      value: New value for field.

    Raises:
      ValueError: If provided with an empty field.
      AttributeError: If not an allowed assignment field.
    """
    if not attr.startswith('_EmailMessageBase'):
      if attr in ['sender', 'reply_to']:
        check_email_valid(value, attr)

      if not value and not attr in self.ALLOWED_EMPTY_PROPERTIES:
        raise ValueError('May not set empty value for \'%s\'' % attr)


      if attr not in self.PROPERTIES:
        raise AttributeError('\'EmailMessage\' has no attribute \'%s\'' % attr)


      if attr == 'attachments':
        self._check_attachments(value)

    super(_EmailMessageBase, self).__setattr__(attr, value)

  def _add_body(self, content_type, payload):
    """Add body to email from payload.

    Will overwrite any existing default plain or html body.

    Args:
      content_type: Content-type of body.
      payload: Payload to store body as.
    """

    if content_type == 'text/plain':
      self.body = payload
    elif content_type == 'text/html':
      self.html = payload

  def _update_payload(self, mime_message):
    """Update payload of mail message from mime_message.

    This function works recusively when it receives a multipart body.
    If it receives a non-multi mime object, it will determine whether or
    not it is an attachment by whether it has a filename or not.  Attachments
    and bodies are then wrapped in EncodedPayload with the correct charsets and
    encodings.

    Args:
      mime_message: A Message MIME email object.
    """
    payload = mime_message.get_payload()

    if payload:
      if mime_message.get_content_maintype() == 'multipart':
        for alternative in payload:
          self._update_payload(alternative)
      else:
        filename = mime_message.get_param('filename',
                                          header='content-disposition')
        if filename:

          filename = email.utils.collapse_rfc2231_value(filename)
        if not filename:
          filename = mime_message.get_param('name')


        payload = EncodedPayload(payload,
                                 (mime_message.get_content_charset() or
                                  mime_message.get_charset()),
                                 mime_message['content-transfer-encoding'])

        if 'content-id' in mime_message:
          attachment = Attachment(filename,
                                  payload,
                                  content_id=mime_message['content-id'])
        else:
          attachment = Attachment(filename, payload)

        if filename:

          try:
            attachments = self.attachments
          except AttributeError:
            self.attachments = [attachment]
          else:
            if isinstance(attachments[0], basestring):
              self.attachments = [attachments]
              attachments = self.attachments
            attachments.append(attachment)
        else:
          self._add_body(mime_message.get_content_type(), payload)

  def update_from_mime_message(self, mime_message):
    """Copy information from a mime message.

    Set information of instance to values of mime message.  This method
    will only copy values that it finds.  Any missing values will not
    be copied, nor will they overwrite old values with blank values.

    This object is not guaranteed to be initialized after this call.

    Args:
      mime_message: email.Message instance to copy information from.

    Returns:
      MIME Message instance of mime_message argument.
    """
    mime_message = _parse_mime_message(mime_message)

    sender = _decode_and_join_header(mime_message['from'])
    if sender:
      self.sender = sender

    reply_to = _decode_and_join_header(mime_message['reply-to'])
    if reply_to:
      self.reply_to = reply_to

    subject = _decode_and_join_header(mime_message['subject'], separator=u'')
    if subject:
      self.subject = subject

    self._update_payload(mime_message)

  def bodies(self, content_type=None):
    """Iterate over all bodies.

    Yields:
      Tuple (content_type, payload) for html and body in that order.
    """
    if (not content_type or
        content_type == 'text' or
        content_type == 'text/html'):
      try:
        yield 'text/html', self.html
      except AttributeError:
        pass

    if (not content_type or
        content_type == 'text' or
        content_type == 'text/plain'):
      try:
        yield 'text/plain', self.body
      except AttributeError:
        pass


class EmailMessage(_EmailMessageBase):
  """Main interface to email API service.

  This class is used to programmatically build an email message to send via
  the Mail API.  The usage is to construct an instance, populate its fields
  and call Send().

  Example Usage:
    An EmailMessage can be built completely by the constructor.

      EmailMessage(sender='sender@nowhere.com',
                   to='recipient@nowhere.com',
                   subject='a subject',
                   body='This is an email to you').Send()

    It might be desirable for an application to build an email in different
    places throughout the code.  For this, EmailMessage is mutable.

      message = EmailMessage()
      message.sender = 'sender@nowhere.com'
      message.to = ['recipient1@nowhere.com', 'recipient2@nowhere.com']
      message.subject = 'a subject'
      message.body = 'This is an email to you')
      message.check_initialized()
      message.send()
  """

  _API_CALL = 'Send'
  PROPERTIES = set(_EmailMessageBase.PROPERTIES | set(('headers',)))

  def check_initialized(self):
    """Provide additional checks to ensure recipients have been specified.

    Raises:
      MissingRecipientError when no recipients specified in to, cc or bcc.
    """
    if (not hasattr(self, 'to') and
        not hasattr(self, 'cc') and
        not hasattr(self, 'bcc')):
      raise MissingRecipientsError()
    super(EmailMessage, self).check_initialized()


  def CheckInitialized(self):
    self.check_initialized()

  def ToProto(self):
    """Does addition conversion of recipient fields to protocol buffer.

    Returns:
      MailMessage protocol version of mail message including sender fields.
    """
    message = super(EmailMessage, self).ToProto()

    for attribute, adder in (('to', message.add_to),
                             ('cc', message.add_cc),
                             ('bcc', message.add_bcc)):
      if hasattr(self, attribute):
        for address in _email_sequence(getattr(self, attribute)):
          adder(_to_str(address))
    for name, value in getattr(self, 'headers', {}).iteritems():
      header = message.add_header()
      header.set_name(name)
      header.set_value(_to_str(value))
    return message

  def __setattr__(self, attr, value):
    """Provides additional checks on recipient fields."""

    if attr in ['to', 'cc', 'bcc']:
      if isinstance(value, basestring):
        if value == '' and getattr(self, 'ALLOW_BLANK_EMAIL', False):
          return
        check_email_valid(value, attr)
      else:
        for address in value:
          check_email_valid(address, attr)
    elif attr == 'headers':
      check_headers_valid(value)

    super(EmailMessage, self).__setattr__(attr, value)

  def update_from_mime_message(self, mime_message):
    """Copy information from a mime message.

    Update fields for recipients.

    Args:
      mime_message: email.Message instance to copy information from.
    """
    mime_message = _parse_mime_message(mime_message)
    super(EmailMessage, self).update_from_mime_message(mime_message)

    to = _decode_address_list_field(mime_message.get_all('to'))
    if to:
      self.to = to

    cc = _decode_address_list_field(mime_message.get_all('cc'))
    if cc:
      self.cc = cc

    bcc = _decode_address_list_field(mime_message.get_all('bcc'))
    if bcc:
      self.bcc = bcc


class AdminEmailMessage(_EmailMessageBase):
  """Interface to sending email messages to all admins via the mail API.

  This class is used to programmatically build an admin email message to send
  via the Mail API.  The usage is to construct an instance, populate its fields
  and call Send().

  Unlike the normal email message, addresses in the recipient fields are
  ignored and not used for sending.

  Example Usage:
    An AdminEmailMessage can be built completely by the constructor.

      AdminEmailMessage(sender='sender@nowhere.com',
                        subject='a subject',
                        body='This is an email to you').Send()

    It might be desirable for an application to build an admin email in
    different places throughout the code.  For this, AdminEmailMessage is
    mutable.

      message = AdminEmailMessage()
      message.sender = 'sender@nowhere.com'
      message.subject = 'a subject'
      message.body = 'This is an email to you')
      message.check_initialized()
      message.send()
  """

  _API_CALL = 'SendToAdmins'
  __UNUSED_PROPERTIES = set(('to', 'cc', 'bcc'))

  def __setattr__(self, attr, value):
    if attr in self.__UNUSED_PROPERTIES:
      logging.warning('\'%s\' is not a valid property to set '
                      'for AdminEmailMessage.  It is unused.', attr)
    super(AdminEmailMessage, self).__setattr__(attr, value)


class InboundEmailMessage(EmailMessage):
  """Parsed email object as recevied from external source.

  Has a date field and can store any number of additional bodies.  These
  additional attributes make the email more flexible as required for
  incoming mail, where the developer has less control over the content.

  Example Usage:

    # Read mail message from CGI input.
    message = InboundEmailMessage(sys.stdin.read())
    logging.info('Received email message from %s at %s',
                 message.sender,
                 message.date)
    enriched_body = list(message.bodies('text/enriched'))[0]
    ... Do something with body ...
  """

  __HEADER_PROPERTIES = {'date': 'date',
                         'message_id': 'message-id',
                        }

  PROPERTIES = frozenset(_EmailMessageBase.PROPERTIES |
                         set(('alternate_bodies',)) |
                         set(__HEADER_PROPERTIES.iterkeys()))

  ALLOW_BLANK_EMAIL = True

  def update_from_mime_message(self, mime_message):
    """Update values from MIME message.

    Copies over date values.

    Args:
      mime_message: email.Message instance to copy information from.
    """
    mime_message = _parse_mime_message(mime_message)
    super(InboundEmailMessage, self).update_from_mime_message(mime_message)

    for property, header in InboundEmailMessage.__HEADER_PROPERTIES.iteritems():
      value = mime_message[header]
      if value:
        setattr(self, property, value)

  def _add_body(self, content_type, payload):
    """Add body to inbound message.

    Method is overidden to handle incoming messages that have more than one
    plain or html bodies or has any unidentified bodies.

    This method will not overwrite existing html and body values.  This means
    that when updating, the text and html bodies that are first in the MIME
    document order are assigned to the body and html properties.

    Args:
      content_type: Content-type of additional body.
      payload: Content of additional body.
    """
    if (content_type == 'text/plain' and not hasattr(self, 'body') or
        content_type == 'text/html' and not hasattr(self, 'html')):

      super(InboundEmailMessage, self)._add_body(content_type, payload)
    else:

      try:
        alternate_bodies = self.alternate_bodies
      except AttributeError:
        alternate_bodies = self.alternate_bodies = [(content_type, payload)]
      else:
        alternate_bodies.append((content_type, payload))

  def bodies(self, content_type=None):
    """Iterate over all bodies.

    Args:
      content_type: Content type to filter on.  Allows selection of only
        specific types of content.  Can be just the base type of the content
        type.  For example:
          content_type = 'text/html'  # Matches only HTML content.
          content_type = 'text'       # Matches text of any kind.

    Yields:
      Tuple (content_type, payload) for all bodies of message, including body,
      html and all alternate_bodies in that order.
    """
    main_bodies = super(InboundEmailMessage, self).bodies(content_type)
    for payload_type, payload in main_bodies:
      yield payload_type, payload

    partial_type = bool(content_type and content_type.find('/') < 0)

    try:
      for payload_type, payload in self.alternate_bodies:
        if content_type:
          if partial_type:
            match_type = payload_type.split('/')[0]
          else:
            match_type = payload_type
          match = match_type == content_type
        else:
          match = True

        if match:
          yield payload_type, payload
    except AttributeError:
      pass

  def to_mime_message(self):
    """Convert to MIME message.

    Adds additional headers from inbound email.

    Returns:
      MIME message instance of payload.
    """
    mime_message = super(InboundEmailMessage, self).to_mime_message()

    for property, header in InboundEmailMessage.__HEADER_PROPERTIES.iteritems():
      try:
        mime_message[header] = getattr(self, property)
      except AttributeError:
        pass

    return mime_message










Parser.Parser

