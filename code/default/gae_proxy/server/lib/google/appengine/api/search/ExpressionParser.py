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


UNDERSCORE=53
GEOPOINT=33
UNICODE_ESC=56
LT=11
TEXT=27
HTML=28
MINUS=18
RSQUARE=25
SNIPPET=44
PHRASE=35
T__58=58
INDEX=5
OCTAL_ESC=57
NUMBER=31
DISTANCE=39
LOG=40
LPAREN=21
RPAREN=22
EQ=15
NAME=26
GEO=32
DATE=30
NOT=10
MIN=42
ASCII_LETTER=52
AND=7
NE=16
POW=43
XOR=9
COUNT=38
SWITCH=45
DOLLAR=54
COND=6
PLUS=17
QUOTE=47
FLOAT=34
MAX=41
INT=24
ATOM=29
NAME_START=50
ABS=37
HEX_DIGIT=55
ESC_SEQ=48
WS=51
EOF=-1
GE=14
COMMA=36
OR=8
TIMES=19
GT=13
DIGIT=46
DIV=20
NEG=4
LSQUARE=23
LE=12
EXPONENT=49


tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "NEG", "INDEX", "COND", "AND", "OR", "XOR", "NOT", "LT", "LE", "GT",
    "GE", "EQ", "NE", "PLUS", "MINUS", "TIMES", "DIV", "LPAREN", "RPAREN",
    "LSQUARE", "INT", "RSQUARE", "NAME", "TEXT", "HTML", "ATOM", "DATE",
    "NUMBER", "GEO", "GEOPOINT", "FLOAT", "PHRASE", "COMMA", "ABS", "COUNT",
    "DISTANCE", "LOG", "MAX", "MIN", "POW", "SNIPPET", "SWITCH", "DIGIT",
    "QUOTE", "ESC_SEQ", "EXPONENT", "NAME_START", "WS", "ASCII_LETTER",
    "UNDERSCORE", "DOLLAR", "HEX_DIGIT", "UNICODE_ESC", "OCTAL_ESC", "'.'"
]




