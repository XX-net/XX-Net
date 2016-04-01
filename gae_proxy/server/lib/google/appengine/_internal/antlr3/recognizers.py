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

import sys
import inspect

from google.appengine._internal.antlr3 import runtime_version, runtime_version_str
from google.appengine._internal.antlr3.constants import DEFAULT_CHANNEL, HIDDEN_CHANNEL, EOF, EOR_TOKEN_TYPE, INVALID_TOKEN_TYPE
from google.appengine._internal.antlr3.exceptions import RecognitionException, MismatchedTokenException, MismatchedRangeException, MismatchedTreeNodeException, NoViableAltException, EarlyExitException, MismatchedSetException, MismatchedNotSetException, FailedPredicateException, BacktrackingFailed, UnwantedTokenException, MissingTokenException
from google.appengine._internal.antlr3.tokens import CommonToken, EOF_TOKEN, SKIP_TOKEN
from google.appengine._internal.antlr3.compat import set, frozenset, reversed


class RecognizerSharedState(object):
    """
    The set of fields needed by an abstract recognizer to recognize input
    and recover from errors etc...  As a separate state object, it can be
    shared among multiple grammars; e.g., when one grammar imports another.

    These fields are publically visible but the actual state pointer per
    parser is protected.
    """

    def __init__(self):
        # Track the set of token types that can follow any rule invocation.
        # Stack grows upwards.
        self.following = []

        # This is true when we see an error and before having successfully
        # matched a token.  Prevents generation of more than one error message
        # per error.
        self.errorRecovery = False

        # The index into the input stream where the last error occurred.
        # This is used to prevent infinite loops where an error is found
        # but no token is consumed during recovery...another error is found,
        # ad naseum.  This is a failsafe mechanism to guarantee that at least
        # one token/tree node is consumed for two errors.
        self.lastErrorIndex = -1

        # If 0, no backtracking is going on.  Safe to exec actions etc...
        # If >0 then it's the level of backtracking.
        self.backtracking = 0

        # An array[size num rules] of Map<Integer,Integer> that tracks
        # the stop token index for each rule.  ruleMemo[ruleIndex] is
        # the memoization table for ruleIndex.  For key ruleStartIndex, you
        # get back the stop token for associated rule or MEMO_RULE_FAILED.
        #
        # This is only used if rule memoization is on (which it is by default).
        self.ruleMemo = None

        ## Did the recognizer encounter a syntax error?  Track how many.
        self.syntaxErrors = 0


        # LEXER FIELDS (must be in same state object to avoid casting
        # constantly in generated code and Lexer object) :(


	## The goal of all lexer rules/methods is to create a token object.
        # This is an instance variable as multiple rules may collaborate to
        # create a single token.  nextToken will return this object after
        # matching lexer rule(s).  If you subclass to allow multiple token
        # emissions, then set this to the last token to be matched or
        # something nonnull so that the auto token emit mechanism will not
        # emit another token.
        self.token = None

        ## What character index in the stream did the current token start at?
        # Needed, for example, to get the text for current token.  Set at
        # the start of nextToken.
        self.tokenStartCharIndex = -1

        ## The line on which the first character of the token resides
        self.tokenStartLine = None

        ## The character position of first character within the line
        self.tokenStartCharPositionInLine = None

        ## The channel number for the current token
        self.channel = None

        ## The token type for the current token
        self.type = None

        ## You can set the text for the current token to override what is in
        # the input char buffer.  Use setText() or can set this instance var.
        self.text = None


