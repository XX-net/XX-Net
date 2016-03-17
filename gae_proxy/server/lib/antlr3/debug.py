# begin[licence]
#
#  [The "BSD licence"]
#  Copyright (c) 2005-2012 Terence Parr
#  All rights reserved.

#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. The name of the author may not be used to endorse or promote products
#     derived from this software without specific prior written permission.

#  THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
#  IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
#  OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
#  THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# end[licence]

import socket
import sys
from .constants import INVALID_TOKEN_TYPE
from .exceptions import RecognitionException
from .recognizers import Parser
from .streams import TokenStream
from .tokens import Token
from .tree import CommonTreeAdaptor, TreeAdaptor, Tree

class DebugParser(Parser):
    def __init__(self, stream, state=None, dbg=None, *args, **kwargs):
        # wrap token stream in DebugTokenStream (unless user already did so).
        if not isinstance(stream, DebugTokenStream):
            stream = DebugTokenStream(stream, dbg)

        super().__init__(stream, state, *args, **kwargs)

        # Who to notify when events in the parser occur.
        self._dbg = None

        self.setDebugListener(dbg)


    def setDebugListener(self, dbg):
        """Provide a new debug event listener for this parser.  Notify the
        input stream too that it should send events to this listener.
        """

        if hasattr(self.input, 'dbg'):
            self.input.dbg = dbg

        self._dbg = dbg

    def getDebugListener(self):
        return self._dbg

    dbg = property(getDebugListener, setDebugListener)


    def beginResync(self):
        self._dbg.beginResync()


    def endResync(self):
        self._dbg.endResync()


    def beginBacktrack(self, level):
        self._dbg.beginBacktrack(level)


    def endBacktrack(self, level, successful):
        self._dbg.endBacktrack(level, successful)


    def reportError(self, exc):
        Parser.reportError(self, exc)

        if isinstance(exc, RecognitionException):
            self._dbg.recognitionException(exc)


class DebugTokenStream(TokenStream):
    def __init__(self, input, dbg=None):
        super().__init__()
        self.input = input
        self.initialStreamState = True
        # Track the last mark() call result value for use in rewind().
        self.lastMarker = None

        self._dbg = None
        self.setDebugListener(dbg)

        # force TokenStream to get at least first valid token
        # so we know if there are any hidden tokens first in the stream
        self.input.LT(1)


    def getDebugListener(self):
        return self._dbg

    def setDebugListener(self, dbg):
        self._dbg = dbg

    dbg = property(getDebugListener, setDebugListener)


    def consume(self):
        if self.initialStreamState:
            self.consumeInitialHiddenTokens()

        a = self.input.index()
        t = self.input.LT(1)
        self.input.consume()
        b = self.input.index()
        self._dbg.consumeToken(t)

        if b > a + 1:
            # then we consumed more than one token; must be off channel tokens
            for idx in range(a + 1, b):
                self._dbg.consumeHiddenToken(self.input.get(idx))


    def consumeInitialHiddenTokens(self):
        """consume all initial off-channel tokens"""

        firstOnChannelTokenIndex = self.input.index()
        for idx in range(firstOnChannelTokenIndex):
            self._dbg.consumeHiddenToken(self.input.get(idx))

        self.initialStreamState = False


    def LT(self, i):
        if self.initialStreamState:
            self.consumeInitialHiddenTokens()

        t = self.input.LT(i)
        self._dbg.LT(i, t)
        return t


    def LA(self, i):
        if self.initialStreamState:
            self.consumeInitialHiddenTokens()

        t = self.input.LT(i)
        self._dbg.LT(i, t)
        return t.type


    def get(self, i):
        return self.input.get(i)


    def index(self):
        return self.input.index()


    def mark(self):
        self.lastMarker = self.input.mark()
        self._dbg.mark(self.lastMarker)
        return self.lastMarker


    def rewind(self, marker=None):
        self._dbg.rewind(marker)
        self.input.rewind(marker)


    def release(self, marker):
        pass


    def seek(self, index):
        # TODO: implement seek in dbg interface
        # self._dbg.seek(index);
        self.input.seek(index)


    def size(self):
        return self.input.size()


    def getTokenSource(self):
        return self.input.getTokenSource()


    def getSourceName(self):
        return self.getTokenSource().getSourceName()


    def toString(self, start=None, stop=None):
        return self.input.toString(start, stop)


