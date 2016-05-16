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


import sys
from google.appengine._internal.antlr3 import *
from google.appengine._internal.antlr3.compat import set, frozenset

from google.appengine._internal.antlr3.tree import *




HIDDEN = BaseRecognizer.HIDDEN


REWRITE=31
NUMBER_PREFIX=40
UNICODE_ESC=34
TEXT=32
VALUE=15
MINUS=38
BACKSLASH=37
DISJUNCTION=6
OCTAL_ESC=35
LITERAL=11
TEXT_ESC=41
LPAREN=24
RPAREN=25
EQ=22
FUNCTION=8
NOT=28
NE=21
AND=26
QUOTE=33
ESCAPED_CHAR=44
ARGS=4
MID_CHAR=42
START_CHAR=39
ESC=36
SEQUENCE=14
GLOBAL=10
HEX_DIGIT=45
WS=16
EOF=-1
EMPTY=7
GE=19
COMMA=29
OR=27
FUZZY=9
NEGATION=12
GT=20
DIGIT=43
CONJUNCTION=5
FIX=30
EXCLAMATION=46
LESSTHAN=18
STRING=13
LE=17
HAS=23


tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "ARGS", "CONJUNCTION", "DISJUNCTION", "EMPTY", "FUNCTION", "FUZZY",
    "GLOBAL", "LITERAL", "NEGATION", "STRING", "SEQUENCE", "VALUE", "WS",
    "LE", "LESSTHAN", "GE", "GT", "NE", "EQ", "HAS", "LPAREN", "RPAREN",
    "AND", "OR", "NOT", "COMMA", "FIX", "REWRITE", "TEXT", "QUOTE", "UNICODE_ESC",
    "OCTAL_ESC", "ESC", "BACKSLASH", "MINUS", "START_CHAR", "NUMBER_PREFIX",
    "TEXT_ESC", "MID_CHAR", "DIGIT", "ESCAPED_CHAR", "HEX_DIGIT", "EXCLAMATION"
]