class BaseRecognizer(object):
    """
    @brief Common recognizer functionality.

    A generic recognizer that can handle recognizers generated from
    lexer, parser, and tree grammars.  This is all the parsing
    support code essentially; most of it is error recovery stuff and
    backtracking.
    """

    MEMO_RULE_FAILED = -2
    MEMO_RULE_UNKNOWN = -1

    # copies from Token object for convenience in actions
    DEFAULT_TOKEN_CHANNEL = DEFAULT_CHANNEL

    # for convenience in actions
    HIDDEN = HIDDEN_CHANNEL

    # overridden by generated subclasses
    tokenNames = None

    # The antlr_version attribute has been introduced in 3.1. If it is not
    # overwritten in the generated recognizer, we assume a default of 3.0.1.
    antlr_version = (3, 0, 1, 0)
    antlr_version_str = "3.0.1"

    def __init__(self, state=None):
        # Input stream of the recognizer. Must be initialized by a subclass.
        self.input = None

        ## State of a lexer, parser, or tree parser are collected into a state
        # object so the state can be shared.  This sharing is needed to
        # have one grammar import others and share same error variables
        # and other state variables.  It's a kind of explicit multiple
        # inheritance via delegation of methods and shared state.
        if state is None:
            state = RecognizerSharedState()
        self._state = state

        if self.antlr_version > runtime_version:
            raise RuntimeError(
                "ANTLR version mismatch: "
                "The recognizer has been generated by V%s, but this runtime "
                "is V%s. Please use the V%s runtime or higher."
                % (self.antlr_version_str,
                   runtime_version_str,
                   self.antlr_version_str))
        elif (self.antlr_version < (3, 1, 0, 0) and
              self.antlr_version != runtime_version):
            # FIXME: make the runtime compatible with 3.0.1 codegen
            # and remove this block.
            raise RuntimeError(
                "ANTLR version mismatch: "
                "The recognizer has been generated by V%s, but this runtime "
                "is V%s. Please use the V%s runtime."
                % (self.antlr_version_str,
                   runtime_version_str,
                   self.antlr_version_str))

    # this one only exists to shut up pylint :(
    def setInput(self, input):
        self.input = input


    def reset(self):
        """
        reset the parser's state; subclasses must rewinds the input stream
        """

        # wack everything related to error recovery
        if self._state is None:
            # no shared state work to do
            return

        self._state.following = []
        self._state.errorRecovery = False
        self._state.lastErrorIndex = -1
        self._state.syntaxErrors = 0
        # wack everything related to backtracking and memoization
        self._state.backtracking = 0
        if self._state.ruleMemo is not None:
            self._state.ruleMemo = {}


    def match(self, input, ttype, follow):
        """
        Match current input symbol against ttype.  Attempt
        single token insertion or deletion error recovery.  If
        that fails, throw MismatchedTokenException.

        To turn off single token insertion or deletion error
        recovery, override mismatchRecover() and have it call
        plain mismatch(), which does not recover.  Then any error
        in a rule will cause an exception and immediate exit from
        rule.  Rule would recover by resynchronizing to the set of
        symbols that can follow rule ref.
        """

        matchedSymbol = self.getCurrentInputSymbol(input)
        if self.input.LA(1) == ttype:
            self.input.consume()
            self._state.errorRecovery = False
            return matchedSymbol

        if self._state.backtracking > 0:
            # FIXME: need to return matchedSymbol here as well. damn!!
            raise BacktrackingFailed

        matchedSymbol = self.recoverFromMismatchedToken(input, ttype, follow)
        return matchedSymbol


    def matchAny(self, input):
        """Match the wildcard: in a symbol"""

        self._state.errorRecovery = False
        self.input.consume()


    def mismatchIsUnwantedToken(self, input, ttype):
        return input.LA(2) == ttype


    def mismatchIsMissingToken(self, input, follow):
        if follow is None:
            # we have no information about the follow; we can only consume
            # a single token and hope for the best
            return False

        # compute what can follow this grammar element reference
        if EOR_TOKEN_TYPE in follow:
            if len(self._state.following) > 0:
                # remove EOR if we're not the start symbol
                follow = follow - set([EOR_TOKEN_TYPE])

            viableTokensFollowingThisRule = self.computeContextSensitiveRuleFOLLOW()
            follow = follow | viableTokensFollowingThisRule

        # if current token is consistent with what could come after set
        # then we know we're missing a token; error recovery is free to
        # "insert" the missing token
        if input.LA(1) in follow or EOR_TOKEN_TYPE in follow:
            return True

        return False


    def mismatch(self, input, ttype, follow):
        """
        Factor out what to do upon token mismatch so tree parsers can behave
        differently.  Override and call mismatchRecover(input, ttype, follow)
        to get single token insertion and deletion. Use this to turn of
        single token insertion and deletion. Override mismatchRecover
        to call this instead.
        """

        if self.mismatchIsUnwantedToken(input, ttype):
            raise UnwantedTokenException(ttype, input)

        elif self.mismatchIsMissingToken(input, follow):
            raise MissingTokenException(ttype, input, None)

        raise MismatchedTokenException(ttype, input)


##     def mismatchRecover(self, input, ttype, follow):
##         if self.mismatchIsUnwantedToken(input, ttype):
##             mte = UnwantedTokenException(ttype, input)

##         elif self.mismatchIsMissingToken(input, follow):
##             mte = MissingTokenException(ttype, input)

##         else:
##             mte = MismatchedTokenException(ttype, input)