class ExpressionParser(Parser):
    grammarFileName = ""
    antlr_version = version_str_to_tuple("3.1.1")
    antlr_version_str = "3.1.1"
    tokenNames = tokenNames

    def __init__(self, input, state=None):
        if state is None:
            state = RecognizerSharedState()

        Parser.__init__(self, input, state)


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







        self._adaptor = CommonTreeAdaptor()



    def getTreeAdaptor(self):
        return self._adaptor

    def setTreeAdaptor(self, adaptor):
        self._adaptor = adaptor

    adaptor = property(getTreeAdaptor, setTreeAdaptor)



    def mismatch(input, ttype, follow):
      raise MismatchedTokenException(ttype, input)

    def recoverFromMismatchedSet(input, e, follow):
      raise e



    class expression_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def expression(self, ):

        retval = self.expression_return()
        retval.start = self.input.LT(1)

        root_0 = None

        EOF2 = None
        conjunction1 = None


        EOF2_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_conjunction_in_expression90)
                conjunction1 = self.conjunction()

                self._state.following.pop()
                self._adaptor.addChild(root_0, conjunction1.tree)
                EOF2=self.match(self.input, EOF, self.FOLLOW_EOF_in_expression92)

                EOF2_tree = self._adaptor.createWithPayload(EOF2)
                self._adaptor.addChild(root_0, EOF2_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class condExpr_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def condExpr(self, ):

        retval = self.condExpr_return()
        retval.start = self.input.LT(1)

        root_0 = None

        COND4 = None
        conjunction3 = None

        addExpr5 = None


        COND4_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_conjunction_in_condExpr105)
                conjunction3 = self.conjunction()

                self._state.following.pop()
                self._adaptor.addChild(root_0, conjunction3.tree)

                alt1 = 2
                LA1_0 = self.input.LA(1)

                if (LA1_0 == COND) :
                    alt1 = 1
                if alt1 == 1:

                    pass
                    COND4=self.match(self.input, COND, self.FOLLOW_COND_in_condExpr108)

                    COND4_tree = self._adaptor.createWithPayload(COND4)
                    root_0 = self._adaptor.becomeRoot(COND4_tree, root_0)

                    self._state.following.append(self.FOLLOW_addExpr_in_condExpr111)
                    addExpr5 = self.addExpr()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, addExpr5.tree)






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class conjunction_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def conjunction(self, ):

        retval = self.conjunction_return()
        retval.start = self.input.LT(1)

        root_0 = None

        AND7 = None
        disjunction6 = None

        disjunction8 = None


        AND7_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_disjunction_in_conjunction126)
                disjunction6 = self.disjunction()

                self._state.following.pop()
                self._adaptor.addChild(root_0, disjunction6.tree)

                while True:
                    alt2 = 2
                    LA2_0 = self.input.LA(1)

                    if (LA2_0 == AND) :
                        alt2 = 1


                    if alt2 == 1:

                        pass
                        AND7=self.match(self.input, AND, self.FOLLOW_AND_in_conjunction129)

                        AND7_tree = self._adaptor.createWithPayload(AND7)
                        root_0 = self._adaptor.becomeRoot(AND7_tree, root_0)

                        self._state.following.append(self.FOLLOW_disjunction_in_conjunction132)
                        disjunction8 = self.disjunction()

                        self._state.following.pop()
                        self._adaptor.addChild(root_0, disjunction8.tree)


                    else:
                        break





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class disjunction_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def disjunction(self, ):

        retval = self.disjunction_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set10 = None
        negation9 = None

        negation11 = None


        set10_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_negation_in_disjunction147)
                negation9 = self.negation()

                self._state.following.pop()
                self._adaptor.addChild(root_0, negation9.tree)

                while True:
                    alt3 = 2
                    LA3_0 = self.input.LA(1)

                    if ((OR <= LA3_0 <= XOR)) :
                        alt3 = 1


                    if alt3 == 1:

                        pass
                        set10 = self.input.LT(1)
                        set10 = self.input.LT(1)
                        if (OR <= self.input.LA(1) <= XOR):
                            self.input.consume()
                            root_0 = self._adaptor.becomeRoot(self._adaptor.createWithPayload(set10), root_0)
                            self._state.errorRecovery = False

                        else:
                            mse = MismatchedSetException(None, self.input)
                            raise mse


                        self._state.following.append(self.FOLLOW_negation_in_disjunction159)
                        negation11 = self.negation()

                        self._state.following.pop()
                        self._adaptor.addChild(root_0, negation11.tree)


                    else:
                        break





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class negation_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def negation(self, ):

        retval = self.negation_return()
        retval.start = self.input.LT(1)

        root_0 = None

        NOT13 = None
        cmpExpr12 = None

        cmpExpr14 = None


        NOT13_tree = None

        try:
            try:

                alt4 = 2
                LA4_0 = self.input.LA(1)

                if (LA4_0 == MINUS or LA4_0 == LPAREN or LA4_0 == INT or (NAME <= LA4_0 <= PHRASE) or (ABS <= LA4_0 <= SWITCH)) :
                    alt4 = 1
                elif (LA4_0 == NOT) :
                    alt4 = 2
                else:
                    nvae = NoViableAltException("", 4, 0, self.input)

                    raise nvae

                if alt4 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_cmpExpr_in_negation174)
                    cmpExpr12 = self.cmpExpr()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, cmpExpr12.tree)


                elif alt4 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    NOT13=self.match(self.input, NOT, self.FOLLOW_NOT_in_negation180)

                    NOT13_tree = self._adaptor.createWithPayload(NOT13)
                    root_0 = self._adaptor.becomeRoot(NOT13_tree, root_0)

                    self._state.following.append(self.FOLLOW_cmpExpr_in_negation183)
                    cmpExpr14 = self.cmpExpr()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, cmpExpr14.tree)


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class cmpExpr_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def cmpExpr(self, ):

        retval = self.cmpExpr_return()
        retval.start = self.input.LT(1)

        root_0 = None

        addExpr15 = None

        cmpOp16 = None

        addExpr17 = None



        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_addExpr_in_cmpExpr196)
                addExpr15 = self.addExpr()

                self._state.following.pop()
                self._adaptor.addChild(root_0, addExpr15.tree)

                alt5 = 2
                LA5_0 = self.input.LA(1)

                if ((LT <= LA5_0 <= NE)) :
                    alt5 = 1
                if alt5 == 1:

                    pass
                    self._state.following.append(self.FOLLOW_cmpOp_in_cmpExpr199)
                    cmpOp16 = self.cmpOp()

                    self._state.following.pop()
                    root_0 = self._adaptor.becomeRoot(cmpOp16.tree, root_0)
                    self._state.following.append(self.FOLLOW_addExpr_in_cmpExpr202)
                    addExpr17 = self.addExpr()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, addExpr17.tree)






                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class cmpOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def cmpOp(self, ):

        retval = self.cmpOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set18 = None

        set18_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                set18 = self.input.LT(1)
                if (LT <= self.input.LA(1) <= NE):
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set18))
                    self._state.errorRecovery = False

                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class addExpr_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def addExpr(self, ):

        retval = self.addExpr_return()
        retval.start = self.input.LT(1)

        root_0 = None

        multExpr19 = None

        addOp20 = None

        multExpr21 = None



        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_multExpr_in_addExpr260)
                multExpr19 = self.multExpr()

                self._state.following.pop()
                self._adaptor.addChild(root_0, multExpr19.tree)

                while True:
                    alt6 = 2
                    LA6_0 = self.input.LA(1)

                    if ((PLUS <= LA6_0 <= MINUS)) :
                        alt6 = 1


                    if alt6 == 1:

                        pass
                        self._state.following.append(self.FOLLOW_addOp_in_addExpr263)
                        addOp20 = self.addOp()

                        self._state.following.pop()
                        root_0 = self._adaptor.becomeRoot(addOp20.tree, root_0)
                        self._state.following.append(self.FOLLOW_multExpr_in_addExpr266)
                        multExpr21 = self.multExpr()

                        self._state.following.pop()
                        self._adaptor.addChild(root_0, multExpr21.tree)


                    else:
                        break





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class addOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def addOp(self, ):

        retval = self.addOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set22 = None

        set22_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                set22 = self.input.LT(1)
                if (PLUS <= self.input.LA(1) <= MINUS):
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set22))
                    self._state.errorRecovery = False

                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class multExpr_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def multExpr(self, ):

        retval = self.multExpr_return()
        retval.start = self.input.LT(1)

        root_0 = None

        unary23 = None

        multOp24 = None

        unary25 = None



        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                self._state.following.append(self.FOLLOW_unary_in_multExpr300)
                unary23 = self.unary()

                self._state.following.pop()
                self._adaptor.addChild(root_0, unary23.tree)

                while True:
                    alt7 = 2
                    LA7_0 = self.input.LA(1)

                    if ((TIMES <= LA7_0 <= DIV)) :
                        alt7 = 1


                    if alt7 == 1:

                        pass
                        self._state.following.append(self.FOLLOW_multOp_in_multExpr303)
                        multOp24 = self.multOp()

                        self._state.following.pop()
                        root_0 = self._adaptor.becomeRoot(multOp24.tree, root_0)
                        self._state.following.append(self.FOLLOW_unary_in_multExpr306)
                        unary25 = self.unary()

                        self._state.following.pop()
                        self._adaptor.addChild(root_0, unary25.tree)


                    else:
                        break





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class multOp_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def multOp(self, ):

        retval = self.multOp_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set26 = None

        set26_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                set26 = self.input.LT(1)
                if (TIMES <= self.input.LA(1) <= DIV):
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set26))
                    self._state.errorRecovery = False

                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class unary_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def unary(self, ):

        retval = self.unary_return()
        retval.start = self.input.LT(1)

        root_0 = None

        MINUS27 = None
        atom28 = None

        atom29 = None


        MINUS27_tree = None
        stream_MINUS = RewriteRuleTokenStream(self._adaptor, "token MINUS")
        stream_atom = RewriteRuleSubtreeStream(self._adaptor, "rule atom")
        try:
            try:

                alt8 = 2
                LA8_0 = self.input.LA(1)

                if (LA8_0 == MINUS) :
                    alt8 = 1
                elif (LA8_0 == LPAREN or LA8_0 == INT or (NAME <= LA8_0 <= PHRASE) or (ABS <= LA8_0 <= SWITCH)) :
                    alt8 = 2
                else:
                    nvae = NoViableAltException("", 8, 0, self.input)

                    raise nvae

                if alt8 == 1:

                    pass
                    MINUS27=self.match(self.input, MINUS, self.FOLLOW_MINUS_in_unary340)
                    stream_MINUS.add(MINUS27)
                    self._state.following.append(self.FOLLOW_atom_in_unary342)
                    atom28 = self.atom()

                    self._state.following.pop()
                    stream_atom.add(atom28.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.create(NEG, "-"), root_1)

                    self._adaptor.addChild(root_1, stream_atom.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                elif alt8 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_atom_in_unary357)
                    atom29 = self.atom()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, atom29.tree)


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class atom_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def atom(self, ):

        retval = self.atom_return()
        retval.start = self.input.LT(1)

        root_0 = None

        LPAREN34 = None
        RPAREN36 = None
        var30 = None

        num31 = None

        str32 = None

        fn33 = None

        conjunction35 = None


        LPAREN34_tree = None
        RPAREN36_tree = None
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_conjunction = RewriteRuleSubtreeStream(self._adaptor, "rule conjunction")
        try:
            try:

                alt9 = 5
                alt9 = self.dfa9.predict(self.input)
                if alt9 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_var_in_atom370)
                    var30 = self.var()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, var30.tree)


                elif alt9 == 2:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_num_in_atom376)
                    num31 = self.num()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, num31.tree)


                elif alt9 == 3:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_str_in_atom382)
                    str32 = self.str()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, str32.tree)


                elif alt9 == 4:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_fn_in_atom388)
                    fn33 = self.fn()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, fn33.tree)


                elif alt9 == 5:

                    pass
                    LPAREN34=self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_atom394)
                    stream_LPAREN.add(LPAREN34)
                    self._state.following.append(self.FOLLOW_conjunction_in_atom396)
                    conjunction35 = self.conjunction()

                    self._state.following.pop()
                    stream_conjunction.add(conjunction35.tree)
                    RPAREN36=self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_atom398)
                    stream_RPAREN.add(RPAREN36)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, stream_conjunction.nextTree())



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class var_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def var(self, ):

        retval = self.var_return()
        retval.start = self.input.LT(1)

        root_0 = None

        name37 = None

        name38 = None

        index39 = None


        stream_name = RewriteRuleSubtreeStream(self._adaptor, "rule name")
        stream_index = RewriteRuleSubtreeStream(self._adaptor, "rule index")
        try:
            try:

                alt10 = 2
                alt10 = self.dfa10.predict(self.input)
                if alt10 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    self._state.following.append(self.FOLLOW_name_in_var415)
                    name37 = self.name()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, name37.tree)


                elif alt10 == 2:

                    pass
                    self._state.following.append(self.FOLLOW_name_in_var421)
                    name38 = self.name()

                    self._state.following.pop()
                    stream_name.add(name38.tree)
                    self._state.following.append(self.FOLLOW_index_in_var423)
                    index39 = self.index()

                    self._state.following.pop()
                    stream_index.add(index39.tree)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()


                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(self._adaptor.create(INDEX, ((index39 is not None) and [self.input.toString(index39.start,index39.stop)] or [None])[0]), root_1)

                    self._adaptor.addChild(root_1, stream_name.nextTree())

                    self._adaptor.addChild(root_0, root_1)



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class index_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def index(self, ):

        retval = self.index_return()
        retval.start = self.input.LT(1)

        root_0 = None

        x = None
        LSQUARE40 = None
        RSQUARE41 = None

        x_tree = None
        LSQUARE40_tree = None
        RSQUARE41_tree = None
        stream_LSQUARE = RewriteRuleTokenStream(self._adaptor, "token LSQUARE")
        stream_RSQUARE = RewriteRuleTokenStream(self._adaptor, "token RSQUARE")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")

        try:
            try:


                pass
                LSQUARE40=self.match(self.input, LSQUARE, self.FOLLOW_LSQUARE_in_index445)
                stream_LSQUARE.add(LSQUARE40)
                x=self.match(self.input, INT, self.FOLLOW_INT_in_index449)
                stream_INT.add(x)
                RSQUARE41=self.match(self.input, RSQUARE, self.FOLLOW_RSQUARE_in_index451)
                stream_RSQUARE.add(RSQUARE41)








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



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class name_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def name(self, ):

        retval = self.name_return()
        retval.start = self.input.LT(1)

        root_0 = None

        t = None
        NAME42 = None
        char_literal43 = None
        NAME44 = None

        t_tree = None
        NAME42_tree = None
        char_literal43_tree = None
        NAME44_tree = None
        stream_GEO = RewriteRuleTokenStream(self._adaptor, "token GEO")
        stream_DATE = RewriteRuleTokenStream(self._adaptor, "token DATE")
        stream_NUMBER = RewriteRuleTokenStream(self._adaptor, "token NUMBER")
        stream_GEOPOINT = RewriteRuleTokenStream(self._adaptor, "token GEOPOINT")
        stream_TEXT = RewriteRuleTokenStream(self._adaptor, "token TEXT")
        stream_HTML = RewriteRuleTokenStream(self._adaptor, "token HTML")
        stream_ATOM = RewriteRuleTokenStream(self._adaptor, "token ATOM")

        try:
            try:

                alt12 = 8
                LA12 = self.input.LA(1)
                if LA12 == NAME:
                    alt12 = 1
                elif LA12 == TEXT:
                    alt12 = 2
                elif LA12 == HTML:
                    alt12 = 3
                elif LA12 == ATOM:
                    alt12 = 4
                elif LA12 == DATE:
                    alt12 = 5
                elif LA12 == NUMBER:
                    alt12 = 6
                elif LA12 == GEO:
                    alt12 = 7
                elif LA12 == GEOPOINT:
                    alt12 = 8
                else:
                    nvae = NoViableAltException("", 12, 0, self.input)

                    raise nvae

                if alt12 == 1:

                    pass
                    root_0 = self._adaptor.nil()

                    NAME42=self.match(self.input, NAME, self.FOLLOW_NAME_in_name469)

                    NAME42_tree = self._adaptor.createWithPayload(NAME42)
                    self._adaptor.addChild(root_0, NAME42_tree)


                    while True:
                        alt11 = 2
                        LA11_0 = self.input.LA(1)

                        if (LA11_0 == 58) :
                            alt11 = 1


                        if alt11 == 1:

                            pass
                            char_literal43=self.match(self.input, 58, self.FOLLOW_58_in_name472)

                            char_literal43_tree = self._adaptor.createWithPayload(char_literal43)
                            root_0 = self._adaptor.becomeRoot(char_literal43_tree, root_0)

                            NAME44=self.match(self.input, NAME, self.FOLLOW_NAME_in_name475)

                            NAME44_tree = self._adaptor.createWithPayload(NAME44)
                            self._adaptor.addChild(root_0, NAME44_tree)



                        else:
                            break




                elif alt12 == 2:

                    pass
                    t=self.match(self.input, TEXT, self.FOLLOW_TEXT_in_name491)
                    stream_TEXT.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 3:

                    pass
                    t=self.match(self.input, HTML, self.FOLLOW_HTML_in_name504)
                    stream_HTML.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 4:

                    pass
                    t=self.match(self.input, ATOM, self.FOLLOW_ATOM_in_name517)
                    stream_ATOM.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 5:

                    pass
                    t=self.match(self.input, DATE, self.FOLLOW_DATE_in_name530)
                    stream_DATE.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 6:

                    pass
                    t=self.match(self.input, NUMBER, self.FOLLOW_NUMBER_in_name543)
                    stream_NUMBER.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 7:

                    pass
                    t=self.match(self.input, GEO, self.FOLLOW_GEO_in_name556)
                    stream_GEO.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                elif alt12 == 8:

                    pass
                    t=self.match(self.input, GEOPOINT, self.FOLLOW_GEOPOINT_in_name569)
                    stream_GEOPOINT.add(t)








                    retval.tree = root_0

                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()

                    self._adaptor.addChild(root_0, self._adaptor.create(NAME, t))



                    retval.tree = root_0


                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class num_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def num(self, ):

        retval = self.num_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set45 = None

        set45_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                set45 = self.input.LT(1)
                if self.input.LA(1) == INT or self.input.LA(1) == FLOAT:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set45))
                    self._state.errorRecovery = False

                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class str_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def str(self, ):

        retval = self.str_return()
        retval.start = self.input.LT(1)

        root_0 = None

        PHRASE46 = None

        PHRASE46_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                PHRASE46=self.match(self.input, PHRASE, self.FOLLOW_PHRASE_in_str606)

                PHRASE46_tree = self._adaptor.createWithPayload(PHRASE46)
                self._adaptor.addChild(root_0, PHRASE46_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class fn_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def fn(self, ):

        retval = self.fn_return()
        retval.start = self.input.LT(1)

        root_0 = None

        LPAREN48 = None
        COMMA50 = None
        RPAREN52 = None
        fnName47 = None

        condExpr49 = None

        condExpr51 = None


        LPAREN48_tree = None
        COMMA50_tree = None
        RPAREN52_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_fnName = RewriteRuleSubtreeStream(self._adaptor, "rule fnName")
        stream_condExpr = RewriteRuleSubtreeStream(self._adaptor, "rule condExpr")
        try:
            try:


                pass
                self._state.following.append(self.FOLLOW_fnName_in_fn619)
                fnName47 = self.fnName()

                self._state.following.pop()
                stream_fnName.add(fnName47.tree)
                LPAREN48=self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_fn621)
                stream_LPAREN.add(LPAREN48)
                self._state.following.append(self.FOLLOW_condExpr_in_fn623)
                condExpr49 = self.condExpr()

                self._state.following.pop()
                stream_condExpr.add(condExpr49.tree)

                while True:
                    alt13 = 2
                    LA13_0 = self.input.LA(1)

                    if (LA13_0 == COMMA) :
                        alt13 = 1


                    if alt13 == 1:

                        pass
                        COMMA50=self.match(self.input, COMMA, self.FOLLOW_COMMA_in_fn626)
                        stream_COMMA.add(COMMA50)
                        self._state.following.append(self.FOLLOW_condExpr_in_fn628)
                        condExpr51 = self.condExpr()

                        self._state.following.pop()
                        stream_condExpr.add(condExpr51.tree)


                    else:
                        break


                RPAREN52=self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_fn632)
                stream_RPAREN.add(RPAREN52)








                retval.tree = root_0

                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()


                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(stream_fnName.nextNode(), root_1)


                if not (stream_condExpr.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_condExpr.hasNext():
                    self._adaptor.addChild(root_1, stream_condExpr.nextTree())


                stream_condExpr.reset()

                self._adaptor.addChild(root_0, root_1)



                retval.tree = root_0



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval



    class fnName_return(ParserRuleReturnScope):
        def __init__(self):
            ParserRuleReturnScope.__init__(self)

            self.tree = None






    def fnName(self, ):

        retval = self.fnName_return()
        retval.start = self.input.LT(1)

        root_0 = None

        set53 = None

        set53_tree = None

        try:
            try:


                pass
                root_0 = self._adaptor.nil()

                set53 = self.input.LT(1)
                if (TEXT <= self.input.LA(1) <= GEOPOINT) or (ABS <= self.input.LA(1) <= SWITCH):
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set53))
                    self._state.errorRecovery = False

                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, e:
              self.reportError(e)
              raise e
        finally:

            pass

        return retval









    DFA9_eot = DFA.unpack(
        u"\15\uffff"
        )

    DFA9_eof = DFA.unpack(
        u"\2\uffff\7\1\4\uffff"
        )

    DFA9_min = DFA.unpack(
        u"\1\25\1\uffff\7\6\4\uffff"
        )

    DFA9_max = DFA.unpack(
        u"\1\55\1\uffff\7\44\4\uffff"
        )

    DFA9_accept = DFA.unpack(
        u"\1\uffff\1\1\7\uffff\1\2\1\3\1\4\1\5"
        )

    DFA9_special = DFA.unpack(
        u"\15\uffff"
        )


    DFA9_transition = [
        DFA.unpack(u"\1\14\2\uffff\1\11\1\uffff\1\1\1\2\1\3\1\4\1\5\1\6\1"
        u"\7\1\10\1\11\1\12\1\uffff\11\13"),
        DFA.unpack(u""),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u"\4\1\1\uffff\12\1\1\13\2\1\14\uffff\1\1"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA9 = DFA


    DFA10_eot = DFA.unpack(
        u"\15\uffff"
        )

    DFA10_eof = DFA.unpack(
        u"\1\uffff\10\13\3\uffff\1\13"
        )

    DFA10_min = DFA.unpack(
        u"\1\32\10\6\1\32\2\uffff\1\6"
        )

    DFA10_max = DFA.unpack(
        u"\1\41\1\72\7\44\1\32\2\uffff\1\72"
        )

    DFA10_accept = DFA.unpack(
        u"\12\uffff\1\2\1\1\1\uffff"
        )

    DFA10_special = DFA.unpack(
        u"\15\uffff"
        )


    DFA10_transition = [
        DFA.unpack(u"\1\1\1\2\1\3\1\4\1\5\1\6\1\7\1\10"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"
        u"\25\uffff\1\11"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"),
        DFA.unpack(u"\1\14"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\4\13\1\uffff\12\13\1\uffff\1\13\1\12\14\uffff\1\13"
        u"\25\uffff\1\11")
    ]



    DFA10 = DFA


    FOLLOW_conjunction_in_expression90 = frozenset([])
    FOLLOW_EOF_in_expression92 = frozenset([1])
    FOLLOW_conjunction_in_condExpr105 = frozenset([1, 6])
    FOLLOW_COND_in_condExpr108 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_addExpr_in_condExpr111 = frozenset([1])
    FOLLOW_disjunction_in_conjunction126 = frozenset([1, 7])
    FOLLOW_AND_in_conjunction129 = frozenset([10, 18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_disjunction_in_conjunction132 = frozenset([1, 7])
    FOLLOW_negation_in_disjunction147 = frozenset([1, 8, 9])
    FOLLOW_set_in_disjunction150 = frozenset([10, 18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_negation_in_disjunction159 = frozenset([1, 8, 9])
    FOLLOW_cmpExpr_in_negation174 = frozenset([1])
    FOLLOW_NOT_in_negation180 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_cmpExpr_in_negation183 = frozenset([1])
    FOLLOW_addExpr_in_cmpExpr196 = frozenset([1, 11, 12, 13, 14, 15, 16])
    FOLLOW_cmpOp_in_cmpExpr199 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_addExpr_in_cmpExpr202 = frozenset([1])
    FOLLOW_set_in_cmpOp0 = frozenset([1])
    FOLLOW_multExpr_in_addExpr260 = frozenset([1, 17, 18])
    FOLLOW_addOp_in_addExpr263 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_multExpr_in_addExpr266 = frozenset([1, 17, 18])
    FOLLOW_set_in_addOp0 = frozenset([1])
    FOLLOW_unary_in_multExpr300 = frozenset([1, 19, 20])
    FOLLOW_multOp_in_multExpr303 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_unary_in_multExpr306 = frozenset([1, 19, 20])
    FOLLOW_set_in_multOp0 = frozenset([1])
    FOLLOW_MINUS_in_unary340 = frozenset([18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_atom_in_unary342 = frozenset([1])
    FOLLOW_atom_in_unary357 = frozenset([1])
    FOLLOW_var_in_atom370 = frozenset([1])
    FOLLOW_num_in_atom376 = frozenset([1])
    FOLLOW_str_in_atom382 = frozenset([1])
    FOLLOW_fn_in_atom388 = frozenset([1])
    FOLLOW_LPAREN_in_atom394 = frozenset([10, 18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_conjunction_in_atom396 = frozenset([22])
    FOLLOW_RPAREN_in_atom398 = frozenset([1])
    FOLLOW_name_in_var415 = frozenset([1])
    FOLLOW_name_in_var421 = frozenset([23])
    FOLLOW_index_in_var423 = frozenset([1])
    FOLLOW_LSQUARE_in_index445 = frozenset([24])
    FOLLOW_INT_in_index449 = frozenset([25])
    FOLLOW_RSQUARE_in_index451 = frozenset([1])
    FOLLOW_NAME_in_name469 = frozenset([1, 58])
    FOLLOW_58_in_name472 = frozenset([26])
    FOLLOW_NAME_in_name475 = frozenset([1, 58])
    FOLLOW_TEXT_in_name491 = frozenset([1])
    FOLLOW_HTML_in_name504 = frozenset([1])
    FOLLOW_ATOM_in_name517 = frozenset([1])
    FOLLOW_DATE_in_name530 = frozenset([1])
    FOLLOW_NUMBER_in_name543 = frozenset([1])
    FOLLOW_GEO_in_name556 = frozenset([1])
    FOLLOW_GEOPOINT_in_name569 = frozenset([1])
    FOLLOW_set_in_num0 = frozenset([1])
    FOLLOW_PHRASE_in_str606 = frozenset([1])
    FOLLOW_fnName_in_fn619 = frozenset([21])
    FOLLOW_LPAREN_in_fn621 = frozenset([10, 18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_condExpr_in_fn623 = frozenset([22, 36])
    FOLLOW_COMMA_in_fn626 = frozenset([10, 18, 21, 24, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 37, 38, 39, 40, 41, 42, 43, 44, 45])
    FOLLOW_condExpr_in_fn628 = frozenset([22, 36])
    FOLLOW_RPAREN_in_fn632 = frozenset([1])
    FOLLOW_set_in_fnName0 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from google.appengine._internal.antlr3.main import ParserMain
    main = ParserMain("ExpressionLexer", ExpressionParser)
    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)


if __name__ == '__main__':
    main(sys.argv)