class DebugTreeAdaptor(TreeAdaptor):
    """A TreeAdaptor proxy that fires debugging events to a DebugEventListener
    delegate and uses the TreeAdaptor delegate to do the actual work.  All
    AST events are triggered by this adaptor; no code gen changes are needed
    in generated rules.  Debugging events are triggered *after* invoking
    tree adaptor routines.

    Trees created with actions in rewrite actions like "-> ^(ADD {foo} {bar})"
    cannot be tracked as they might not use the adaptor to create foo, bar.
    The debug listener has to deal with tree node IDs for which it did
    not see a createNode event.  A single <unknown> node is sufficient even
    if it represents a whole tree.
    """

    def __init__(self, dbg, adaptor):
        super().__init__()
        self.dbg = dbg
        self.adaptor = adaptor


    def createWithPayload(self, payload):
        if payload.index < 0:
            # could be token conjured up during error recovery
            return self.createFromType(payload.type, payload.text)

        node = self.adaptor.createWithPayload(payload)
        self.dbg.createNode(node, payload)
        return node

    def createFromToken(self, tokenType, fromToken, text=None):
        node = self.adaptor.createFromToken(tokenType, fromToken, text)
        self.dbg.createNode(node)
        return node

    def createFromType(self, tokenType, text):
        node = self.adaptor.createFromType(tokenType, text)
        self.dbg.createNode(node)
        return node


    def errorNode(self, input, start, stop, exc):
        node = self.adaptor.errorNode(input, start, stop, exc)
        if node is not None:
            self.dbg.errorNode(node)

        return node


    def dupTree(self, tree):
        t = self.adaptor.dupTree(tree)
        # walk the tree and emit create and add child events
        # to simulate what dupTree has done. dupTree does not call this debug
        # adapter so I must simulate.
        self.simulateTreeConstruction(t)
        return t


    def simulateTreeConstruction(self, t):
        """^(A B C): emit create A, create B, add child, ..."""
        self.dbg.createNode(t)
        for i in range(self.adaptor.getChildCount(t)):
            child = self.adaptor.getChild(t, i)
            self.simulateTreeConstruction(child)
            self.dbg.addChild(t, child)


    def dupNode(self, treeNode):
        d = self.adaptor.dupNode(treeNode)
        self.dbg.createNode(d)
        return d


    def nil(self):
        node = self.adaptor.nil()
        self.dbg.nilNode(node)
        return node


    def isNil(self, tree):
        return self.adaptor.isNil(tree)


    def addChild(self, t, child):
        if isinstance(child, Token):
            n = self.createWithPayload(child)
            self.addChild(t, n)

        else:
            if t is None or child is None:
                return

            self.adaptor.addChild(t, child)
            self.dbg.addChild(t, child)

    def becomeRoot(self, newRoot, oldRoot):
        if isinstance(newRoot, Token):
            n = self.createWithPayload(newRoot)
            self.adaptor.becomeRoot(n, oldRoot)
        else:
            n = self.adaptor.becomeRoot(newRoot, oldRoot)

        self.dbg.becomeRoot(newRoot, oldRoot)
        return n


    def rulePostProcessing(self, root):
        return self.adaptor.rulePostProcessing(root)


    def getType(self, t):
        return self.adaptor.getType(t)


    def setType(self, t, type):
        self.adaptor.setType(t, type)


    def getText(self, t):
        return self.adaptor.getText(t)


    def setText(self, t, text):
        self.adaptor.setText(t, text)


    def getToken(self, t):
        return self.adaptor.getToken(t)


    def setTokenBoundaries(self, t, startToken, stopToken):
        self.adaptor.setTokenBoundaries(t, startToken, stopToken)
        if t and startToken and stopToken:
            self.dbg.setTokenBoundaries(
                t, startToken.index, stopToken.index)


    def getTokenStartIndex(self, t):
        return self.adaptor.getTokenStartIndex(t)


    def getTokenStopIndex(self, t):
        return self.adaptor.getTokenStopIndex(t)


    def getChild(self, t, i):
        return self.adaptor.getChild(t, i)


    def setChild(self, t, i, child):
        self.adaptor.setChild(t, i, child)


    def deleteChild(self, t, i):
        return self.adaptor.deleteChild(t, i)


    def getChildCount(self, t):
        return self.adaptor.getChildCount(t)


    def getUniqueID(self, node):
        return self.adaptor.getUniqueID(node)


    def getParent(self, t):
        return self.adaptor.getParent(t)


    def getChildIndex(self, t):
        return self.adaptor.getChildIndex(t)


    def setParent(self, t, parent):
        self.adaptor.setParent(t, parent)


    def setChildIndex(self, t, index):
        self.adaptor.setChildIndex(t, index)


    def replaceChildren(self, parent, startChildIndex, stopChildIndex, t):
        self.adaptor.replaceChildren(parent, startChildIndex, stopChildIndex, t)


    ## support

    def getDebugListener(self):
        return self.dbg

    def setDebugListener(self, dbg):
        self.dbg = dbg


    def getTreeAdaptor(self):
        return self.adaptor