##         self.recoverFromMismatchedToken(input, mte, ttype, follow)


    def reportError(self, e):
        """Report a recognition problem.

        This method sets errorRecovery to indicate the parser is recovering
        not parsing.  Once in recovery mode, no errors are generated.
        To get out of recovery mode, the parser must successfully match
        a token (after a resync).  So it will go:

        1. error occurs
        2. enter recovery mode, report error
        3. consume until token found in resynch set
        4. try to resume parsing
        5. next match() will reset errorRecovery mode

        If you override, make sure to update syntaxErrors if you care about
        that.

        """

        # if we've already reported an error and have not matched a token
        # yet successfully, don't report any errors.
        if self._state.errorRecovery:
            return

        self._state.syntaxErrors += 1 # don't count spurious
        self._state.errorRecovery = True

        self.displayRecognitionError(self.tokenNames, e)


    def displayRecognitionError(self, tokenNames, e):
        hdr = self.getErrorHeader(e)
        msg = self.getErrorMessage(e, tokenNames)
        self.emitErrorMessage(hdr+" "+msg)


    def getErrorMessage(self, e, tokenNames):
        """
        What error message should be generated for the various
        exception types?

        Not very object-oriented code, but I like having all error message
        generation within one method rather than spread among all of the
        exception classes. This also makes it much easier for the exception
        handling because the exception classes do not have to have pointers back
        to this object to access utility routines and so on. Also, changing
        the message for an exception type would be difficult because you
        would have to subclassing exception, but then somehow get ANTLR
        to make those kinds of exception objects instead of the default.
        This looks weird, but trust me--it makes the most sense in terms
        of flexibility.

        For grammar debugging, you will want to override this to add
        more information such as the stack frame with
        getRuleInvocationStack(e, this.getClass().getName()) and,
        for no viable alts, the decision description and state etc...

        Override this to change the message generated for one or more
        exception types.
        """

        if isinstance(e, UnwantedTokenException):
            tokenName = "<unknown>"
            if e.expecting == EOF:
                tokenName = "EOF"

            else:
                tokenName = self.tokenNames[e.expecting]

            msg = "extraneous input %s expecting %s" % (
                self.getTokenErrorDisplay(e.getUnexpectedToken()),
                tokenName
                )

        elif isinstance(e, MissingTokenException):
            tokenName = "<unknown>"
            if e.expecting == EOF:
                tokenName = "EOF"

            else:
                tokenName = self.tokenNames[e.expecting]

            msg = "missing %s at %s" % (
                tokenName, self.getTokenErrorDisplay(e.token)
                )

        elif isinstance(e, MismatchedTokenException):
            tokenName = "<unknown>"
            if e.expecting == EOF:
                tokenName = "EOF"
            else:
                tokenName = self.tokenNames[e.expecting]

            msg = "mismatched input " + self.getTokenErrorDisplay(e.token) + " expecting " + tokenName

        elif isinstance(e, MismatchedTreeNodeException):
            tokenName = "<unknown>"
            if e.expecting == EOF:
                tokenName = "EOF"
            else:
                tokenName = self.tokenNames[e.expecting]

            msg = "mismatched tree node: %s expecting %s" % (e.node, tokenName)

        elif isinstance(e, NoViableAltException):
            msg = "no viable alternative at input " + self.getTokenErrorDisplay(e.token)

        elif isinstance(e, EarlyExitException):
            msg = "required (...)+ loop did not match anything at input " + self.getTokenErrorDisplay(e.token)

        elif isinstance(e, MismatchedSetException):
            msg = "mismatched input " + self.getTokenErrorDisplay(e.token) + " expecting set " + repr(e.expecting)

        elif isinstance(e, MismatchedNotSetException):
            msg = "mismatched input " + self.getTokenErrorDisplay(e.token) + " expecting set " + repr(e.expecting)

        elif isinstance(e, FailedPredicateException):
            msg = "rule " + e.ruleName + " failed predicate: {" + e.predicateText + "}?"

        else:
            msg = str(e)

        return msg


    def getNumberOfSyntaxErrors(self):
        """
        Get number of recognition errors (lexer, parser, tree parser).  Each
        recognizer tracks its own number.  So parser and lexer each have
        separate count.  Does not count the spurious errors found between
        an error and next valid token match

        See also reportError()
	"""
        return self._state.syntaxErrors


    def getErrorHeader(self, e):
        """
        What is the error header, normally line/character position information?
        """

        return "line %d:%d" % (e.line, e.charPositionInLine)


    def getTokenErrorDisplay(self, t):
        """
        How should a token be displayed in an error message? The default
        is to display just the text, but during development you might
        want to have a lot of information spit out.  Override in that case
        to use t.toString() (which, for CommonToken, dumps everything about
        the token). This is better than forcing you to override a method in
        your token objects because you don't have to go modify your lexer
        so that it creates a new Java type.
        """

        s = t.text
        if s is None:
            if t.type == EOF:
                s = "<EOF>"
            else:
                s = "<"+t.type+">"

        return repr(s)


    def emitErrorMessage(self, msg):
        """Override this method to change where error messages go"""
        sys.stderr.write(msg + '\n')


    def recover(self, input, re):
        """
        Recover from an error found on the input stream.  This is
        for NoViableAlt and mismatched symbol exceptions.  If you enable
        single token insertion and deletion, this will usually not
        handle mismatched symbol exceptions but there could be a mismatched
        token that the match() routine could not recover from.
        """

        # PROBLEM? what if input stream is not the same as last time
        # perhaps make lastErrorIndex a member of input
        if self._state.lastErrorIndex == input.index():
            # uh oh, another error at same token index; must be a case
            # where LT(1) is in the recovery token set so nothing is
            # consumed; consume a single token so at least to prevent
            # an infinite loop; this is a failsafe.
            input.consume()

        self._state.lastErrorIndex = input.index()
        followSet = self.computeErrorRecoverySet()

        self.beginResync()
        self.consumeUntil(input, followSet)
        self.endResync()


    def beginResync(self):
        """
        A hook to listen in on the token consumption during error recovery.
        The DebugParser subclasses this to fire events to the listenter.
        """

        pass


    def endResync(self):
        """
        A hook to listen in on the token consumption during error recovery.
        The DebugParser subclasses this to fire events to the listenter.
        """

        pass


    def computeErrorRecoverySet(self):
        """
        Compute the error recovery set for the current rule.  During
        rule invocation, the parser pushes the set of tokens that can
        follow that rule reference on the stack; this amounts to
        computing FIRST of what follows the rule reference in the
        enclosing rule. This local follow set only includes tokens
        from within the rule; i.e., the FIRST computation done by
        ANTLR stops at the end of a rule.

        EXAMPLE

        When you find a "no viable alt exception", the input is not
        consistent with any of the alternatives for rule r.  The best
        thing to do is to consume tokens until you see something that
        can legally follow a call to r *or* any rule that called r.
        You don't want the exact set of viable next tokens because the
        input might just be missing a token--you might consume the
        rest of the input looking for one of the missing tokens.

        Consider grammar:

        a : '[' b ']'
          | '(' b ')'
          ;
        b : c '^' INT ;
        c : ID
          | INT
          ;

        At each rule invocation, the set of tokens that could follow
        that rule is pushed on a stack.  Here are the various "local"
        follow sets:

        FOLLOW(b1_in_a) = FIRST(']') = ']'
        FOLLOW(b2_in_a) = FIRST(')') = ')'
        FOLLOW(c_in_b) = FIRST('^') = '^'

        Upon erroneous input "[]", the call chain is

        a -> b -> c

        and, hence, the follow context stack is:

        depth  local follow set     after call to rule
          0         \<EOF>                    a (from main())
          1          ']'                     b
          3          '^'                     c

        Notice that ')' is not included, because b would have to have
        been called from a different context in rule a for ')' to be
        included.

        For error recovery, we cannot consider FOLLOW(c)
        (context-sensitive or otherwise).  We need the combined set of
        all context-sensitive FOLLOW sets--the set of all tokens that
        could follow any reference in the call chain.  We need to
        resync to one of those tokens.  Note that FOLLOW(c)='^' and if
        we resync'd to that token, we'd consume until EOF.  We need to
        sync to context-sensitive FOLLOWs for a, b, and c: {']','^'}.
        In this case, for input "[]", LA(1) is in this set so we would
        not consume anything and after printing an error rule c would
        return normally.  It would not find the required '^' though.
        At this point, it gets a mismatched token error and throws an
        exception (since LA(1) is not in the viable following token
        set).  The rule exception handler tries to recover, but finds
        the same recovery set and doesn't consume anything.  Rule b
        exits normally returning to rule a.  Now it finds the ']' (and
        with the successful match exits errorRecovery mode).

        So, you cna see that the parser walks up call chain looking
        for the token that was a member of the recovery set.

        Errors are not generated in errorRecovery mode.

        ANTLR's error recovery mechanism is based upon original ideas:

        "Algorithms + Data Structures = Programs" by Niklaus Wirth

        and

        "A note on error recovery in recursive descent parsers":
        http://portal.acm.org/citation.cfm?id=947902.947905

        Later, Josef Grosch had some good ideas:

        "Efficient and Comfortable Error Recovery in Recursive Descent
        Parsers":
        ftp://www.cocolab.com/products/cocktail/doca4.ps/ell.ps.zip

        Like Grosch I implemented local FOLLOW sets that are combined
        at run-time upon error to avoid overhead during parsing.
        """

        return self.combineFollows(False)


    def computeContextSensitiveRuleFOLLOW(self):
        """
        Compute the context-sensitive FOLLOW set for current rule.
        This is set of token types that can follow a specific rule
        reference given a specific call chain.  You get the set of
        viable tokens that can possibly come next (lookahead depth 1)
        given the current call chain.  Contrast this with the
        definition of plain FOLLOW for rule r:

         FOLLOW(r)={x | S=>*alpha r beta in G and x in FIRST(beta)}

        where x in T* and alpha, beta in V*; T is set of terminals and
        V is the set of terminals and nonterminals.  In other words,
        FOLLOW(r) is the set of all tokens that can possibly follow
        references to r in *any* sentential form (context).  At
        runtime, however, we know precisely which context applies as
        we have the call chain.  We may compute the exact (rather
        than covering superset) set of following tokens.

        For example, consider grammar:

        stat : ID '=' expr ';'      // FOLLOW(stat)=={EOF}
             | "return" expr '.'
             ;
        expr : atom ('+' atom)* ;   // FOLLOW(expr)=={';','.',')'}
        atom : INT                  // FOLLOW(atom)=={'+',')',';','.'}
             | '(' expr ')'
             ;

        The FOLLOW sets are all inclusive whereas context-sensitive
        FOLLOW sets are precisely what could follow a rule reference.
        For input input "i=(3);", here is the derivation:

        stat => ID '=' expr ';'
             => ID '=' atom ('+' atom)* ';'
             => ID '=' '(' expr ')' ('+' atom)* ';'
             => ID '=' '(' atom ')' ('+' atom)* ';'
             => ID '=' '(' INT ')' ('+' atom)* ';'
             => ID '=' '(' INT ')' ';'

        At the "3" token, you'd have a call chain of

          stat -> expr -> atom -> expr -> atom

        What can follow that specific nested ref to atom?  Exactly ')'
        as you can see by looking at the derivation of this specific
        input.  Contrast this with the FOLLOW(atom)={'+',')',';','.'}.

        You want the exact viable token set when recovering from a
        token mismatch.  Upon token mismatch, if LA(1) is member of
        the viable next token set, then you know there is most likely
        a missing token in the input stream.  "Insert" one by just not
        throwing an exception.
        """

        return self.combineFollows(True)


    def combineFollows(self, exact):
        followSet = set()
        for idx, localFollowSet in reversed(list(enumerate(self._state.following))):
            followSet |= localFollowSet
            if exact:
                # can we see end of rule?
                if EOR_TOKEN_TYPE in localFollowSet:
                    # Only leave EOR in set if at top (start rule); this lets
                    # us know if have to include follow(start rule); i.e., EOF
                    if idx > 0:
                        followSet.remove(EOR_TOKEN_TYPE)

                else:
                    # can't see end of rule, quit
                    break

        return followSet


    def recoverFromMismatchedToken(self, input, ttype, follow):
        """Attempt to recover from a single missing or extra token.

        EXTRA TOKEN

        LA(1) is not what we are looking for.  If LA(2) has the right token,
        however, then assume LA(1) is some extra spurious token.  Delete it
        and LA(2) as if we were doing a normal match(), which advances the
        input.

        MISSING TOKEN

        If current token is consistent with what could come after
        ttype then it is ok to 'insert' the missing token, else throw
        exception For example, Input 'i=(3;' is clearly missing the
        ')'.  When the parser returns from the nested call to expr, it
        will have call chain:

          stat -> expr -> atom

        and it will be trying to match the ')' at this point in the
        derivation:

             => ID '=' '(' INT ')' ('+' atom)* ';'
                                ^
        match() will see that ';' doesn't match ')' and report a
        mismatched token error.  To recover, it sees that LA(1)==';'
        is in the set of tokens that can follow the ')' token
        reference in rule atom.  It can assume that you forgot the ')'.
        """

        e = None

        # if next token is what we are looking for then "delete" this token
        if self. mismatchIsUnwantedToken(input, ttype):
            e = UnwantedTokenException(ttype, input)

            self.beginResync()
            input.consume() # simply delete extra token
            self.endResync()

            # report after consuming so AW sees the token in the exception
            self.reportError(e)

            # we want to return the token we're actually matching
            matchedSymbol = self.getCurrentInputSymbol(input)

            # move past ttype token as if all were ok
            input.consume()
            return matchedSymbol

        # can't recover with single token deletion, try insertion
        if self.mismatchIsMissingToken(input, follow):
            inserted = self.getMissingSymbol(input, e, ttype, follow)
            e = MissingTokenException(ttype, input, inserted)

            # report after inserting so AW sees the token in the exception
            self.reportError(e)
            return inserted

        # even that didn't work; must throw the exception
        e = MismatchedTokenException(ttype, input)
        raise e


    def recoverFromMismatchedSet(self, input, e, follow):
        """Not currently used"""

        if self.mismatchIsMissingToken(input, follow):
            self.reportError(e)
            # we don't know how to conjure up a token for sets yet
            return self.getMissingSymbol(input, e, INVALID_TOKEN_TYPE, follow)

        # TODO do single token deletion like above for Token mismatch
        raise e


    def getCurrentInputSymbol(self, input):
        """
        Match needs to return the current input symbol, which gets put
        into the label for the associated token ref; e.g., x=ID.  Token
        and tree parsers need to return different objects. Rather than test
        for input stream type or change the IntStream interface, I use
        a simple method to ask the recognizer to tell me what the current
        input symbol is.

        This is ignored for lexers.
        """

        return None


    def getMissingSymbol(self, input, e, expectedTokenType, follow):
        """Conjure up a missing token during error recovery.

        The recognizer attempts to recover from single missing
        symbols. But, actions might refer to that missing symbol.
        For example, x=ID {f($x);}. The action clearly assumes
        that there has been an identifier matched previously and that
        $x points at that token. If that token is missing, but
        the next token in the stream is what we want we assume that
        this token is missing and we keep going. Because we
        have to return some token to replace the missing token,
        we have to conjure one up. This method gives the user control
        over the tokens returned for missing tokens. Mostly,
        you will want to create something special for identifier
        tokens. For literals such as '{' and ',', the default
        action in the parser or tree parser works. It simply creates
        a CommonToken of the appropriate type. The text will be the token.
        If you change what tokens must be created by the lexer,
        override this method to create the appropriate tokens.
        """

        return None


