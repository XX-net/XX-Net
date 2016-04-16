"""ANTLR3 exception hierarchy"""

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

from antlr3.constants import INVALID_TOKEN_TYPE


class BacktrackingFailed(Exception):
    """@brief Raised to signal failed backtrack attempt"""

    pass


class RecognitionException(Exception):
    """@brief The root of the ANTLR exception hierarchy.

    To avoid English-only error messages and to generally make things
    as flexible as possible, these exceptions are not created with strings,
    but rather the information necessary to generate an error.  Then
    the various reporting methods in Parser and Lexer can be overridden
    to generate a localized error message.  For example, MismatchedToken
    exceptions are built with the expected token type.
    So, don't expect getMessage() to return anything.

    Note that as of Java 1.4, you can access the stack trace, which means
    that you can compute the complete trace of rules from the start symbol.
    This gives you considerable context information with which to generate
    useful error messages.

    ANTLR generates code that throws exceptions upon recognition error and
    also generates code to catch these exceptions in each rule.  If you
    want to quit upon first error, you can turn off the automatic error
    handling mechanism using rulecatch action, but you still need to
    override methods mismatch and recoverFromMismatchSet.
    
    In general, the recognition exceptions can track where in a grammar a
    problem occurred and/or what was the expected input.  While the parser
    knows its state (such as current input symbol and line info) that
    state can change before the exception is reported so current token index
    is computed and stored at exception time.  From this info, you can
    perhaps print an entire line of input not just a single token, for example.
    Better to just say the recognizer had a problem and then let the parser
    figure out a fancy report.
    
    """

    def __init__(self, input=None):
        Exception.__init__(self)

	# What input stream did the error occur in?
        self.input = None

        # What is index of token/char were we looking at when the error
        # occurred?
        self.index = None

	# The current Token when an error occurred.  Since not all streams
	# can retrieve the ith Token, we have to track the Token object.
	# For parsers.  Even when it's a tree parser, token might be set.
        self.token = None

	# If this is a tree parser exception, node is set to the node with
	# the problem.
        self.node = None

	# The current char when an error occurred. For lexers.
        self.c = None

	# Track the line at which the error occurred in case this is
	# generated from a lexer.  We need to track this since the
        # unexpected char doesn't carry the line info.
        self.line = None

        self.charPositionInLine = None

        # If you are parsing a tree node stream, you will encounter som
        # imaginary nodes w/o line/col info.  We now search backwards looking
        # for most recent token with line/col info, but notify getErrorHeader()
        # that info is approximate.
        self.approximateLineInfo = False

        
        if input is not None:
            self.input = input
            self.index = input.index()

            # late import to avoid cyclic dependencies
            from antlr3.streams import TokenStream, CharStream
            from antlr3.tree import TreeNodeStream

            if isinstance(self.input, TokenStream):
                self.token = self.input.LT(1)
                self.line = self.token.line
                self.charPositionInLine = self.token.charPositionInLine

            if isinstance(self.input, TreeNodeStream):
                self.extractInformationFromTreeNodeStream(self.input)

            else:
                if isinstance(self.input, CharStream):
                    self.c = self.input.LT(1)
                    self.line = self.input.line
                    self.charPositionInLine = self.input.charPositionInLine

                else:
                    self.c = self.input.LA(1)

    def extractInformationFromTreeNodeStream(self, nodes):
        from antlr3.tree import Tree, CommonTree
        from antlr3.tokens import CommonToken
        
        self.node = nodes.LT(1)
        adaptor = nodes.adaptor
        payload = adaptor.getToken(self.node)
        if payload is not None:
            self.token = payload
            if payload.line <= 0:
                # imaginary node; no line/pos info; scan backwards
                i = -1
                priorNode = nodes.LT(i)
                while priorNode is not None:
                    priorPayload = adaptor.getToken(priorNode)
                    if priorPayload is not None and priorPayload.line > 0:
                        # we found the most recent real line / pos info
                        self.line = priorPayload.line
                        self.charPositionInLine = priorPayload.charPositionInLine
                        self.approximateLineInfo = True
                        break
                    
                    i -= 1
                    priorNode = nodes.LT(i)
                    
            else: # node created from real token
                self.line = payload.line
                self.charPositionInLine = payload.charPositionInLine
                
        elif isinstance(self.node, Tree):
            self.line = self.node.line
            self.charPositionInLine = self.node.charPositionInLine
            if isinstance(self.node, CommonTree):
                self.token = self.node.token

        else:
            type = adaptor.getType(self.node)
            text = adaptor.getText(self.node)
            self.token = CommonToken(type=type, text=text)

     
    def getUnexpectedType(self):
        """Return the token type or char of the unexpected input element"""

        from antlr3.streams import TokenStream
        from antlr3.tree import TreeNodeStream

        if isinstance(self.input, TokenStream):
            return self.token.type

        elif isinstance(self.input, TreeNodeStream):
            adaptor = self.input.treeAdaptor
            return adaptor.getType(self.node)

        else:
            return self.c

    unexpectedType = property(getUnexpectedType)
    

