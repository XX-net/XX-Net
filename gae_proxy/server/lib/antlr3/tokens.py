"""ANTLR3 runtime package"""

# begin[licence]
#
# [The "BSD licence"]
# Copyright (c) 2005-2012 Terence Parr
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# end[licence]

from .constants import DEFAULT_CHANNEL, EOF, INVALID_TOKEN_TYPE

############################################################################
#
# basic token interface
#
############################################################################

class Token(object):
    """@brief Abstract token baseclass."""

    TOKEN_NAMES_MAP = None

    @classmethod
    def registerTokenNamesMap(cls, tokenNamesMap):
        """@brief Store a mapping from token type to token name.
        
        This enables token.typeName to give something more meaningful
        than, e.g., '6'.
        """
        cls.TOKEN_NAMES_MAP = tokenNamesMap
        cls.TOKEN_NAMES_MAP[EOF] = "EOF"

    def __init__(self, type=None, channel=DEFAULT_CHANNEL, text=None,
                 index=-1, line=0, charPositionInLine=-1, input=None):
        # We use -1 for index and charPositionInLine as an invalid index
        self._type = type
        self._channel = channel
        self._text = text
        self._index = index
        self._line = 0
        self._charPositionInLine = charPositionInLine
        self.input = input

    # To override a property, you'll need to override both the getter and setter.
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value


    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    # For compatibility
    def getType(self):
        return self._type

    @property
    def typeName(self):
        if self.TOKEN_NAMES_MAP:
            return self.TOKEN_NAMES_MAP.get(self._type, "INVALID_TOKEN_TYPE")
        else:
            return str(self._type)
    
    @property
    def line(self):
        """Lines are numbered 1..n."""
        return self._line

    @line.setter
    def line(self, value):
        self._line = value


    @property
    def charPositionInLine(self):
        """Columns are numbered 0..n-1."""
        return self._charPositionInLine

    @charPositionInLine.setter
    def charPositionInLine(self, pos):
        self._charPositionInLine = pos


    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self._channel = value


    @property
    def index(self):
        """
        An index from 0..n-1 of the token object in the input stream.
        This must be valid in order to use the ANTLRWorks debugger.
        """
        return self._index

    @index.setter
    def index(self, value):
        self._index = value


    def getInputStream(self):
        """@brief From what character stream was this token created.

        You don't have to implement but it's nice to know where a Token
        comes from if you have include files etc... on the input."""

        raise NotImplementedError

    def setInputStream(self, input):
        """@brief From what character stream was this token created.

        You don't have to implement but it's nice to know where a Token
        comes from if you have include files etc... on the input."""

        raise NotImplementedError


############################################################################
#
# token implementations
#
# Token
# +- CommonToken
# \- ClassicToken
#
############################################################################

class CommonToken(Token):
    """@brief Basic token implementation.

    This implementation does not copy the text from the input stream upon
    creation, but keeps start/stop pointers into the stream to avoid
    unnecessary copy operations.

    """

    def __init__(self, type=None, channel=DEFAULT_CHANNEL, text=None,
                 input=None, start=None, stop=None, oldToken=None):

        if oldToken:
            super().__init__(oldToken.type, oldToken.channel, oldToken.text,
                             oldToken.index, oldToken.line,
                             oldToken.charPositionInLine, oldToken.input)
            if isinstance(oldToken, CommonToken):
                self.start = oldToken.start
                self.stop = oldToken.stop
            else:
                self.start = start
                self.stop = stop

        else:
            super().__init__(type=type, channel=channel, input=input)

            # We need to be able to change the text once in a while.  If
            # this is non-null, then getText should return this.  Note that
            # start/stop are not affected by changing this.
            self._text = text

            # The char position into the input buffer where this token starts
            self.start = start

            # The char position into the input buffer where this token stops
            # This is the index of the last char, *not* the index after it!
            self.stop = stop


    @property
    def text(self):
        # Could be the empty string, and we want to return that.
        if self._text is not None:
            return self._text

        if not self.input:
            return None

        if self.start < self.input.size() and self.stop < self.input.size():
            return self.input.substring(self.start, self.stop)

        return '<EOF>'

    @text.setter
    def text(self, value):
        """
        Override the text for this token.  getText() will return this text
        rather than pulling from the buffer.  Note that this does not mean
        that start/stop indexes are not valid.  It means that that input
        was converted to a new string in the token object.
        """
        self._text = value


    def getInputStream(self):
        return self.input

    def setInputStream(self, input):
        self.input = input


    def __str__(self):
        if self.type == EOF:
            return "<EOF>"

        channelStr = ""
        if self.channel > 0:
            channelStr = ",channel=" + str(self.channel)

        txt = self.text
        if txt:
            # Put 2 backslashes in front of each character
            txt = txt.replace("\n", r"\\n")
            txt = txt.replace("\r", r"\\r")
            txt = txt.replace("\t", r"\\t")
        else:
            txt = "<no text>"

        return ("[@{0.index},{0.start}:{0.stop}={txt!r},"
                "<{0.typeName}>{channelStr},"
                "{0.line}:{0.charPositionInLine}]"
                .format(self, txt=txt, channelStr=channelStr))


class ClassicToken(Token):
    """@brief Alternative token implementation.

    A Token object like we'd use in ANTLR 2.x; has an actual string created
    and associated with this object.  These objects are needed for imaginary
    tree nodes that have payload objects.  We need to create a Token object
    that has a string; the tree node will point at this token.  CommonToken
    has indexes into a char stream and hence cannot be used to introduce
    new strings.
    """

    def __init__(self, type=None, text=None, channel=DEFAULT_CHANNEL,
                 oldToken=None):
        if oldToken:
            super().__init__(type=oldToken.type, channel=oldToken.channel,
                             text=oldToken.text, line=oldToken.line,
                             charPositionInLine=oldToken.charPositionInLine)

        else:
            super().__init__(type=type, channel=channel, text=text,
                             index=None, line=None, charPositionInLine=None)


    def getInputStream(self):
        return None

    def setInputStream(self, input):
        pass


    def toString(self):
        channelStr = ""
        if self.channel > 0:
            channelStr = ",channel=" + str(self.channel)

        txt = self.text
        if not txt:
            txt = "<no text>"

        return ("[@{0.index!r},{txt!r},<{0.type!r}>{channelStr},"
                "{0.line!r}:{0.charPositionInLine!r}]"
                .format(self, txt=txt, channelStr=channelStr))

    __str__ = toString
    __repr__ = toString


INVALID_TOKEN = CommonToken(type=INVALID_TOKEN_TYPE)

# In an action, a lexer rule can set token to this SKIP_TOKEN and ANTLR
# will avoid creating a token for this symbol and try to fetch another.
SKIP_TOKEN = CommonToken(type=INVALID_TOKEN_TYPE)