##     def recoverFromMissingElement(self, input, e, follow):
##         """
##         This code is factored out from mismatched token and mismatched set
##         recovery.  It handles "single token insertion" error recovery for
##         both.  No tokens are consumed to recover from insertions.  Return
##         true if recovery was possible else return false.
##         """

##         if self.mismatchIsMissingToken(input, follow):
##             self.reportError(e)
##             return True

##         # nothing to do; throw exception
##         return False


    def consumeUntil(self, input, tokenTypes):
        """
        Consume tokens until one matches the given token or token set

        tokenTypes can be a single token type or a set of token types

        """

        if not isinstance(tokenTypes, (set, frozenset)):
            tokenTypes = frozenset([tokenTypes])

        ttype = input.LA(1)
        while ttype != EOF and ttype not in tokenTypes:
            input.consume()
            ttype = input.LA(1)


    def getRuleInvocationStack(self):
        """
        Return List<String> of the rules in your parser instance
        leading up to a call to this method.  You could override if
        you want more details such as the file/line info of where
        in the parser java code a rule is invoked.

        This is very useful for error messages and for context-sensitive
        error recovery.

        You must be careful, if you subclass a generated recognizers.
        The default implementation will only search the module of self
        for rules, but the subclass will not contain any rules.
        You probably want to override this method to look like

        def getRuleInvocationStack(self):
            return self._getRuleInvocationStack(<class>.__module__)

        where <class> is the class of the generated recognizer, e.g.
        the superclass of self.
        """

        return self._getRuleInvocationStack(self.__module__)


    def _getRuleInvocationStack(cls, module):
        """
        A more general version of getRuleInvocationStack where you can
        pass in, for example, a RecognitionException to get it's rule
        stack trace.  This routine is shared with all recognizers, hence,
        static.

        TODO: move to a utility class or something; weird having lexer call
        this
        """

        # mmmhhh,... perhaps look at the first argument
        # (f_locals[co_varnames[0]]?) and test if it's a (sub)class of
        # requested recognizer...

        rules = []
        for frame in reversed(inspect.stack()):
            code = frame[0].f_code
            codeMod = inspect.getmodule(code)
            if codeMod is None:
                continue

            # skip frames not in requested module
            if codeMod.__name__ != module:
                continue

            # skip some unwanted names
            if code.co_name in ('nextToken', '<module>'):
                continue

            rules.append(code.co_name)

        return rules

    _getRuleInvocationStack = classmethod(_getRuleInvocationStack)


    def getBacktrackingLevel(self):
        return self._state.backtracking


    def getGrammarFileName(self):
        """For debugging and other purposes, might want the grammar name.

        Have ANTLR generate an implementation for this method.
        """

        return self.grammarFileName


    def getSourceName(self):
        raise NotImplementedError


    def toStrings(self, tokens):
        """A convenience method for use most often with template rewrites.

        Convert a List<Token> to List<String>
        """

        if tokens is None:
            return None

        return [token.text for token in tokens]


    def getRuleMemoization(self, ruleIndex, ruleStartIndex):
        """
        Given a rule number and a start token index number, return
        MEMO_RULE_UNKNOWN if the rule has not parsed input starting from
        start index.  If this rule has parsed input starting from the
        start index before, then return where the rule stopped parsing.
        It returns the index of the last token matched by the rule.
        """

        if ruleIndex not in self._state.ruleMemo:
            self._state.ruleMemo[ruleIndex] = {}

        return self._state.ruleMemo[ruleIndex].get(
            ruleStartIndex, self.MEMO_RULE_UNKNOWN
            )


    def alreadyParsedRule(self, input, ruleIndex):
        """
        Has this rule already parsed input at the current index in the
        input stream?  Return the stop token index or MEMO_RULE_UNKNOWN.
        If we attempted but failed to parse properly before, return
        MEMO_RULE_FAILED.

        This method has a side-effect: if we have seen this input for
        this rule and successfully parsed before, then seek ahead to
        1 past the stop token matched for this rule last time.
        """

        stopIndex = self.getRuleMemoization(ruleIndex, input.index())
        if stopIndex == self.MEMO_RULE_UNKNOWN:
            return False

        if stopIndex == self.MEMO_RULE_FAILED:
            raise BacktrackingFailed

        else:
            input.seek(stopIndex + 1)

        return True


    def memoize(self, input, ruleIndex, ruleStartIndex, success):
        """
        Record whether or not this rule parsed the input at this position
        successfully.
        """

        if success:
            stopTokenIndex = input.index() - 1
        else:
            stopTokenIndex = self.MEMO_RULE_FAILED

        if ruleIndex in self._state.ruleMemo:
            self._state.ruleMemo[ruleIndex][ruleStartIndex] = stopTokenIndex


    def traceIn(self, ruleName, ruleIndex, inputSymbol):
        sys.stdout.write("enter %s %s" % (ruleName, inputSymbol))