class DebugEventListener(object):
    """All debugging events that a recognizer can trigger.

    I did not create a separate AST debugging interface as it would create
    lots of extra classes and DebugParser has a dbg var defined, which makes
    it hard to change to ASTDebugEventListener.  I looked hard at this issue
    and it is easier to understand as one monolithic event interface for all
    possible events.  Hopefully, adding ST debugging stuff won't be bad.  Leave
    for future. 4/26/2006.
    """

    # Moved to version 2 for v3.1: added grammar name to enter/exit Rule
    PROTOCOL_VERSION = "2"

    def enterRule(self, grammarFileName, ruleName):
        """The parser has just entered a rule. No decision has been made about
        which alt is predicted.  This is fired AFTER init actions have been
        executed.  Attributes are defined and available etc...
        The grammarFileName allows composite grammars to jump around among
        multiple grammar files.
        """

        pass


    def enterAlt(self, alt):
        """Because rules can have lots of alternatives, it is very useful to
        know which alt you are entering.  This is 1..n for n alts.
        """
        pass


    def exitRule(self, grammarFileName, ruleName):
        """This is the last thing executed before leaving a rule.  It is
        executed even if an exception is thrown.  This is triggered after
        error reporting and recovery have occurred (unless the exception is
        not caught in this rule).  This implies an "exitAlt" event.
        The grammarFileName allows composite grammars to jump around among
        multiple grammar files.
        """
        pass


    def enterSubRule(self, decisionNumber):
        """Track entry into any (...) subrule other EBNF construct"""
        pass


    def exitSubRule(self, decisionNumber):
        pass


    def enterDecision(self, decisionNumber, couldBacktrack):
        """Every decision, fixed k or arbitrary, has an enter/exit event
        so that a GUI can easily track what LT/consume events are
        associated with prediction.  You will see a single enter/exit
        subrule but multiple enter/exit decision events, one for each
        loop iteration.
        """
        pass


    def exitDecision(self, decisionNumber):
        pass


    def consumeToken(self, t):
        """An input token was consumed; matched by any kind of element.
        Trigger after the token was matched by things like match(), matchAny().
        """
        pass


    def consumeHiddenToken(self, t):
        """An off-channel input token was consumed.
        Trigger after the token was matched by things like match(), matchAny().
        (unless of course the hidden token is first stuff in the input stream).
        """
        pass


    def LT(self, i, t):
        """Somebody (anybody) looked ahead.  Note that this actually gets
        triggered by both LA and LT calls.  The debugger will want to know
        which Token object was examined.  Like consumeToken, this indicates
        what token was seen at that depth.  A remote debugger cannot look
        ahead into a file it doesn't have so LT events must pass the token
        even if the info is redundant.
        For tree parsers, if the type is UP or DOWN,
        then the ID is not really meaningful as it's fixed--there is
        just one UP node and one DOWN navigation node.
        """
        pass


    def mark(self, marker):
        """The parser is going to look arbitrarily ahead; mark this location,
        the token stream's marker is sent in case you need it.
        """
        pass


    def rewind(self, marker=None):
        """After an arbitrairly long lookahead as with a cyclic DFA (or with
        any backtrack), this informs the debugger that stream should be
        rewound to the position associated with marker.

        """
        pass


    def beginBacktrack(self, level):
        pass


    def endBacktrack(self, level, successful):
        pass


    def location(self, line, pos):
        """To watch a parser move through the grammar, the parser needs to
        inform the debugger what line/charPos it is passing in the grammar.
        For now, this does not know how to switch from one grammar to the
        other and back for island grammars etc...

        This should also allow breakpoints because the debugger can stop
        the parser whenever it hits this line/pos.
        """
        pass


    def recognitionException(self, e):
        """A recognition exception occurred such as NoViableAltException.  I made
        this a generic event so that I can alter the exception hierachy later
        without having to alter all the debug objects.

        Upon error, the stack of enter rule/subrule must be properly unwound.
        If no viable alt occurs it is within an enter/exit decision, which
        also must be rewound.  Even the rewind for each mark must be unwount.
        In the Java target this is pretty easy using try/finally, if a bit
        ugly in the generated code.  The rewind is generated in DFA.predict()
        actually so no code needs to be generated for that.  For languages
        w/o this "finally" feature (C++?), the target implementor will have
        to build an event stack or something.

        Across a socket for remote debugging, only the RecognitionException
        data fields are transmitted.  The token object or whatever that
        caused the problem was the last object referenced by LT.  The
        immediately preceding LT event should hold the unexpected Token or
        char.

        Here is a sample event trace for grammar:

        b : C ({;}A|B) // {;} is there to prevent A|B becoming a set
          | D
          ;

        The sequence for this rule (with no viable alt in the subrule) for
        input 'c c' (there are 3 tokens) is:

                commence
                LT(1)
                enterRule b
                location 7 1
                enter decision 3
                LT(1)
                exit decision 3
                enterAlt1
                location 7 5
                LT(1)
                consumeToken [c/<4>,1:0]
                location 7 7
                enterSubRule 2
                enter decision 2
                LT(1)
                LT(1)
                recognitionException NoViableAltException 2 1 2
                exit decision 2
                exitSubRule 2
                beginResync
                LT(1)
                consumeToken [c/<4>,1:1]
                LT(1)
                endResync
                LT(-1)
                exitRule b
                terminate
        """
        pass


    def beginResync(self):
        """Indicates the recognizer is about to consume tokens to resynchronize
        the parser.  Any consume events from here until the recovered event
        are not part of the parse--they are dead tokens.
        """
        pass


    def endResync(self):
        """Indicates that the recognizer has finished consuming tokens in order
        to resychronize.  There may be multiple beginResync/endResync pairs
        before the recognizer comes out of errorRecovery mode (in which
        multiple errors are suppressed).  This will be useful
        in a gui where you want to probably grey out tokens that are consumed
        but not matched to anything in grammar.  Anything between
        a beginResync/endResync pair was tossed out by the parser.
        """
        pass


    def semanticPredicate(self, result, predicate):
        """A semantic predicate was evaluate with this result and action text"""
        pass


    def commence(self):
        """Announce that parsing has begun.  Not technically useful except for
        sending events over a socket.  A GUI for example will launch a thread
        to connect and communicate with a remote parser.  The thread will want
        to notify the GUI when a connection is made.  ANTLR parsers
        trigger this upon entry to the first rule (the ruleLevel is used to
        figure this out).
        """
        pass


    def terminate(self):
        """Parsing is over; successfully or not.  Mostly useful for telling
        remote debugging listeners that it's time to quit.  When the rule
        invocation level goes to zero at the end of a rule, we are done
        parsing.
        """
        pass


    ## T r e e  P a r s i n g

    def consumeNode(self, t):
        """Input for a tree parser is an AST, but we know nothing for sure
        about a node except its type and text (obtained from the adaptor).
        This is the analog of the consumeToken method.  Again, the ID is
        the hashCode usually of the node so it only works if hashCode is
        not implemented.  If the type is UP or DOWN, then
        the ID is not really meaningful as it's fixed--there is
        just one UP node and one DOWN navigation node.
        """
        pass


    ## A S T  E v e n t s

    def nilNode(self, t):
        """A nil was created (even nil nodes have a unique ID...
        they are not "null" per se).  As of 4/28/2006, this
        seems to be uniquely triggered when starting a new subtree
        such as when entering a subrule in automatic mode and when
        building a tree in rewrite mode.

        If you are receiving this event over a socket via
        RemoteDebugEventSocketListener then only t.ID is set.
        """
        pass


    def errorNode(self, t):
        """Upon syntax error, recognizers bracket the error with an error node
        if they are building ASTs.
        """
        pass


    def createNode(self, node, token=None):
        """Announce a new node built from token elements such as type etc...

        If you are receiving this event over a socket via
        RemoteDebugEventSocketListener then only t.ID, type, text are
        set.
        """
        pass


    def becomeRoot(self, newRoot, oldRoot):
        """Make a node the new root of an existing root.

        Note: the newRootID parameter is possibly different
        than the TreeAdaptor.becomeRoot() newRoot parameter.
        In our case, it will always be the result of calling
        TreeAdaptor.becomeRoot() and not root_n or whatever.

        The listener should assume that this event occurs
        only when the current subrule (or rule) subtree is
        being reset to newRootID.

        If you are receiving this event over a socket via
        RemoteDebugEventSocketListener then only IDs are set.

        @see antlr3.tree.TreeAdaptor.becomeRoot()
        """
        pass


    def addChild(self, root, child):
        """Make childID a child of rootID.

        If you are receiving this event over a socket via
        RemoteDebugEventSocketListener then only IDs are set.

        @see antlr3.tree.TreeAdaptor.addChild()
        """
        pass


    def setTokenBoundaries(self, t, tokenStartIndex, tokenStopIndex):
        """Set the token start/stop token index for a subtree root or node.

        If you are receiving this event over a socket via
        RemoteDebugEventSocketListener then only t.ID is set.
        """
        pass