class QueryParser(Parser):
    grammarFileName = ""
    antlr_version = version_str_to_tuple("3.1.1")
    antlr_version_str = "3.1.1"
    tokenNames = tokenNames

    def __init__(self, input, state=None):
        if state is None:
            state = RecognizerSharedState()

        Parser.__init__(self, input, state)


        self.dfa4 = self.DFA4(
            self, 4,
            eot = self.DFA4_eot,
            eof = self.DFA4_eof,
            min = self.DFA4_min,
            max = self.DFA4_max,
            accept = self.DFA4_accept,
            special = self.DFA4_special,
            transition = self.DFA4_transition
            )

        self.dfa6 = self.DFA6(
            self, 6,
            eot = self.DFA6_eot,
            eof = self.DFA6_eof,
            min = self.DFA6_min,
            max = self.DFA6_max,
            accept = self.DFA6_accept,
            special = self.DFA6_special,
            transition = self.DFA6_transition
            )

        self.dfa5 = self.DFA5(
            self, 5,
            eot = self.DFA5_eot,
            eof = self.DFA5_eof,
            min = self.DFA5_min,
            max = self.DFA5_max,
            accept = self.DFA5_accept,
            special = self.DFA5_special,
            transition = self.DFA5_transition
            )

        self.dfa9 = self.DFA9(
            self, 9,
            eot = self.DFA9_eot,
            eof = self.DFA9_eof,
            min = self.DFA9_min,
            max = self.DFA9_max,
            accept = self.DFA9_accept,
            special = self.DFA9_special,
            transition = self.DFA9_transition
            )

        self.dfa8 = self.DFA8(
            self, 8,
            eot = self.DFA8_eot,
            eof = self.DFA8_eof,
            min = self.DFA8_min,
            max = self.DFA8_max,
            accept = self.DFA8_accept,
            special = self.DFA8_special,
            transition = self.DFA8_transition
            )

        self.dfa11 = self.DFA11(
            self, 11,
            eot = self.DFA11_eot,
            eof = self.DFA11_eof,
            min = self.DFA11_min,
            max = self.DFA11_max,
            accept = self.DFA11_accept,
            special = self.DFA11_special,
            transition = self.DFA11_transition
            )

        self.dfa10 = self.DFA10(
            self, 10,
            eot = self.DFA10_eot,
            eof = self.DFA10_eof,
            min = self.DFA10_min,
            max = self.DFA10_max,
            accept = self.DFA10_accept,
            special = self.DFA10_special,
            transition = self.DFA10_transition
            )

        self.dfa14 = self.DFA14(
            self, 14,
            eot = self.DFA14_eot,
            eof = self.DFA14_eof,
            min = self.DFA14_min,
            max = self.DFA14_max,
            accept = self.DFA14_accept,
            special = self.DFA14_special,
            transition = self.DFA14_transition
            )







        self._adaptor = CommonTreeAdaptor()



    def getTreeAdaptor(self):
        return self._adaptor

    def setTreeAdaptor(self, adaptor):
        self._adaptor = adaptor

    adaptor = property(getTreeAdaptor, setTreeAdaptor)


    class query_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def query(self, ):

        retval = self.query_return()
        retval.start = self.input.LT(1)

        root_0 = None

        WS1 = None
        EOF2 = None
        WS3 = None
        WS5 = None
        EOF6 = None
        expression4 = None


        WS1_tree = None
        EOF2_tree = None
        WS3_tree = None
        WS5_tree = None
        EOF6_tree = None
        stream_WS = RewriteRuleTokenStream(self._adaptor, "token WS")
        stream_EOF = RewriteRuleTokenStream(self._adaptor, "token EOF")
        stream_expression = RewriteRuleSubtreeStream(self._adaptor, "rule expression")
        try:
            try:

                alt4 = 2
                alt4 = self.dfa4.predict(self.input)
                if alt4 == 1:

                    pass

                    while True:
                        alt1 = 2
                        LA1_0 = self.input.LA(1)

                        if (LA1_0 == WS) :
                            alt1 = 1


                        if alt1 == 1:

                            pass
                            WS1=self.match(self.input, WS, self.FOLLOW_WS_in_query122)
                            stream_WS.add(WS1)


                        else:
                            break


                    EOF2=self.match(self.input, EOF, self.FOLLOW_EOF_in_query125)
                    stream_EOF.add(EOF2)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(EMPTY, "EMPTY"), root_1)

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt4 == 2:

                    pass

                    while True:
                        alt2 = 2
                        LA2_0 = self.input.LA(1)

                        if (LA2_0 == WS) :
                            alt2 = 1


                        if alt2 == 1:

                            pass
                            WS3=self.match(self.input, WS, self.FOLLOW_WS_in_query154)
                            stream_WS.add(WS3)


                        else:
                            break


                    self._state.following.append(self.FOLLOW_expression_in_query157)
                    expression4 = self.expression()

                    self._state.following.pop()
                    stream_expression.add(expression4.tree)

                    while True:
                        alt3 = 2
                        LA3_0 = self.input.LA(1)

                        if (LA3_0 == WS) :
                            alt3 = 1


                        if alt3 == 1:

                            pass
                            WS5=self.match(self.input, WS, self.FOLLOW_WS_in_query159)
                            stream_WS.add(WS5)


                        else:
                            break


                    EOF6=self.match(self.input, EOF, self.FOLLOW_EOF_in_query162)
                    stream_EOF.add(EOF6)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_expression.nextTree())



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class expression_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def expression(self, ):

        retval = self.expression_return()
        retval.start = self.input.LT(1)

        root_0 = None

        sequence7 = None

        andOp8 = None

        sequence9 = None


        stream_sequence = RewriteRuleSubtreeStream(self._adaptor, "rule sequence")
        stream_andOp = RewriteRuleSubtreeStream(self._adaptor, "rule andOp")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_sequence_in_expression185)
                sequence7 = self.sequence()

                self._state.following.pop()
                stream_sequence.add(sequence7.tree)

                alt6 = 2
                alt6 = self.dfa6.predict(self.input)
                if alt6 == 1:

                    pass







                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_sequence.nextTree())



                    retval.tree = root_0


                elif alt6 == 2:

                    pass

                    cnt5 = 0
                    while True:
                        alt5 = 2
                        alt5 = self.dfa5.predict(self.input)
                        if alt5 == 1:

                            pass
                            self._state.following.append(self.FOLLOW_andOp_in_expression222)
                            andOp8 = self.andOp()

                            self._state.following.pop()
                            stream_andOp.add(andOp8.tree)
                            self._state.following.append(self.FOLLOW_sequence_in_expression224)
                            sequence9 = self.sequence()

                            self._state.following.pop()
                            stream_sequence.add(sequence9.tree)


                        else:
                            if cnt5 >= 1:
                                break

                            eee = EarlyExitException(5, self.input)
                            raise eee

                        cnt5 += 1










                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(CONJUNCTION, "CONJUNCTION"), root_1)


                    if not (stream_sequence.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_sequence.hasNext():
                        self._adaptor.addChild(root_1, stream_sequence.nextTree())


                    stream_sequence.reset()

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class sequence_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def sequence(self, ):

        retval = self.sequence_return()
        retval.start = self.input.LT(1)

        root_0 = None

        WS11 = None
        factor10 = None

        factor12 = None


        WS11_tree = None
        stream_WS = RewriteRuleTokenStream(self._adaptor, "token WS")
        stream_factor = RewriteRuleSubtreeStream(self._adaptor, "rule factor")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_factor_in_sequence262)
                factor10 = self.factor()

                self._state.following.pop()
                stream_factor.add(factor10.tree)

                alt9 = 2
                alt9 = self.dfa9.predict(self.input)
                if alt9 == 1:

                    pass







                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_factor.nextTree())



                    retval.tree = root_0


                elif alt9 == 2:

                    pass

                    cnt8 = 0
                    while True:
                        alt8 = 2
                        alt8 = self.dfa8.predict(self.input)
                        if alt8 == 1:

                            pass

                            cnt7 = 0
                            while True:
                                alt7 = 2
                                LA7_0 = self.input.LA(1)

                                if (LA7_0 == WS) :
                                    alt7 = 1


                                if alt7 == 1:

                                    pass
                                    WS11=self.match(self.input, WS, self.FOLLOW_WS_in_sequence298)
                                    stream_WS.add(WS11)


                                else:
                                    if cnt7 >= 1:
                                        break

                                    eee = EarlyExitException(7, self.input)
                                    raise eee

                                cnt7 += 1


                            self._state.following.append(self.FOLLOW_factor_in_sequence301)
                            factor12 = self.factor()

                            self._state.following.pop()
                            stream_factor.add(factor12.tree)


                        else:
                            if cnt8 >= 1:
                                break

                            eee = EarlyExitException(8, self.input)
                            raise eee

                        cnt8 += 1










                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(SEQUENCE, "SEQUENCE"), root_1)


                    if not (stream_factor.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_factor.hasNext():
                        self._adaptor.addChild(root_1, stream_factor.nextTree())


                    stream_factor.reset()

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class factor_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def factor(self, ):

        retval = self.factor_return()
        retval.start = self.input.LT(1)

        root_0 = None

        term13 = None

        orOp14 = None

        term15 = None


        stream_orOp = RewriteRuleSubtreeStream(self._adaptor, "rule orOp")
        stream_term = RewriteRuleSubtreeStream(self._adaptor, "rule term")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_term_in_factor342)
                term13 = self.term()

                self._state.following.pop()
                stream_term.add(term13.tree)

                alt11 = 2
                alt11 = self.dfa11.predict(self.input)
                if alt11 == 1:

                    pass







                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_term.nextTree())



                    retval.tree = root_0


                elif alt11 == 2:

                    pass

                    cnt10 = 0
                    while True:
                        alt10 = 2
                        alt10 = self.dfa10.predict(self.input)
                        if alt10 == 1:

                            pass
                            self._state.following.append(self.FOLLOW_orOp_in_factor374)
                            orOp14 = self.orOp()

                            self._state.following.pop()
                            stream_orOp.add(orOp14.tree)
                            self._state.following.append(self.FOLLOW_term_in_factor376)
                            term15 = self.term()

                            self._state.following.pop()
                            stream_term.add(term15.tree)


                        else:
                            if cnt10 >= 1:
                                break

                            eee = EarlyExitException(10, self.input)
                            raise eee

                        cnt10 += 1










                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(DISJUNCTION, "DISJUNCTION"), root_1)


                    if not (stream_term.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_term.hasNext():
                        self._adaptor.addChild(root_1, stream_term.nextTree())


                    stream_term.reset()

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class term_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def term(self, ):

        retval = self.term_return()
        retval.start = self.input.LT(1)

        root_0 = None

        primitive16 = None

        notOp17 = None

        primitive18 = None


        stream_primitive = RewriteRuleSubtreeStream(self._adaptor, "rule primitive")
        stream_notOp = RewriteRuleSubtreeStream(self._adaptor, "rule notOp")
        try:
            try:

                alt12 = 2
                LA12_0 = self.input.LA(1)

                if (LA12_0 == LPAREN or (FIX <= LA12_0 <= QUOTE)) :
                    alt12 = 1
                elif (LA12_0 == NOT or LA12_0 == MINUS) :
                    alt12 = 2
                else:
                    nvae = NoViableAltException("", 12, 0, self.input)

                    raise nvae

                if alt12 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_primitive_in_term410)
                    primitive16 = self.primitive()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, primitive16.tree)


                elif alt12 == 2:

                    pass
                    self._state.following.append(self.FOLLOW_notOp_in_term416)
                    notOp17 = self.notOp()

                    self._state.following.pop()
                    stream_notOp.add(notOp17.tree)
                    self._state.following.append(self.FOLLOW_primitive_in_term418)
                    primitive18 = self.primitive()

                    self._state.following.pop()
                    stream_primitive.add(primitive18.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(NEGATION, "NEGATION"), root_1)

                    self._adaptor.addChild(root_1, stream_primitive.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class primitive_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def primitive(self, ):

        retval = self.primitive_return()
        retval.start = self.input.LT(1)

        root_0 = None

        restriction19 = None

        composite20 = None



        try:
            try:

                alt13 = 2
                LA13_0 = self.input.LA(1)

                if ((FIX <= LA13_0 <= QUOTE)) :
                    alt13 = 1
                elif (LA13_0 == LPAREN) :
                    alt13 = 2
                else:
                    nvae = NoViableAltException("", 13, 0, self.input)

                    raise nvae

                if alt13 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_restriction_in_primitive444)
                    restriction19 = self.restriction()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, restriction19.tree)


                elif alt13 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_composite_in_primitive450)
                    composite20 = self.composite()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, composite20.tree)


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class restriction_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def restriction(self, ):

        retval = self.restriction_return()
        retval.start = self.input.LT(1)

        root_0 = None

        comparable21 = None

        comparator22 = None

        arg23 = None


        stream_comparator = RewriteRuleSubtreeStream(self._adaptor, "rule comparator")
        stream_arg = RewriteRuleSubtreeStream(self._adaptor, "rule arg")
        stream_comparable = RewriteRuleSubtreeStream(self._adaptor, "rule comparable")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_comparable_in_restriction467)
                comparable21 = self.comparable()

                self._state.following.pop()
                stream_comparable.add(comparable21.tree)

                alt14 = 2
                alt14 = self.dfa14.predict(self.input)
                if alt14 == 1:

                    pass







                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(HAS, "HAS"), root_1)

                    self._adaptor.addChild(root_1, self._adaptor.createFromType(GLOBAL, "GLOBAL"))
                    self._adaptor.addChild(root_1, stream_comparable.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt14 == 2:

                    pass
                    self._state.following.append(self.FOLLOW_comparator_in_restriction502)
                    comparator22 = self.comparator()

                    self._state.following.pop()
                    stream_comparator.add(comparator22.tree)
                    self._state.following.append(self.FOLLOW_arg_in_restriction504)
                    arg23 = self.arg()

                    self._state.following.pop()
                    stream_arg.add(arg23.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(stream_comparator.nextNode(), root_1)

                    self._adaptor.addChild(root_1, stream_comparable.nextTree())
                    self._adaptor.addChild(root_1, stream_arg.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class comparator_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def comparator(self, ):

        retval = self.comparator_return()
        retval.start = self.input.LT(1)

        root_0 = None

        x = None
        WS24 = None
        WS25 = None

        x_tree = None
        WS24_tree = None
        WS25_tree = None
        stream_NE = RewriteRuleTokenStream(self._adaptor, "token NE")
        stream_LESSTHAN = RewriteRuleTokenStream(self._adaptor, "token LESSTHAN")
        stream_LE = RewriteRuleTokenStream(self._adaptor, "token LE")
        stream_HAS = RewriteRuleTokenStream(self._adaptor, "token HAS")
        stream_WS = RewriteRuleTokenStream(self._adaptor, "token WS")
        stream_EQ = RewriteRuleTokenStream(self._adaptor, "token EQ")
        stream_GT = RewriteRuleTokenStream(self._adaptor, "token GT")
        stream_GE = RewriteRuleTokenStream(self._adaptor, "token GE")

        try:
            try:


                pass

                while True:
                    alt15 = 2
                    LA15_0 = self.input.LA(1)

                    if (LA15_0 == WS) :
                        alt15 = 1


                    if alt15 == 1:

                        pass
                        WS24=self.match(self.input, WS, self.FOLLOW_WS_in_comparator534)
                        stream_WS.add(WS24)


                    else:
                        break



                alt16 = 7
                LA16 = self.input.LA(1)
                if LA16 == LE:
                    alt16 = 1
                elif LA16 == LESSTHAN:
                    alt16 = 2
                elif LA16 == GE:
                    alt16 = 3
                elif LA16 == GT:
                    alt16 = 4
                elif LA16 == NE:
                    alt16 = 5
                elif LA16 == EQ:
                    alt16 = 6
                elif LA16 == HAS:
                    alt16 = 7
                else:
                    nvae = NoViableAltException("", 16, 0, self.input)

                    raise nvae

                if alt16 == 1:

                    pass
                    x=self.match(self.input, LE, self.FOLLOW_LE_in_comparator540)
                    stream_LE.add(x)


                elif alt16 == 2:

                    pass
                    x=self.match(self.input, LESSTHAN, self.FOLLOW_LESSTHAN_in_comparator546)
                    stream_LESSTHAN.add(x)


                elif alt16 == 3:

                    pass
                    x=self.match(self.input, GE, self.FOLLOW_GE_in_comparator552)
                    stream_GE.add(x)


                elif alt16 == 4:

                    pass
                    x=self.match(self.input, GT, self.FOLLOW_GT_in_comparator558)
                    stream_GT.add(x)


                elif alt16 == 5:

                    pass
                    x=self.match(self.input, NE, self.FOLLOW_NE_in_comparator564)
                    stream_NE.add(x)


                elif alt16 == 6:

                    pass
                    x=self.match(self.input, EQ, self.FOLLOW_EQ_in_comparator570)
                    stream_EQ.add(x)


                elif alt16 == 7:

                    pass
                    x=self.match(self.input, HAS, self.FOLLOW_HAS_in_comparator576)
                    stream_HAS.add(x)




                while True:
                    alt17 = 2
                    LA17_0 = self.input.LA(1)

                    if (LA17_0 == WS) :
                        alt17 = 1


                    if alt17 == 1:

                        pass
                        WS25=self.match(self.input, WS, self.FOLLOW_WS_in_comparator579)
                        stream_WS.add(WS25)


                    else:
                        break










                retval.tree = root_0
                stream_x = RewriteRuleTokenStream(self._adaptor, "token x", x)

                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()

                self._adaptor.addChild(root_0, stream_x.nextNode())



                retval.tree = root_0



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class comparable_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def comparable(self, ):

        retval = self.comparable_return()
        retval.start = self.input.LT(1)

        root_0 = None

        member26 = None

        function27 = None



        try:
            try:

                alt18 = 2
                LA18_0 = self.input.LA(1)

                if ((FIX <= LA18_0 <= REWRITE) or LA18_0 == QUOTE) :
                    alt18 = 1
                elif (LA18_0 == TEXT) :
                    LA18_2 = self.input.LA(2)

                    if (LA18_2 == LPAREN) :
                        alt18 = 2
                    elif (LA18_2 == EOF or (WS <= LA18_2 <= HAS) or LA18_2 == RPAREN or LA18_2 == COMMA) :
                        alt18 = 1
                    else:
                        nvae = NoViableAltException("", 18, 2, self.input)

                        raise nvae

                else:
                    nvae = NoViableAltException("", 18, 0, self.input)

                    raise nvae

                if alt18 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_member_in_comparable601)
                    member26 = self.member()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, member26.tree)


                elif alt18 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_function_in_comparable607)
                    function27 = self.function()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, function27.tree)


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class member_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def member(self, ):

        retval = self.member_return()
        retval.start = self.input.LT(1)

        root_0 = None

        item28 = None



        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_item_in_member622)
                item28 = self.item()

                self._state.following.pop()
                self._adaptor.addChild(root_0, item28.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class function_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def function(self, ):

        retval = self.function_return()
        retval.start = self.input.LT(1)

        root_0 = None

        LPAREN30 = None
        RPAREN32 = None
        text29 = None

        arglist31 = None


        LPAREN30_tree = None
        RPAREN32_tree = None
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_arglist = RewriteRuleSubtreeStream(self._adaptor, "rule arglist")
        stream_text = RewriteRuleSubtreeStream(self._adaptor, "rule text")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_text_in_function639)
                text29 = self.text()

                self._state.following.pop()
                stream_text.add(text29.tree)
                LPAREN30=self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_function641)
                stream_LPAREN.add(LPAREN30)
                self._state.following.append(self.FOLLOW_arglist_in_function643)
                arglist31 = self.arglist()

                self._state.following.pop()
                stream_arglist.add(arglist31.tree)
                RPAREN32=self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_function645)
                stream_RPAREN.add(RPAREN32)








                retval.tree = root_0

                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()


                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(FUNCTION, "FUNCTION"), root_1)

                self._adaptor.addChild(root_1, stream_text.nextTree())

                root_2 = self._adaptor.nil()
                root_2 = self._adaptor.becomeRoot(self._adaptor.createFromType(ARGS, "ARGS"), root_2)

                self._adaptor.addChild(root_2, stream_arglist.nextTree())

                self._adaptor.addChild(root_1, root_2)

                self._adaptor.addChild(root_0, root_1)



                retval.tree = root_0



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class arglist_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def arglist(self, ):

        retval = self.arglist_return()
        retval.start = self.input.LT(1)

        root_0 = None

        arg33 = None

        sep34 = None

        arg35 = None


        stream_arg = RewriteRuleSubtreeStream(self._adaptor, "rule arg")
        stream_sep = RewriteRuleSubtreeStream(self._adaptor, "rule sep")
        try:
            try:

                alt20 = 2
                LA20_0 = self.input.LA(1)

                if (LA20_0 == RPAREN) :
                    alt20 = 1
                elif (LA20_0 == LPAREN or (FIX <= LA20_0 <= QUOTE)) :
                    alt20 = 2
                else:
                    nvae = NoViableAltException("", 20, 0, self.input)

                    raise nvae

                if alt20 == 1:

                    pass
                    root_0 = self._adaptor.nil()


                elif alt20 == 2:

                    pass
                    self._state.following.append(self.FOLLOW_arg_in_arglist680)
                    arg33 = self.arg()

                    self._state.following.pop()
                    stream_arg.add(arg33.tree)

                    while True:
                        alt19 = 2
                        LA19_0 = self.input.LA(1)

                        if (LA19_0 == WS or LA19_0 == COMMA) :
                            alt19 = 1


                        if alt19 == 1:

                            pass
                            self._state.following.append(self.FOLLOW_sep_in_arglist683)
                            sep34 = self.sep()

                            self._state.following.pop()
                            stream_sep.add(sep34.tree)
                            self._state.following.append(self.FOLLOW_arg_in_arglist685)
                            arg35 = self.arg()

                            self._state.following.pop()
                            stream_arg.add(arg35.tree)


                        else:
                            break










                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    while stream_arg.hasNext():
                        self._adaptor.addChild(root_0, stream_arg.nextTree())


                    stream_arg.reset();



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class arg_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def arg(self, ):

        retval = self.arg_return()
        retval.start = self.input.LT(1)

        root_0 = None

        comparable36 = None

        composite37 = None



        try:
            try:

                alt21 = 2
                LA21_0 = self.input.LA(1)

                if ((FIX <= LA21_0 <= QUOTE)) :
                    alt21 = 1
                elif (LA21_0 == LPAREN) :
                    alt21 = 2
                else:
                    nvae = NoViableAltException("", 21, 0, self.input)

                    raise nvae

                if alt21 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_comparable_in_arg706)
                    comparable36 = self.comparable()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, comparable36.tree)


                elif alt21 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_composite_in_arg712)
                    composite37 = self.composite()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, composite37.tree)


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class andOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def andOp(self, ):

        retval = self.andOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        WS38 = None
        AND39 = None
        WS40 = None

        WS38_tree = None
        AND39_tree = None
        WS40_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()


                cnt22 = 0
                while True:
                    alt22 = 2
                    LA22_0 = self.input.LA(1)

                    if (LA22_0 == WS) :
                        alt22 = 1


                    if alt22 == 1:

                        pass
                        WS38=self.match(self.input, WS, self.FOLLOW_WS_in_andOp726)

                        WS38_tree = self._adaptor.createWithPayload(WS38)
                        self._adaptor.addChild(root_0, WS38_tree)



                    else:
                        if cnt22 >= 1:
                            break

                        eee = EarlyExitException(22, self.input)
                        raise eee

                    cnt22 += 1


                AND39=self.match(self.input, AND, self.FOLLOW_AND_in_andOp729)

                AND39_tree = self._adaptor.createWithPayload(AND39)
                self._adaptor.addChild(root_0, AND39_tree)


                cnt23 = 0
                while True:
                    alt23 = 2
                    LA23_0 = self.input.LA(1)

                    if (LA23_0 == WS) :
                        alt23 = 1


                    if alt23 == 1:

                        pass
                        WS40=self.match(self.input, WS, self.FOLLOW_WS_in_andOp731)

                        WS40_tree = self._adaptor.createWithPayload(WS40)
                        self._adaptor.addChild(root_0, WS40_tree)



                    else:
                        if cnt23 >= 1:
                            break

                        eee = EarlyExitException(23, self.input)
                        raise eee

                    cnt23 += 1





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class orOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def orOp(self, ):

        retval = self.orOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        WS41 = None
        OR42 = None
        WS43 = None

        WS41_tree = None
        OR42_tree = None
        WS43_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()


                cnt24 = 0
                while True:
                    alt24 = 2
                    LA24_0 = self.input.LA(1)

                    if (LA24_0 == WS) :
                        alt24 = 1


                    if alt24 == 1:

                        pass
                        WS41=self.match(self.input, WS, self.FOLLOW_WS_in_orOp746)

                        WS41_tree = self._adaptor.createWithPayload(WS41)
                        self._adaptor.addChild(root_0, WS41_tree)



                    else:
                        if cnt24 >= 1:
                            break

                        eee = EarlyExitException(24, self.input)
                        raise eee

                    cnt24 += 1


                OR42=self.match(self.input, OR, self.FOLLOW_OR_in_orOp749)

                OR42_tree = self._adaptor.createWithPayload(OR42)
                self._adaptor.addChild(root_0, OR42_tree)


                cnt25 = 0
                while True:
                    alt25 = 2
                    LA25_0 = self.input.LA(1)

                    if (LA25_0 == WS) :
                        alt25 = 1


                    if alt25 == 1:

                        pass
                        WS43=self.match(self.input, WS, self.FOLLOW_WS_in_orOp751)

                        WS43_tree = self._adaptor.createWithPayload(WS43)
                        self._adaptor.addChild(root_0, WS43_tree)



                    else:
                        if cnt25 >= 1:
                            break

                        eee = EarlyExitException(25, self.input)
                        raise eee

                    cnt25 += 1





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class notOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def notOp(self, ):

        retval = self.notOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        char_literal44 = None
        NOT45 = None
        WS46 = None

        char_literal44_tree = None
        NOT45_tree = None
        WS46_tree = None

        try:
            try:

                alt27 = 2
                LA27_0 = self.input.LA(1)

                if (LA27_0 == MINUS) :
                    alt27 = 1
                elif (LA27_0 == NOT) :
                    alt27 = 2
                else:
                    nvae = NoViableAltException("", 27, 0, self.input)

                    raise nvae

                if alt27 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    char_literal44=self.match(self.input, MINUS, self.FOLLOW_MINUS_in_notOp766)

                    char_literal44_tree = self._adaptor.createWithPayload(char_literal44)
                    self._adaptor.addChild(root_0, char_literal44_tree)



                elif alt27 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    NOT45=self.match(self.input, NOT, self.FOLLOW_NOT_in_notOp772)

                    NOT45_tree = self._adaptor.createWithPayload(NOT45)
                    self._adaptor.addChild(root_0, NOT45_tree)


                    cnt26 = 0
                    while True:
                        alt26 = 2
                        LA26_0 = self.input.LA(1)

                        if (LA26_0 == WS) :
                            alt26 = 1


                        if alt26 == 1:

                            pass
                            WS46=self.match(self.input, WS, self.FOLLOW_WS_in_notOp774)

                            WS46_tree = self._adaptor.createWithPayload(WS46)
                            self._adaptor.addChild(root_0, WS46_tree)



                        else:
                            if cnt26 >= 1:
                                break

                            eee = EarlyExitException(26, self.input)
                            raise eee

                        cnt26 += 1




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class sep_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def sep(self, ):

        retval = self.sep_return()
        retval.start = self.input.LT(1)

        root_0 = None

        WS47 = None
        COMMA48 = None
        WS49 = None

        WS47_tree = None
        COMMA48_tree = None
        WS49_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()


                while True:
                    alt28 = 2
                    LA28_0 = self.input.LA(1)

                    if (LA28_0 == WS) :
                        alt28 = 1


                    if alt28 == 1:

                        pass
                        WS47=self.match(self.input, WS, self.FOLLOW_WS_in_sep789)

                        WS47_tree = self._adaptor.createWithPayload(WS47)
                        self._adaptor.addChild(root_0, WS47_tree)



                    else:
                        break


                COMMA48=self.match(self.input, COMMA, self.FOLLOW_COMMA_in_sep792)

                COMMA48_tree = self._adaptor.createWithPayload(COMMA48)
                self._adaptor.addChild(root_0, COMMA48_tree)


                while True:
                    alt29 = 2
                    LA29_0 = self.input.LA(1)

                    if (LA29_0 == WS) :
                        alt29 = 1


                    if alt29 == 1:

                        pass
                        WS49=self.match(self.input, WS, self.FOLLOW_WS_in_sep794)

                        WS49_tree = self._adaptor.createWithPayload(WS49)
                        self._adaptor.addChild(root_0, WS49_tree)



                    else:
                        break





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class composite_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def composite(self, ):

        retval = self.composite_return()
        retval.start = self.input.LT(1)

        root_0 = None

        LPAREN50 = None
        WS51 = None
        WS53 = None
        RPAREN54 = None
        expression52 = None


        LPAREN50_tree = None
        WS51_tree = None
        WS53_tree = None
        RPAREN54_tree = None
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_WS = RewriteRuleTokenStream(self._adaptor, "token WS")
        stream_expression = RewriteRuleSubtreeStream(self._adaptor, "rule expression")
        try:
            try:


                pass
                LPAREN50=self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_composite810)
                stream_LPAREN.add(LPAREN50)

                while True:
                    alt30 = 2
                    LA30_0 = self.input.LA(1)

                    if (LA30_0 == WS) :
                        alt30 = 1


                    if alt30 == 1:

                        pass
                        WS51=self.match(self.input, WS, self.FOLLOW_WS_in_composite812)
                        stream_WS.add(WS51)


                    else:
                        break


                self._state.following.append(self.FOLLOW_expression_in_composite815)
                expression52 = self.expression()

                self._state.following.pop()
                stream_expression.add(expression52.tree)

                while True:
                    alt31 = 2
                    LA31_0 = self.input.LA(1)

                    if (LA31_0 == WS) :
                        alt31 = 1


                    if alt31 == 1:

                        pass
                        WS53=self.match(self.input, WS, self.FOLLOW_WS_in_composite817)
                        stream_WS.add(WS53)


                    else:
                        break


                RPAREN54=self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_composite820)
                stream_RPAREN.add(RPAREN54)








                retval.tree = root_0

                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()

                self._adaptor.addChild(root_0, stream_expression.nextTree())



                retval.tree = root_0



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class item_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def item(self, ):

        retval = self.item_return()
        retval.start = self.input.LT(1)

        root_0 = None

        FIX55 = None
        REWRITE57 = None
        value56 = None

        value58 = None

        value59 = None


        FIX55_tree = None
        REWRITE57_tree = None
        stream_REWRITE = RewriteRuleTokenStream(self._adaptor, "token REWRITE")
        stream_FIX = RewriteRuleTokenStream(self._adaptor, "token FIX")
        stream_value = RewriteRuleSubtreeStream(self._adaptor, "rule value")
        try:
            try:

                alt32 = 3
                LA32 = self.input.LA(1)
                if LA32 == FIX:
                    alt32 = 1
                elif LA32 == REWRITE:
                    alt32 = 2
                elif LA32 == TEXT or LA32 == QUOTE:
                    alt32 = 3
                else:
                    nvae = NoViableAltException("", 32, 0, self.input)

                    raise nvae

                if alt32 == 1:

                    pass
                    FIX55=self.match(self.input, FIX, self.FOLLOW_FIX_in_item840)
                    stream_FIX.add(FIX55)
                    self._state.following.append(self.FOLLOW_value_in_item842)
                    value56 = self.value()

                    self._state.following.pop()
                    stream_value.add(value56.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(LITERAL, "LITERAL"), root_1)

                    self._adaptor.addChild(root_1, stream_value.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt32 == 2:

                    pass
                    REWRITE57=self.match(self.input, REWRITE, self.FOLLOW_REWRITE_in_item856)
                    stream_REWRITE.add(REWRITE57)
                    self._state.following.append(self.FOLLOW_value_in_item858)
                    value58 = self.value()

                    self._state.following.pop()
                    stream_value.add(value58.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(FUZZY, "FUZZY"), root_1)

                    self._adaptor.addChild(root_1, stream_value.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt32 == 3:

                    pass
                    self._state.following.append(self.FOLLOW_value_in_item872)
                    value59 = self.value()

                    self._state.following.pop()
                    stream_value.add(value59.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_value.nextTree())



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class value_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def value(self, ):

        retval = self.value_return()
        retval.start = self.input.LT(1)

        root_0 = None

        text60 = None

        phrase61 = None


        stream_phrase = RewriteRuleSubtreeStream(self._adaptor, "rule phrase")
        stream_text = RewriteRuleSubtreeStream(self._adaptor, "rule text")
        try:
            try:

                alt33 = 2
                LA33_0 = self.input.LA(1)

                if (LA33_0 == TEXT) :
                    alt33 = 1
                elif (LA33_0 == QUOTE) :
                    alt33 = 2
                else:
                    nvae = NoViableAltException("", 33, 0, self.input)

                    raise nvae

                if alt33 == 1:

                    pass
                    self._state.following.append(self.FOLLOW_text_in_value890)
                    text60 = self.text()

                    self._state.following.pop()
                    stream_text.add(text60.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(VALUE, "VALUE"), root_1)

                    self._adaptor.addChild(root_1, self._adaptor.createFromType(TEXT, "TEXT"))
                    self._adaptor.addChild(root_1, stream_text.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt33 == 2:

                    pass
                    self._state.following.append(self.FOLLOW_phrase_in_value906)
                    phrase61 = self.phrase()

                    self._state.following.pop()
                    stream_phrase.add(phrase61.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.createFromType(VALUE, "VALUE"), root_1)

                    self._adaptor.addChild(root_1, self._adaptor.createFromType(STRING, "STRING"))
                    self._adaptor.addChild(root_1, stream_phrase.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class text_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def text(self, ):

        retval = self.text_return()
        retval.start = self.input.LT(1)

        root_0 = None

        TEXT62 = None

        TEXT62_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                TEXT62=self.match(self.input, TEXT, self.FOLLOW_TEXT_in_text930)

                TEXT62_tree = self._adaptor.createWithPayload(TEXT62)
                self._adaptor.addChild(root_0, TEXT62_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval



    class phrase_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def phrase(self, ):

        retval = self.phrase_return()
        retval.start = self.input.LT(1)

        root_0 = None

        QUOTE63 = None
        set64 = None
        QUOTE65 = None

        QUOTE63_tree = None
        set64_tree = None
        QUOTE65_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                QUOTE63=self.match(self.input, QUOTE, self.FOLLOW_QUOTE_in_phrase944)

                QUOTE63_tree = self._adaptor.createWithPayload(QUOTE63)
                self._adaptor.addChild(root_0, QUOTE63_tree)


                while True:
                    alt34 = 2
                    LA34_0 = self.input.LA(1)

                    if ((ARGS <= LA34_0 <= TEXT) or (UNICODE_ESC <= LA34_0 <= EXCLAMATION)) :
                        alt34 = 1


                    if alt34 == 1:

                        pass
                        set64 = self.input.LT(1)
                        if (ARGS <= self.input.LA(1) <= TEXT) or (UNICODE_ESC <= self.input.LA(1) <= EXCLAMATION):
                            self.input.consume()
                            self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set64))
                            self._state.errorRecovery = False

                        else:
                            mse = MismatchedSetException(None, self.input)
                            raise mse




                    else:
                        break


                QUOTE65=self.match(self.input, QUOTE, self.FOLLOW_QUOTE_in_phrase950)

                QUOTE65_tree = self._adaptor.createWithPayload(QUOTE65)
                self._adaptor.addChild(root_0, QUOTE65_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)


            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)
        finally:

            pass

        return retval









    DFA4_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA4_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA4_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA4_max = DFA.unpack(
        u"\2\46\2\uffff"
        )

    DFA4_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA4_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA4_transition = [
        DFA.unpack(u"\1\1\7\uffff\1\3\3\uffff\1\3\1\uffff\4\3\4\uffff\1\3"),
        DFA.unpack(u"\1\1\7\uffff\1\3\3\uffff\1\3\1\uffff\4\3\4\uffff\1"
        u"\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA4 = DFA


    DFA6_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA6_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA6_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA6_max = DFA.unpack(
        u"\1\31\1\32\2\uffff"
        )

    DFA6_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA6_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA6_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\10\uffff\1\2\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA6 = DFA


    DFA5_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA5_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA5_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA5_max = DFA.unpack(
        u"\1\31\1\32\2\uffff"
        )

    DFA5_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1"
        )

    DFA5_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA5_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\10\uffff\1\2\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA5 = DFA


    DFA9_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA9_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA9_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA9_max = DFA.unpack(
        u"\1\31\1\46\2\uffff"
        )

    DFA9_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA9_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA9_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\7\uffff\1\3\2\2\1\uffff\1\3\1\uffff\4\3\4\uffff"
        u"\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA9 = DFA


    DFA8_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA8_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA8_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA8_max = DFA.unpack(
        u"\1\31\1\46\2\uffff"
        )

    DFA8_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1"
        )

    DFA8_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA8_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\7\uffff\1\3\2\2\1\uffff\1\3\1\uffff\4\3\4\uffff"
        u"\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA8 = DFA


    DFA11_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA11_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA11_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA11_max = DFA.unpack(
        u"\1\31\1\46\2\uffff"
        )

    DFA11_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA11_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA11_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\7\uffff\3\2\1\3\1\2\1\uffff\4\2\4\uffff\1\2"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA11 = DFA


    DFA10_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA10_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA10_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA10_max = DFA.unpack(
        u"\1\31\1\46\2\uffff"
        )

    DFA10_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1"
        )

    DFA10_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA10_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\1\7\uffff\3\2\1\3\1\2\1\uffff\4\2\4\uffff\1\2"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA10 = DFA


    DFA14_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA14_eof = DFA.unpack(
        u"\2\2\2\uffff"
        )

    DFA14_min = DFA.unpack(
        u"\2\20\2\uffff"
        )

    DFA14_max = DFA.unpack(
        u"\1\31\1\46\2\uffff"
        )

    DFA14_accept = DFA.unpack(
        u"\2\uffff\1\1\1\2"
        )

    DFA14_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA14_transition = [
        DFA.unpack(u"\1\1\7\3\1\uffff\1\2"),
        DFA.unpack(u"\1\1\7\3\5\2\1\uffff\4\2\4\uffff\1\2"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA14 = DFA


    FOLLOW_WS_in_query122 = frozenset([16])
    FOLLOW_EOF_in_query125 = frozenset([1])
    FOLLOW_WS_in_query154 = frozenset([16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_expression_in_query157 = frozenset([16])
    FOLLOW_WS_in_query159 = frozenset([16])
    FOLLOW_EOF_in_query162 = frozenset([1])
    FOLLOW_sequence_in_expression185 = frozenset([1, 16])
    FOLLOW_andOp_in_expression222 = frozenset([24, 28, 30, 31, 32, 33, 38])
    FOLLOW_sequence_in_expression224 = frozenset([1, 16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_factor_in_sequence262 = frozenset([1, 16])
    FOLLOW_WS_in_sequence298 = frozenset([16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_factor_in_sequence301 = frozenset([1, 16])
    FOLLOW_term_in_factor342 = frozenset([1, 16])
    FOLLOW_orOp_in_factor374 = frozenset([24, 28, 30, 31, 32, 33, 38])
    FOLLOW_term_in_factor376 = frozenset([1, 16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_primitive_in_term410 = frozenset([1])
    FOLLOW_notOp_in_term416 = frozenset([24, 30, 31, 32, 33])
    FOLLOW_primitive_in_term418 = frozenset([1])
    FOLLOW_restriction_in_primitive444 = frozenset([1])
    FOLLOW_composite_in_primitive450 = frozenset([1])
    FOLLOW_comparable_in_restriction467 = frozenset([1, 16, 17, 18, 19, 20, 21, 22, 23])
    FOLLOW_comparator_in_restriction502 = frozenset([24, 30, 31, 32, 33])
    FOLLOW_arg_in_restriction504 = frozenset([1])
    FOLLOW_WS_in_comparator534 = frozenset([16, 17, 18, 19, 20, 21, 22, 23])
    FOLLOW_LE_in_comparator540 = frozenset([1, 16])
    FOLLOW_LESSTHAN_in_comparator546 = frozenset([1, 16])
    FOLLOW_GE_in_comparator552 = frozenset([1, 16])
    FOLLOW_GT_in_comparator558 = frozenset([1, 16])
    FOLLOW_NE_in_comparator564 = frozenset([1, 16])
    FOLLOW_EQ_in_comparator570 = frozenset([1, 16])
    FOLLOW_HAS_in_comparator576 = frozenset([1, 16])
    FOLLOW_WS_in_comparator579 = frozenset([1, 16])
    FOLLOW_member_in_comparable601 = frozenset([1])
    FOLLOW_function_in_comparable607 = frozenset([1])
    FOLLOW_item_in_member622 = frozenset([1])
    FOLLOW_text_in_function639 = frozenset([24])
    FOLLOW_LPAREN_in_function641 = frozenset([24, 25, 30, 31, 32, 33])
    FOLLOW_arglist_in_function643 = frozenset([25])
    FOLLOW_RPAREN_in_function645 = frozenset([1])
    FOLLOW_arg_in_arglist680 = frozenset([1, 16, 29])
    FOLLOW_sep_in_arglist683 = frozenset([24, 30, 31, 32, 33])
    FOLLOW_arg_in_arglist685 = frozenset([1, 16, 29])
    FOLLOW_comparable_in_arg706 = frozenset([1])
    FOLLOW_composite_in_arg712 = frozenset([1])
    FOLLOW_WS_in_andOp726 = frozenset([16, 26])
    FOLLOW_AND_in_andOp729 = frozenset([16])
    FOLLOW_WS_in_andOp731 = frozenset([1, 16])
    FOLLOW_WS_in_orOp746 = frozenset([16, 27])
    FOLLOW_OR_in_orOp749 = frozenset([16])
    FOLLOW_WS_in_orOp751 = frozenset([1, 16])
    FOLLOW_MINUS_in_notOp766 = frozenset([1])
    FOLLOW_NOT_in_notOp772 = frozenset([16])
    FOLLOW_WS_in_notOp774 = frozenset([1, 16])
    FOLLOW_WS_in_sep789 = frozenset([16, 29])
    FOLLOW_COMMA_in_sep792 = frozenset([1, 16])
    FOLLOW_WS_in_sep794 = frozenset([1, 16])
    FOLLOW_LPAREN_in_composite810 = frozenset([16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_WS_in_composite812 = frozenset([16, 24, 28, 30, 31, 32, 33, 38])
    FOLLOW_expression_in_composite815 = frozenset([16, 25])
    FOLLOW_WS_in_composite817 = frozenset([16, 25])
    FOLLOW_RPAREN_in_composite820 = frozenset([1])
    FOLLOW_FIX_in_item840 = frozenset([30, 31, 32, 33])
    FOLLOW_value_in_item842 = frozenset([1])
    FOLLOW_REWRITE_in_item856 = frozenset([30, 31, 32, 33])
    FOLLOW_value_in_item858 = frozenset([1])
    FOLLOW_value_in_item872 = frozenset([1])
    FOLLOW_text_in_value890 = frozenset([1])
    FOLLOW_phrase_in_value906 = frozenset([1])
    FOLLOW_TEXT_in_text930 = frozenset([1])
    FOLLOW_QUOTE_in_phrase944 = frozenset([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46])
    FOLLOW_set_in_phrase946 = frozenset([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46])
    FOLLOW_QUOTE_in_phrase950 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from google.appengine._internal.antlr3.main import ParserMain
    main = ParserMain("QueryLexer", QueryParser)
    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)


if __name__ == '__main__':
    main(sys.argv)