##         if self._state.failed:
##             sys.stdout.write(" failed=%s" % self._state.failed)

        if self._state.backtracking > 0:
            sys.stdout.write(" backtracking=%s" % self._state.backtracking)

        sys.stdout.write('\n')


    def traceOut(self, ruleName, ruleIndex, inputSymbol):
        sys.stdout.write("exit %s %s" % (ruleName, inputSymbol))

##         if self._state.failed:
##             sys.stdout.write(" failed=%s" % self._state.failed)

        if self._state.backtracking > 0:
            sys.stdout.write(" backtracking=%s" % self._state.backtracking)

        sys.stdout.write('\n')



class TokenSource(object):
    """
    @brief Abstract baseclass for token producers.

    A source of tokens must provide a sequence of tokens via nextToken()
    and also must reveal it's source of characters; CommonToken's text is
    computed from a CharStream; it only store indices into the char stream.

    Errors from the lexer are never passed to the parser.  Either you want
    to keep going or you do not upon token recognition error.  If you do not
    want to continue lexing then you do not want to continue parsing.  Just
    throw an exception not under RecognitionException and Java will naturally
    toss you all the way out of the recognizers.  If you want to continue
    lexing then you should not throw an exception to the parser--it has already
    requested a token.  Keep lexing until you get a valid one.  Just report
    errors and keep going, looking for a valid token.
    """

    def nextToken(self):
        """Return a Token object from your input stream (usually a CharStream).

        Do not fail/return upon lexing error; keep chewing on the characters
        until you get a good one; errors are not passed through to the parser.
        """

        raise NotImplementedError


    def __iter__(self):
        """The TokenSource is an interator.

        The iteration will not include the final EOF token, see also the note
        for the next() method.

        """

        return self


    def next(self):
        """Return next token or raise StopIteration.

        Note that this will raise StopIteration when hitting the EOF token,
        so EOF will not be part of the iteration.

        """

        token = self.nextToken()
        if token is None or token.type == EOF:
            raise StopIteration
        return token