class BlankDebugEventListener(DebugEventListener):
    """A blank listener that does nothing; useful for real classes so
    they don't have to have lots of blank methods and are less
    sensitive to updates to debug interface.

    Note: this class is identical to DebugEventListener and exists purely
    for compatibility with Java.
    """
    pass


class TraceDebugEventListener(DebugEventListener):
    """A listener that simply records text representations of the events.

    Useful for debugging the debugging facility ;)

    Subclasses can override the record() method (which defaults to printing to
    stdout) to record the events in a different way.
    """

    def __init__(self, adaptor=None):
        super().__init__()

        if adaptor is None:
            adaptor = CommonTreeAdaptor()
        self.adaptor = adaptor

    def record(self, event):
        sys.stdout.write(event + '\n')

    def enterRule(self, grammarFileName, ruleName):
        self.record("enterRule " + ruleName)

    def exitRule(self, grammarFileName, ruleName):
        self.record("exitRule " + ruleName)

    def enterSubRule(self, decisionNumber):
        self.record("enterSubRule")

    def exitSubRule(self, decisionNumber):
        self.record("exitSubRule")

    def location(self, line, pos):
        self.record("location {}:{}".format(line, pos))

    ## Tree parsing stuff

    def consumeNode(self, t):
        self.record("consumeNode {} {} {}".format(
                self.adaptor.getUniqueID(t),
                self.adaptor.getText(t),
                self.adaptor.getType(t)))

    def LT(self, i, t):
        self.record("LT {} {} {} {}".format(
                i,
                self.adaptor.getUniqueID(t),
                self.adaptor.getText(t),
                self.adaptor.getType(t)))


    ## AST stuff
    def nilNode(self, t):
        self.record("nilNode {}".format(self.adaptor.getUniqueID(t)))

    def createNode(self, t, token=None):
        if token is None:
            self.record("create {}: {}, {}".format(
                    self.adaptor.getUniqueID(t),
                    self.adaptor.getText(t),
                    self.adaptor.getType(t)))

        else:
            self.record("create {}: {}".format(
                    self.adaptor.getUniqueID(t),
                    token.index))

    def becomeRoot(self, newRoot, oldRoot):
        self.record("becomeRoot {}, {}".format(
                self.adaptor.getUniqueID(newRoot),
                self.adaptor.getUniqueID(oldRoot)))

    def addChild(self, root, child):
        self.record("addChild {}, {}".format(
                self.adaptor.getUniqueID(root),
                self.adaptor.getUniqueID(child)))

    def setTokenBoundaries(self, t, tokenStartIndex, tokenStopIndex):
        self.record("setTokenBoundaries {}, {}, {}".format(
                self.adaptor.getUniqueID(t),
                tokenStartIndex, tokenStopIndex))


