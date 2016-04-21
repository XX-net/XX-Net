# This module contains abstractions for the input stream. You don't have to
# looks further, there are no pretty code.
#
# We define two classes here.
#
#   Mark(source, line, column)
# It's just a record and its only use is producing nice error messages.
# Parser does not use it for any other purposes.
#
#   Reader(source, data)
# Reader determines the encoding of `data` and converts it to unicode.
# Reader provides the following methods and attributes:
#   reader.peek(length=1) - return the next `length` characters
#   reader.forward(length=1) - move the current position to `length` characters.
#   reader.index - the number of the current character.
#   reader.line, stream.column - the line and the column of the current character.

__all__ = ['Reader', 'ReaderError']

from error import YAMLError, Mark

import codecs, re

# Unfortunately, codec functions in Python 2.3 does not support the `finish`
# arguments, so we have to write our own wrappers.

try:
    codecs.utf_8_decode('', 'strict', False)
    from codecs import utf_8_decode, utf_16_le_decode, utf_16_be_decode

except TypeError:

    def utf_16_le_decode(data, errors, finish=False):
        if not finish and len(data) % 2 == 1:
            data = data[:-1]
        return codecs.utf_16_le_decode(data, errors)

    def utf_16_be_decode(data, errors, finish=False):
        if not finish and len(data) % 2 == 1:
            data = data[:-1]
        return codecs.utf_16_be_decode(data, errors)

    def utf_8_decode(data, errors, finish=False):
        if not finish:
            # We are trying to remove a possible incomplete multibyte character
            # from the suffix of the data.
            # The first byte of a multi-byte sequence is in the range 0xc0 to 0xfd.
            # All further bytes are in the range 0x80 to 0xbf.
            # UTF-8 encoded UCS characters may be up to six bytes long.
            count = 0
            while count < 5 and count < len(data)   \
                    and '\x80' <= data[-count-1] <= '\xBF':
                count -= 1
            if count < 5 and count < len(data)  \
                    and '\xC0' <= data[-count-1] <= '\xFD':
                data = data[:-count-1]
        return codecs.utf_8_decode(data, errors)

class ReaderError(YAMLError):

    def __init__(self, name, position, character, encoding, reason):
        self.name = name
        self.character = character
        self.position = position
        self.encoding = encoding
        self.reason = reason

    def __str__(self):
        if isinstance(self.character, str):
            return "'%s' codec can't decode byte #x%02x: %s\n"  \
                    "  in \"%s\", position %d"    \
                    % (self.encoding, ord(self.character), self.reason,
                            self.name, self.position)
        else:
            return "unacceptable character #x%04x: %s\n"    \
                    "  in \"%s\", position %d"    \
                    % (ord(self.character), self.reason,
                            self.name, self.position)

class Reader(object):
    # Reader:
    # - determines the data encoding and converts it to unicode,
    # - checks if characters are in allowed range,
    # - adds '\0' to the end.

    # Reader accepts
    #  - a `str` object,
    #  - a `unicode` object,
    #  - a file-like object with its `read` method returning `str`,
    #  - a file-like object with its `read` method returning `unicode`.

    # Yeah, it's ugly and slow.

    def __init__(self, stream):
        self.name = None
        self.stream = None
        self.stream_pointer = 0
        self.eof = True
        self.buffer = u''
        self.pointer = 0
        self.raw_buffer = None
        self.raw_decode = None
        self.encoding = None
        self.index = 0
        self.line = 0
        self.column = 0
        if isinstance(stream, unicode):
            self.name = "<unicode string>"
            self.check_printable(stream)
            self.buffer = stream+u'\0'
        elif isinstance(stream, str):
            self.name = "<string>"
            self.raw_buffer = stream
            self.determine_encoding()
        else:
            self.stream = stream
            self.name = getattr(stream, 'name', "<file>")
            self.eof = False
            self.raw_buffer = ''
            self.determine_encoding()

    def peek(self, index=0):
        try:
            return self.buffer[self.pointer+index]
        except IndexError:
            self.update(index+1)
            return self.buffer[self.pointer+index]

    def prefix(self, length=1):
        if self.pointer+length >= len(self.buffer):
            self.update(length)
        return self.buffer[self.pointer:self.pointer+length]

    def forward(self, length=1):
        if self.pointer+length+1 >= len(self.buffer):
            self.update(length+1)
        while length:
            ch = self.buffer[self.pointer]
            self.pointer += 1
            self.index += 1
            if ch in u'\n\x85\u2028\u2029'  \
                    or (ch == u'\r' and self.buffer[self.pointer] != u'\n'):
                self.line += 1
                self.column = 0
            elif ch != u'\uFEFF':
                self.column += 1
            length -= 1

    def get_mark(self):
        if self.stream is None:
            return Mark(self.name, self.index, self.line, self.column,
                    self.buffer, self.pointer)
        else:
            return Mark(self.name, self.index, self.line, self.column,
                    None, None)

    def determine_encoding(self):
        while not self.eof and len(self.raw_buffer) < 2:
            self.update_raw()
        if not isinstance(self.raw_buffer, unicode):
            if self.raw_buffer.startswith(codecs.BOM_UTF16_LE):
                self.raw_decode = utf_16_le_decode
                self.encoding = 'utf-16-le'
            elif self.raw_buffer.startswith(codecs.BOM_UTF16_BE):
                self.raw_decode = utf_16_be_decode
                self.encoding = 'utf-16-be'
            else:
                self.raw_decode = utf_8_decode
                self.encoding = 'utf-8'
        self.update(1)

    NON_PRINTABLE = re.compile(u'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-\uD7FF\uE000-\uFFFD]')
    def check_printable(self, data):
        match = self.NON_PRINTABLE.search(data)
        if match:
            character = match.group()
            position = self.index+(len(self.buffer)-self.pointer)+match.start()
            raise ReaderError(self.name, position, character,
                    'unicode', "special characters are not allowed")

    def update(self, length):
        if self.raw_buffer is None:
            return
        self.buffer = self.buffer[self.pointer:]
        self.pointer = 0
        while len(self.buffer) < length:
            if not self.eof:
                self.update_raw()
            if self.raw_decode is not None:
                try:
                    data, converted = self.raw_decode(self.raw_buffer,
                            'strict', self.eof)
                except UnicodeDecodeError, exc:
                    character = exc.object[exc.start]
                    if self.stream is not None:
                        position = self.stream_pointer-len(self.raw_buffer)+exc.start
                    else:
                        position = exc.start
                    raise ReaderError(self.name, position, character,
                            exc.encoding, exc.reason)
            else:
                data = self.raw_buffer
                converted = len(data)
            self.check_printable(data)
            self.buffer += data
            self.raw_buffer = self.raw_buffer[converted:]
            if self.eof:
                self.buffer += u'\0'
                self.raw_buffer = None
                break

    def update_raw(self, size=1024):
        data = self.stream.read(size)
        if data:
            self.raw_buffer += data
            self.stream_pointer += len(data)
        else:
            self.eof = True

#try:
#    import psyco
#    psyco.bind(Reader)
#except ImportError:
#    pass