class Lexer(BaseRecognizer, TokenSource):
    """
    @brief Baseclass for generated lexer classes.

    A lexer is recognizer that draws input symbols from a character stream.
    lexer grammars result in a subclass of this object. A Lexer object
    uses simplified match() and error recovery mechanisms in the interest
    of speed.
    """

    def __init__(self, input, state=None):
        BaseRecognizer.__init__(self, state)
        TokenSource.__init__(self)

        # Where is the lexer drawing characters from?
        self.input = input


    def reset(self):
        BaseRecognizer.reset(self) # reset all recognizer state variables

        if self.input is not None:
            # rewind the input
            self.input.seek(0)

        if self._state is None:
            # no shared state work to do
            return

        # wack Lexer state variables
        self._state.token = None
        self._state.type = INVALID_TOKEN_TYPE
        self._state.channel = DEFAULT_CHANNEL
        self._state.tokenStartCharIndex = -1
        self._state.tokenStartLine = -1
        self._state.tokenStartCharPositionInLine = -1
        self._state.text = None


    def nextToken(self):
        """
        Return a token from this source; i.e., match a token on the char
        stream.
        """

        while 1:
            self._state.token = None
            self._state.channel = DEFAULT_CHANNEL
            self._state.tokenStartCharIndex = self.input.index()
            self._state.tokenStartCharPositionInLine = self.input.charPositionInLine
            self._state.tokenStartLine = self.input.line
            self._state.text = None
            if self.input.LA(1) == EOF:
                return EOF_TOKEN

            try:
                self.mTokens()

                if self._state.token is None:
                    self.emit()

                elif self._state.token == SKIP_TOKEN:
                    continue

                return self._state.token

            except NoViableAltException, re:
                self.reportError(re)
                self.recover(re) # throw out current char and try again

            except RecognitionException, re:
                self.reportError(re)
                # match() routine has already called recover()


    def skip(self):
        """
        Instruct the lexer to skip creating a token for current lexer rule
        and look for another token.  nextToken() knows to keep looking when
        a lexer rule finishes with token set to SKIP_TOKEN.  Recall that
        if token==null at end of any token rule, it creates one for you
        and emits it.
        """

        self._state.token = SKIP_TOKEN


    def mTokens(self):
        """This is the lexer entry point that sets instance var 'token'"""

        # abstract method
        raise NotImplementedError


    def setCharStream(self, input):
        """Set the char stream and reset the lexer"""
        self.input = None
        self.reset()
        self.input = input


    def getSourceName(self):
        return self.input.getSourceName()


    def emit(self, token=None):
        """
        The standard method called to automatically emit a token at the
        outermost lexical rule.  The token object should point into the
        char buffer start..stop.  If there is a text override in 'text',
        use that to set the token's text.  Override this method to emit
        custom Token objects.

        If you are building trees, then you should also override
        Parser or TreeParser.getMissingSymbol().
        """

        if token is None:
            token = CommonToken(
                input=self.input,
                type=self._state.type,
                channel=self._state.channel,
                start=self._state.tokenStartCharIndex,
                stop=self.getCharIndex()-1
                )
            token.line = self._state.tokenStartLine
            token.text = self._state.text
            token.charPositionInLine = self._state.tokenStartCharPositionInLine

        self._state.token = token

        return token


    def match(self, s):
        if isinstance(s, basestring):
            for c in s:
                if self.input.LA(1) != ord(c):
                    if self._state.backtracking > 0:
                        raise BacktrackingFailed

                    mte = MismatchedTokenException(c, self.input)
                    self.recover(mte)
                    raise mte

                self.input.consume()

        else:
            if self.input.LA(1) != s:
                if self._state.backtracking > 0:
                    raise BacktrackingFailed

                mte = MismatchedTokenException(unichr(s), self.input)
                self.recover(mte) # don't really recover; just consume in lexer
                raise mte

            self.input.consume()


    def matchAny(self):
        self.input.consume()


    def matchRange(self, a, b):
        if self.input.LA(1) < a or self.input.LA(1) > b:
            if self._state.backtracking > 0:
                raise BacktrackingFailed

            mre = MismatchedRangeException(unichr(a), unichr(b), self.input)
            self.recover(mre)
            raise mre

        self.input.consume()


    def getLine(self):
        return self.input.line


    def getCharPositionInLine(self):
        return self.input.charPositionInLine


    def getCharIndex(self):
        """What is the index of the current character of lookahead?"""

        return self.input.index()


    def getText(self):
        """
        Return the text matched so far for the current token or any
        text override.
        """
        if self._state.text is not None:
            return self._state.text

        return self.input.substring(
            self._state.tokenStartCharIndex,
            self.getCharIndex()-1
            )


    def setText(self, text):
        """
        Set the complete text of this token; it wipes any previous
        changes to the text.
        """
        self._state.text = text


    text = property(getText, setText)


    def reportError(self, e):
        ## TODO: not thought about recovery in lexer yet.

        ## # if we've already reported an error and have not matched a token
        ## # yet successfully, don't report any errors.
        ## if self.errorRecovery:
        ##     #System.err.print("[SPURIOUS] ");
        ##     return;
        ##
        ## self.errorRecovery = True

        self.displayRecognitionError(self.tokenNames, e)


    def getErrorMessage(self, e, tokenNames):
        msg = None

        if isinstance(e, MismatchedTokenException):
            msg = "mismatched character " + self.getCharErrorDisplay(e.c) + " expecting " + self.getCharErrorDisplay(e.expecting)

        elif isinstance(e, NoViableAltException):
            msg = "no viable alternative at character " + self.getCharErrorDisplay(e.c)

        elif isinstance(e, EarlyExitException):
            msg = "required (...)+ loop did not match anything at character " + self.getCharErrorDisplay(e.c)

        elif isinstance(e, MismatchedNotSetException):
            msg = "mismatched character " + self.getCharErrorDisplay(e.c) + " expecting set " + repr(e.expecting)

        elif isinstance(e, MismatchedSetException):
            msg = "mismatched character " + self.getCharErrorDisplay(e.c) + " expecting set " + repr(e.expecting)

        elif isinstance(e, MismatchedRangeException):
            msg = "mismatched character " + self.getCharErrorDisplay(e.c) + " expecting set " + self.getCharErrorDisplay(e.a) + ".." + self.getCharErrorDisplay(e.b)

        else:
            msg = BaseRecognizer.getErrorMessage(self, e, tokenNames)

        return msg


    def getCharErrorDisplay(self, c):
        if c == EOF:
            c = '<EOF>'
        return repr(c)


    def recover(self, re):
        """
        Lexers can normally match any char in it's vocabulary after matching
        a token, so do the easy thing and just kill a character and hope
        it all works out.  You can instead use the rule invocation stack
        to do sophisticated error recovery if you are in a fragment rule.
        """

        self.input.consume()


    def traceIn(self, ruleName, ruleIndex):
        inputSymbol = "%s line=%d:%s" % (self.input.LT(1),
                                         self.getLine(),
                                         self.getCharPositionInLine()
                                         )

        BaseRecognizer.traceIn(self, ruleName, ruleIndex, inputSymbol)


    def traceOut(self, ruleName, ruleIndex):
        inputSymbol = "%s line=%d:%s" % (self.input.LT(1),
                                         self.getLine(),
                                         self.getCharPositionInLine()
                                         )

        BaseRecognizer.traceOut(self, ruleName, ruleIndex, inputSymbol)