class RecordDebugEventListener(TraceDebugEventListener):
    """A listener that records events as strings in an array."""

    def __init__(self, adaptor=None):
        super().__init__(adaptor)

        self.events = []

    def record(self, event):
        self.events.append(event)


class DebugEventSocketProxy(DebugEventListener):
    """A proxy debug event listener that forwards events over a socket to
    a debugger (or any other listener) using a simple text-based protocol;
    one event per line.  ANTLRWorks listens on server socket with a
    RemoteDebugEventSocketListener instance.  These two objects must therefore
    be kept in sync.  New events must be handled on both sides of socket.
    """

    DEFAULT_DEBUGGER_PORT = 49100

    def __init__(self, recognizer, adaptor=None, port=None, debug=None):
        super().__init__()

        self.grammarFileName = recognizer.getGrammarFileName()

        # Almost certainly the recognizer will have adaptor set, but
        # we don't know how to cast it (Parser or TreeParser) to get
        # the adaptor field.  Must be set with a constructor. :(
        self.adaptor = adaptor

        self.port = port or self.DEFAULT_DEBUGGER_PORT

        self.debug = debug

        self.socket = None
        self.connection = None
        self.input = None
        self.output = None


    def log(self, msg):
        if self.debug:
            self.debug.write(msg + '\n')


    def handshake(self):
        if self.socket is None:
            # create listening socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.port))
            self.socket.listen(1)
            self.log("Waiting for incoming connection on port {}".format(self.port))

            # wait for an incoming connection
            self.connection, addr = self.socket.accept()
            self.log("Accepted connection from {}:{}".format(addr[0], addr[1]))

            self.connection.setblocking(1)
            self.connection.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

            self.output = self.connection.makefile('w', 1)
            self.input = self.connection.makefile('r', 1)

            self.write("ANTLR {}".format(self.PROTOCOL_VERSION))
            self.write('grammar "{}"'.format(self.grammarFileName))
            self.ack()


    def write(self, msg):
        self.log("> {}".format(msg))
        self.output.write("{}\n".format(msg))
        self.output.flush()


    def ack(self):
        t = self.input.readline()
        self.log("< {}".format(t.rstrip()))


    def transmit(self, event):
        self.write(event)
        self.ack()


    def commence(self):
        # don't bother sending event; listener will trigger upon connection
        pass


    def terminate(self):
        self.transmit("terminate")
        self.output.close()
        self.input.close()
        self.connection.close()
        self.socket.close()


    def enterRule(self, grammarFileName, ruleName):
        self.transmit("enterRule\t{}\t{}".format(grammarFileName, ruleName))


    def enterAlt(self, alt):
        self.transmit("enterAlt\t{}".format(alt))


    def exitRule(self, grammarFileName, ruleName):
        self.transmit("exitRule\t{}\t{}".format(grammarFileName, ruleName))


    def enterSubRule(self, decisionNumber):
        self.transmit("enterSubRule\t{}".format(decisionNumber))


    def exitSubRule(self, decisionNumber):
        self.transmit("exitSubRule\t{}".format(decisionNumber))


    def enterDecision(self, decisionNumber, couldBacktrack):
        self.transmit(
            "enterDecision\t{}\t{:d}".format(decisionNumber, couldBacktrack))


    def exitDecision(self, decisionNumber):
        self.transmit("exitDecision\t{}".format(decisionNumber))


    def consumeToken(self, t):
        self.transmit("consumeToken\t{}".format(self.serializeToken(t)))


    def consumeHiddenToken(self, t):
        self.transmit("consumeHiddenToken\t{}".format(self.serializeToken(t)))


    def LT(self, i, o):
        if isinstance(o, Tree):
            return self.LT_tree(i, o)
        return self.LT_token(i, o)


    def LT_token(self, i, t):
        if t is not None:
            self.transmit("LT\t{}\t{}".format(i, self.serializeToken(t)))


    def mark(self, i):
        self.transmit("mark\t{}".format(i))


    def rewind(self, i=None):
        if i is not None:
            self.transmit("rewind\t{}".format(i))
        else:
            self.transmit("rewind")


    def beginBacktrack(self, level):
        self.transmit("beginBacktrack\t{}".format(level))


    def endBacktrack(self, level, successful):
        self.transmit("endBacktrack\t{}\t{}".format(
                level, '1' if successful else '0'))


    def location(self, line, pos):
        self.transmit("location\t{}\t{}".format(line, pos))


    def recognitionException(self, exc):
        self.transmit('\t'.join([
                    "exception",
                    exc.__class__.__name__,
                    str(int(exc.index)),
                    str(int(exc.line)),
                    str(int(exc.charPositionInLine))]))


    def beginResync(self):
        self.transmit("beginResync")


    def endResync(self):
        self.transmit("endResync")


    def semanticPredicate(self, result, predicate):
        self.transmit('\t'.join([
                    "semanticPredicate",
                    str(int(result)),
                    self.escapeNewlines(predicate)]))

    ## A S T  P a r s i n g  E v e n t s

    def consumeNode(self, t):
        FIXME(31)