class MismatchedTokenException(RecognitionException):
    """@brief A mismatched char or Token or tree node."""
    
    def __init__(self, expecting, input):
        RecognitionException.__init__(self, input)
        self.expecting = expecting
        

    def __str__(self):
        #return "MismatchedTokenException("+self.expecting+")"
        return "MismatchedTokenException(%r!=%r)" % (
            self.getUnexpectedType(), self.expecting
            )
    __repr__ = __str__


class UnwantedTokenException(MismatchedTokenException):
    """An extra token while parsing a TokenStream"""

    def getUnexpectedToken(self):
        return self.token


    def __str__(self):
        exp = ", expected %s" % self.expecting
        if self.expecting == INVALID_TOKEN_TYPE:
            exp = ""

        if self.token is None:
            return "UnwantedTokenException(found=%s%s)" % (None, exp)

        return "UnwantedTokenException(found=%s%s)" % (self.token.text, exp)
    __repr__ = __str__


class MissingTokenException(MismatchedTokenException):
    """
    We were expecting a token but it's not found.  The current token
    is actually what we wanted next.
    """

    def __init__(self, expecting, input, inserted):
        MismatchedTokenException.__init__(self, expecting, input)

        self.inserted = inserted


    def getMissingType(self):
        return self.expecting


    def __str__(self):
        if self.inserted is not None and self.token is not None:
            return "MissingTokenException(inserted %r at %r)" % (
                self.inserted, self.token.text)

        if self.token is not None:
            return "MissingTokenException(at %r)" % self.token.text

        return "MissingTokenException"
    __repr__ = __str__


class MismatchedRangeException(RecognitionException):
    """@brief The next token does not match a range of expected types."""

    def __init__(self, a, b, input):
        RecognitionException.__init__(self, input)

        self.a = a
        self.b = b
        

    def __str__(self):
        return "MismatchedRangeException(%r not in [%r..%r])" % (
            self.getUnexpectedType(), self.a, self.b
            )
    __repr__ = __str__
    

class MismatchedSetException(RecognitionException):
    """@brief The next token does not match a set of expected types."""

    def __init__(self, expecting, input):
        RecognitionException.__init__(self, input)

        self.expecting = expecting
        

    def __str__(self):
        return "MismatchedSetException(%r not in %r)" % (
            self.getUnexpectedType(), self.expecting
            )
    __repr__ = __str__


class MismatchedNotSetException(MismatchedSetException):
    """@brief Used for remote debugger deserialization"""
    
    def __str__(self):
        return "MismatchedNotSetException(%r!=%r)" % (
            self.getUnexpectedType(), self.expecting
            )
    __repr__ = __str__


class NoViableAltException(RecognitionException):
    """@brief Unable to decide which alternative to choose."""

    def __init__(
        self, grammarDecisionDescription, decisionNumber, stateNumber, input
        ):
        RecognitionException.__init__(self, input)

        self.grammarDecisionDescription = grammarDecisionDescription
        self.decisionNumber = decisionNumber
        self.stateNumber = stateNumber


    def __str__(self):
        return "NoViableAltException(%r!=[%r])" % (
            self.unexpectedType, self.grammarDecisionDescription
            )
    __repr__ = __str__
    

class EarlyExitException(RecognitionException):
    """@brief The recognizer did not match anything for a (..)+ loop."""

    def __init__(self, decisionNumber, input):
        RecognitionException.__init__(self, input)

        self.decisionNumber = decisionNumber


class FailedPredicateException(RecognitionException):
    """@brief A semantic predicate failed during validation.

    Validation of predicates
    occurs when normally parsing the alternative just like matching a token.
    Disambiguating predicate evaluation occurs when we hoist a predicate into
    a prediction decision.
    """

    def __init__(self, input, ruleName, predicateText):
        RecognitionException.__init__(self, input)
        
        self.ruleName = ruleName
        self.predicateText = predicateText


    def __str__(self):
        return "FailedPredicateException("+self.ruleName+",{"+self.predicateText+"}?)"
    __repr__ = __str__
    

class MismatchedTreeNodeException(RecognitionException):
    """@brief The next tree mode does not match the expected type."""

    def __init__(self, expecting, input):
        RecognitionException.__init__(self, input)
        
        self.expecting = expecting

    def __str__(self):
        return "MismatchedTreeNodeException(%r!=%r)" % (
            self.getUnexpectedType(), self.expecting
            )
    __repr__ = __str__