class Parser(BaseRecognizer):
    """
    @brief Baseclass for generated parser classes.
    """

    def __init__(self, lexer, state=None):
        BaseRecognizer.__init__(self, state)

        self.setTokenStream(lexer)


    def reset(self):
        BaseRecognizer.reset(self) # reset all recognizer state variables
        if self.input is not None:
            self.input.seek(0) # rewind the input


    def getCurrentInputSymbol(self, input):
        return input.LT(1)


    def getMissingSymbol(self, input, e, expectedTokenType, follow):
        if expectedTokenType == EOF:
            tokenText = "<missing EOF>"
        else:
            tokenText = "<missing " + self.tokenNames[expectedTokenType] + ">"
        t = CommonToken(type=expectedTokenType, text=tokenText)
        current = input.LT(1)
        if current.type == EOF:
            current = input.LT(-1)

        if current is not None:
            t.line = current.line
            t.charPositionInLine = current.charPositionInLine
        t.channel = DEFAULT_CHANNEL
        return t


    def setTokenStream(self, input):
        """Set the token stream and reset the parser"""

        self.input = None
        self.reset()
        self.input = input


    def getTokenStream(self):
        return self.input


    def getSourceName(self):
        return self.input.getSourceName()


    def traceIn(self, ruleName, ruleIndex):
        BaseRecognizer.traceIn(self, ruleName, ruleIndex, self.input.LT(1))


    def traceOut(self, ruleName, ruleIndex):
        BaseRecognizer.traceOut(self, ruleName, ruleIndex, self.input.LT(1))


