"""ANTLR3 runtime package"""

# begin[licence]
#
# [The "BSD licence"]
# Copyright (c) 2005-2008 Terence Parr
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

from google.appengine._internal.antlr3.constants import EOF, DEFAULT_CHANNEL, INVALID_TOKEN_TYPE

############################################################################
#
# basic token interface
#
############################################################################

class Token(object):
    """@brief Abstract token baseclass."""

    def getText(self):
        """@brief Get the text of the token.

        Using setter/getter methods is deprecated. Use o.text instead.
        """
        raise NotImplementedError

    def setText(self, text):
        """@brief Set the text of the token.

        Using setter/getter methods is deprecated. Use o.text instead.
        """
        raise NotImplementedError


    def getType(self):
        """@brief Get the type of the token.

        Using setter/getter methods is deprecated. Use o.type instead."""

        raise NotImplementedError

    def setType(self, ttype):
        """@brief Get the type of the token.

        Using setter/getter methods is deprecated. Use o.type instead."""

        raise NotImplementedError


    def getLine(self):
        """@brief Get the line number on which this token was matched

        Lines are numbered 1..n

        Using setter/getter methods is deprecated. Use o.line instead."""

        raise NotImplementedError

    def setLine(self, line):
        """@brief Set the line number on which this token was matched

        Using setter/getter methods is deprecated. Use o.line instead."""

        raise NotImplementedError


    def getCharPositionInLine(self):
        """@brief Get the column of the tokens first character,

        Columns are numbered 0..n-1

        Using setter/getter methods is deprecated. Use o.charPositionInLine instead."""

        raise NotImplementedError

    def setCharPositionInLine(self, pos):
        """@brief Set the column of the tokens first character,

        Using setter/getter methods is deprecated. Use o.charPositionInLine instead."""

        raise NotImplementedError


    def getChannel(self):
        """@brief Get the channel of the token

        Using setter/getter methods is deprecated. Use o.channel instead."""

        raise NotImplementedError

    def setChannel(self, channel):
        """@brief Set the channel of the token

        Using setter/getter methods is deprecated. Use o.channel instead."""

        raise NotImplementedError


    def getTokenIndex(self):
        """@brief Get the index in the input stream.

        An index from 0..n-1 of the token object in the input stream.
        This must be valid in order to use the ANTLRWorks debugger.

        Using setter/getter methods is deprecated. Use o.index instead."""

        raise NotImplementedError

    def setTokenIndex(self, index):
        """@brief Set the index in the input stream.

        Using setter/getter methods is deprecated. Use o.index instead."""

        raise NotImplementedError


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
        Token.__init__(self)

        if oldToken is not None:
            self.type = oldToken.type
            self.line = oldToken.line
            self.charPositionInLine = oldToken.charPositionInLine
            self.channel = oldToken.channel
            self.index = oldToken.index
            self._text = oldToken._text
            if isinstance(oldToken, CommonToken):
                self.input = oldToken.input
                self.start = oldToken.start
                self.stop = oldToken.stop

        else:
            self.type = type
            self.input = input
            self.charPositionInLine = -1 # set to invalid position
            self.line = 0
            self.channel = channel

	    #What token number is this from 0..n-1 tokens; < 0 implies invalid index
            self.index = -1

            # We need to be able to change the text once in a while.  If
            # this is non-null, then getText should return this.  Note that
            # start/stop are not affected by changing this.
            self._text = text

            # The char position into the input buffer where this token starts
            self.start = start

            # The char position into the input buffer where this token stops
            # This is the index of the last char, *not* the index after it!
            self.stop = stop


    def getText(self):
        if self._text is not None:
            return self._text

        if self.input is None:
            return None

        return self.input.substring(self.start, self.stop)


    def setText(self, text):
        """
        Override the text for this token.  getText() will return this text
        rather than pulling from the buffer.  Note that this does not mean
        that start/stop indexes are not valid.  It means that that input
        was converted to a new string in the token object.
	"""
        self._text = text

    text = property(getText, setText)


    def getType(self):
        return self.type

    def setType(self, ttype):
        self.type = ttype


    def getLine(self):
        return self.line

    def setLine(self, line):
        self.line = line


    def getCharPositionInLine(self):
        return self.charPositionInLine

    def setCharPositionInLine(self, pos):
        self.charPositionInLine = pos


    def getChannel(self):
        return self.channel

    def setChannel(self, channel):
        self.channel = channel


    def getTokenIndex(self):
        return self.index

    def setTokenIndex(self, index):
        self.index = index


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
        if txt is not None:
            txt = txt.replace("\n","\\\\n")
            txt = txt.replace("\r","\\\\r")
            txt = txt.replace("\t","\\\\t")
        else:
            txt = "<no text>"

        return "[@%d,%d:%d=%r,<%d>%s,%d:%d]" % (
            self.index,
            self.start, self.stop,
            txt,
            self.type, channelStr,
            self.line, self.charPositionInLine
            )


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
                 oldToken=None
                 ):
        Token.__init__(self)

        if oldToken is not None:
            self.text = oldToken.text
            self.type = oldToken.type
            self.line = oldToken.line
            self.charPositionInLine = oldToken.charPositionInLine
            self.channel = oldToken.channel

        self.text = text
        self.type = type
        self.line = None
        self.charPositionInLine = None
        self.channel = channel
        self.index = None


    def getText(self):
        return self.text

    def setText(self, text):
        self.text = text


    def getType(self):
        return self.type

    def setType(self, ttype):
        self.type = ttype


    def getLine(self):
        return self.line

    def setLine(self, line):
        self.line = line


    def getCharPositionInLine(self):
        return self.charPositionInLine

    def setCharPositionInLine(self, pos):
        self.charPositionInLine = pos


    def getChannel(self):
        return self.channel

    def setChannel(self, channel):
        self.channel = channel


    def getTokenIndex(self):
        return self.index

    def setTokenIndex(self, index):
        self.index = index


    def getInputStream(self):
        return None

    def setInputStream(self, input):
        pass


    def toString(self):
        channelStr = ""
        if self.channel > 0:
            channelStr = ",channel=" + str(self.channel)

        txt = self.text
        if txt is None:
            txt = "<no text>"

        return "[@%r,%r,<%r>%s,%r:%r]" % (self.index,
                                          txt,
                                          self.type,
                                          channelStr,
                                          self.line,
                                          self.charPositionInLine
                                          )


    __str__ = toString
    __repr__ = toString



EOF_TOKEN = CommonToken(type=EOF)

INVALID_TOKEN = CommonToken(type=INVALID_TOKEN_TYPE)

# In an action, a lexer rule can set token to this SKIP_TOKEN and ANTLR
# will avoid creating a token for this symbol and try to fetch another.
SKIP_TOKEN = CommonToken(type=INVALID_TOKEN_TYPE)