#         StringBuffer buf = new StringBuffer(50);
#         buf.append("consumeNode");
#         serializeNode(buf, t);
#         transmit(buf.toString());


    def LT_tree(self, i, t):
        FIXME(34)
#         int ID = adaptor.getUniqueID(t);
#         String text = adaptor.getText(t);
#         int type = adaptor.getType(t);
#         StringBuffer buf = new StringBuffer(50);
#         buf.append("LN\t"); // lookahead node; distinguish from LT in protocol
#         buf.append(i);
#         serializeNode(buf, t);
#         transmit(buf.toString());


    def serializeNode(self, buf, t):
        FIXME(33)
#         int ID = adaptor.getUniqueID(t);
#         String text = adaptor.getText(t);
#         int type = adaptor.getType(t);
#         buf.append("\t");
#         buf.append(ID);
#         buf.append("\t");
#         buf.append(type);
#         Token token = adaptor.getToken(t);
#         int line = -1;
#         int pos = -1;
#         if ( token!=null ) {
#             line = token.getLine();
#             pos = token.getCharPositionInLine();
#             }
#         buf.append("\t");
#         buf.append(line);
#         buf.append("\t");
#         buf.append(pos);
#         int tokenIndex = adaptor.getTokenStartIndex(t);
#         buf.append("\t");
#         buf.append(tokenIndex);
#         serializeText(buf, text);


    ## A S T  E v e n t s

    def nilNode(self, t):
        self.transmit("nilNode\t{}".format(self.adaptor.getUniqueID(t)))


    def errorNode(self, t):
        self.transmit('errorNode\t{}\t{}\t"{}'.format(
             self.adaptor.getUniqueID(t),
             INVALID_TOKEN_TYPE,
             self.escapeNewlines(t.toString())))


    def createNode(self, node, token=None):
        if token is not None:
            self.transmit("createNode\t{}\t{}".format(
                    self.adaptor.getUniqueID(node),
                    token.index))

        else:
            self.transmit('createNodeFromTokenElements\t{}\t{}\t"{}'.format(
                    self.adaptor.getUniqueID(node),
                    self.adaptor.getType(node),
                    self.adaptor.getText(node)))


    def becomeRoot(self, newRoot, oldRoot):
        self.transmit("becomeRoot\t{}\t{}".format(
                self.adaptor.getUniqueID(newRoot),
                self.adaptor.getUniqueID(oldRoot)))


    def addChild(self, root, child):
        self.transmit("addChild\t{}\t{}".format(
                self.adaptor.getUniqueID(root),
                self.adaptor.getUniqueID(child)))


    def setTokenBoundaries(self, t, tokenStartIndex, tokenStopIndex):
        self.transmit("setTokenBoundaries\t{}\t{}\t{}".format(
                self.adaptor.getUniqueID(t),
                tokenStartIndex, tokenStopIndex))



    ## support

    def setTreeAdaptor(self, adaptor):
        self.adaptor = adaptor

    def getTreeAdaptor(self):
        return self.adaptor


    def serializeToken(self, t):
        buf = [str(int(t.index)),
               str(int(t.type)),
               str(int(t.channel)),
               str(int(t.line or 0)),
               str(int(t.charPositionInLine or 0)),
               '"' + self.escapeNewlines(t.text)]
        return '\t'.join(buf)


    def escapeNewlines(self, txt):
        if txt is None:
            return ''

        txt = txt.replace("%","%25")   # escape all escape char ;)
        txt = txt.replace("\n","%0A")  # escape \n
        txt = txt.replace("\r","%0D")  # escape \r
        return txt