class RuleReturnScope(object):
    """
    Rules can return start/stop info as well as possible trees and templates.
    """

    def getStart(self):
        """Return the start token or tree."""
        return None


    def getStop(self):
        """Return the stop token or tree."""
        return None


    def getTree(self):
        """Has a value potentially if output=AST."""
        return None


    def getTemplate(self):
        """Has a value potentially if output=template."""
        return None


class ParserRuleReturnScope(RuleReturnScope):
    """
    Rules that return more than a single value must return an object
    containing all the values.  Besides the properties defined in
    RuleLabelScope.predefinedRulePropertiesScope there may be user-defined
    return values.  This class simply defines the minimum properties that
    are always defined and methods to access the others that might be
    available depending on output option such as template and tree.

    Note text is not an actual property of the return value, it is computed
    from start and stop using the input stream's toString() method.  I
    could add a ctor to this so that we can pass in and store the input
    stream, but I'm not sure we want to do that.  It would seem to be undefined
    to get the .text property anyway if the rule matches tokens from multiple
    input streams.

    I do not use getters for fields of objects that are used simply to
    group values such as this aggregate.  The getters/setters are there to
    satisfy the superclass interface.
    """

    def __init__(self):
        self.start = None
        self.stop = None


    def getStart(self):
        return self.start


    def getStop(self):
        return self.stop

