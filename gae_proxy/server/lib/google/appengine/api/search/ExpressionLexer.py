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


class ExpressionLexer(Lexer):

    grammarFileName = ""
    antlr_version = version_str_to_tuple("3.1.1")
    antlr_version_str = "3.1.1"

    def __init__(self, input=None, state=None):
        if state is None:
            state = RecognizerSharedState()
        Lexer.__init__(self, input, state)

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

        self.dfa16 = self.DFA16(
            self, 16,
            eot = self.DFA16_eot,
            eof = self.DFA16_eof,
            min = self.DFA16_min,
            max = self.DFA16_max,
            accept = self.DFA16_accept,
            special = self.DFA16_special,
            transition = self.DFA16_transition
            )







    def mT__58(self, ):

        try:
            _type = T__58
            _channel = DEFAULT_CHANNEL



            pass
            self.match(46)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mABS(self, ):

        try:
            _type = ABS
            _channel = DEFAULT_CHANNEL



            pass
            self.match("abs")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mCOUNT(self, ):

        try:
            _type = COUNT
            _channel = DEFAULT_CHANNEL



            pass
            self.match("count")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mDISTANCE(self, ):

        try:
            _type = DISTANCE
            _channel = DEFAULT_CHANNEL



            pass
            self.match("distance")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mGEOPOINT(self, ):

        try:
            _type = GEOPOINT
            _channel = DEFAULT_CHANNEL



            pass
            self.match("geopoint")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mLOG(self, ):

        try:
            _type = LOG
            _channel = DEFAULT_CHANNEL



            pass
            self.match("log")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mMAX(self, ):

        try:
            _type = MAX
            _channel = DEFAULT_CHANNEL



            pass
            self.match("max")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mMIN(self, ):

        try:
            _type = MIN
            _channel = DEFAULT_CHANNEL



            pass
            self.match("min")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mPOW(self, ):

        try:
            _type = POW
            _channel = DEFAULT_CHANNEL



            pass
            self.match("pow")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mAND(self, ):

        try:
            _type = AND
            _channel = DEFAULT_CHANNEL



            pass
            self.match("AND")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mOR(self, ):

        try:
            _type = OR
            _channel = DEFAULT_CHANNEL



            pass
            self.match("OR")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mXOR(self, ):

        try:
            _type = XOR
            _channel = DEFAULT_CHANNEL



            pass
            self.match("XOR")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mNOT(self, ):

        try:
            _type = NOT
            _channel = DEFAULT_CHANNEL



            pass
            self.match("NOT")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mSNIPPET(self, ):

        try:
            _type = SNIPPET
            _channel = DEFAULT_CHANNEL



            pass
            self.match("snippet")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mSWITCH(self, ):

        try:
            _type = SWITCH
            _channel = DEFAULT_CHANNEL



            pass
            self.match("switch")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mTEXT(self, ):

        try:
            _type = TEXT
            _channel = DEFAULT_CHANNEL



            pass
            self.match("text")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mHTML(self, ):

        try:
            _type = HTML
            _channel = DEFAULT_CHANNEL



            pass
            self.match("html")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mATOM(self, ):

        try:
            _type = ATOM
            _channel = DEFAULT_CHANNEL



            pass
            self.match("atom")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mDATE(self, ):

        try:
            _type = DATE
            _channel = DEFAULT_CHANNEL



            pass
            self.match("date")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mNUMBER(self, ):

        try:
            _type = NUMBER
            _channel = DEFAULT_CHANNEL



            pass
            self.match("number")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mGEO(self, ):

        try:
            _type = GEO
            _channel = DEFAULT_CHANNEL



            pass
            self.match("geo")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mINT(self, ):

        try:
            _type = INT
            _channel = DEFAULT_CHANNEL



            pass

            cnt1 = 0
            while True:
                alt1 = 2
                LA1_0 = self.input.LA(1)

                if ((48 <= LA1_0 <= 57)) :
                    alt1 = 1


                if alt1 == 1:

                    pass
                    self.mDIGIT()


                else:
                    if cnt1 >= 1:
                        break

                    eee = EarlyExitException(1, self.input)
                    raise eee

                cnt1 += 1





            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mPHRASE(self, ):

        try:
            _type = PHRASE
            _channel = DEFAULT_CHANNEL



            pass
            self.mQUOTE()

            while True:
                alt2 = 3
                LA2_0 = self.input.LA(1)

                if (LA2_0 == 92) :
                    alt2 = 1
                elif ((0 <= LA2_0 <= 33) or (35 <= LA2_0 <= 91) or (93 <= LA2_0 <= 65535)) :
                    alt2 = 2


                if alt2 == 1:

                    pass
                    self.mESC_SEQ()


                elif alt2 == 2:

                    pass
                    if (0 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse



                else:
                    break


            self.mQUOTE()



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mFLOAT(self, ):

        try:
            _type = FLOAT
            _channel = DEFAULT_CHANNEL


            alt9 = 3
            alt9 = self.dfa9.predict(self.input)
            if alt9 == 1:

                pass

                cnt3 = 0
                while True:
                    alt3 = 2
                    LA3_0 = self.input.LA(1)

                    if ((48 <= LA3_0 <= 57)) :
                        alt3 = 1


                    if alt3 == 1:

                        pass
                        self.mDIGIT()


                    else:
                        if cnt3 >= 1:
                            break

                        eee = EarlyExitException(3, self.input)
                        raise eee

                    cnt3 += 1


                self.match(46)

                while True:
                    alt4 = 2
                    LA4_0 = self.input.LA(1)

                    if ((48 <= LA4_0 <= 57)) :
                        alt4 = 1


                    if alt4 == 1:

                        pass
                        self.mDIGIT()


                    else:
                        break



                alt5 = 2
                LA5_0 = self.input.LA(1)

                if (LA5_0 == 69 or LA5_0 == 101) :
                    alt5 = 1
                if alt5 == 1:

                    pass
                    self.mEXPONENT()





            elif alt9 == 2:

                pass
                self.match(46)

                cnt6 = 0
                while True:
                    alt6 = 2
                    LA6_0 = self.input.LA(1)

                    if ((48 <= LA6_0 <= 57)) :
                        alt6 = 1


                    if alt6 == 1:

                        pass
                        self.mDIGIT()


                    else:
                        if cnt6 >= 1:
                            break

                        eee = EarlyExitException(6, self.input)
                        raise eee

                    cnt6 += 1



                alt7 = 2
                LA7_0 = self.input.LA(1)

                if (LA7_0 == 69 or LA7_0 == 101) :
                    alt7 = 1
                if alt7 == 1:

                    pass
                    self.mEXPONENT()





            elif alt9 == 3:

                pass

                cnt8 = 0
                while True:
                    alt8 = 2
                    LA8_0 = self.input.LA(1)

                    if ((48 <= LA8_0 <= 57)) :
                        alt8 = 1


                    if alt8 == 1:

                        pass
                        self.mDIGIT()


                    else:
                        if cnt8 >= 1:
                            break

                        eee = EarlyExitException(8, self.input)
                        raise eee

                    cnt8 += 1


                self.mEXPONENT()


            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mNAME(self, ):

        try:
            _type = NAME
            _channel = DEFAULT_CHANNEL



            pass
            self.mNAME_START()

            while True:
                alt10 = 2
                LA10_0 = self.input.LA(1)

                if (LA10_0 == 36 or (48 <= LA10_0 <= 57) or (65 <= LA10_0 <= 90) or LA10_0 == 95 or (97 <= LA10_0 <= 122)) :
                    alt10 = 1


                if alt10 == 1:

                    pass
                    if self.input.LA(1) == 36 or (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 90) or self.input.LA(1) == 95 or (97 <= self.input.LA(1) <= 122):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse



                else:
                    break





            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mLPAREN(self, ):

        try:
            _type = LPAREN
            _channel = DEFAULT_CHANNEL



            pass
            self.match(40)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mRPAREN(self, ):

        try:
            _type = RPAREN
            _channel = DEFAULT_CHANNEL



            pass
            self.match(41)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mLSQUARE(self, ):

        try:
            _type = LSQUARE
            _channel = DEFAULT_CHANNEL



            pass
            self.match(91)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mRSQUARE(self, ):

        try:
            _type = RSQUARE
            _channel = DEFAULT_CHANNEL



            pass
            self.match(93)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mPLUS(self, ):

        try:
            _type = PLUS
            _channel = DEFAULT_CHANNEL



            pass
            self.match(43)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mMINUS(self, ):

        try:
            _type = MINUS
            _channel = DEFAULT_CHANNEL



            pass
            self.match(45)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mTIMES(self, ):

        try:
            _type = TIMES
            _channel = DEFAULT_CHANNEL



            pass
            self.match(42)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mDIV(self, ):

        try:
            _type = DIV
            _channel = DEFAULT_CHANNEL



            pass
            self.match(47)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mLT(self, ):

        try:
            _type = LT
            _channel = DEFAULT_CHANNEL



            pass
            self.match(60)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mLE(self, ):

        try:
            _type = LE
            _channel = DEFAULT_CHANNEL



            pass
            self.match("<=")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mGT(self, ):

        try:
            _type = GT
            _channel = DEFAULT_CHANNEL



            pass
            self.match(62)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mGE(self, ):

        try:
            _type = GE
            _channel = DEFAULT_CHANNEL



            pass
            self.match(">=")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mEQ(self, ):

        try:
            _type = EQ
            _channel = DEFAULT_CHANNEL



            pass
            self.match(61)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mNE(self, ):

        try:
            _type = NE
            _channel = DEFAULT_CHANNEL



            pass
            self.match("!=")



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mCOND(self, ):

        try:
            _type = COND
            _channel = DEFAULT_CHANNEL



            pass
            self.match(63)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mQUOTE(self, ):

        try:
            _type = QUOTE
            _channel = DEFAULT_CHANNEL



            pass
            self.match(34)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mCOMMA(self, ):

        try:
            _type = COMMA
            _channel = DEFAULT_CHANNEL



            pass
            self.match(44)



            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mWS(self, ):

        try:
            _type = WS
            _channel = DEFAULT_CHANNEL



            pass

            cnt11 = 0
            while True:
                alt11 = 2
                LA11_0 = self.input.LA(1)

                if ((9 <= LA11_0 <= 10) or LA11_0 == 13 or LA11_0 == 32) :
                    alt11 = 1


                if alt11 == 1:

                    pass
                    if (9 <= self.input.LA(1) <= 10) or self.input.LA(1) == 13 or self.input.LA(1) == 32:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse



                else:
                    if cnt11 >= 1:
                        break

                    eee = EarlyExitException(11, self.input)
                    raise eee

                cnt11 += 1



            _channel = HIDDEN;




            self._state.type = _type
            self._state.channel = _channel

        finally:

            pass






    def mEXPONENT(self, ):

        try:


            pass
            if self.input.LA(1) == 69 or self.input.LA(1) == 101:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse


            alt12 = 2
            LA12_0 = self.input.LA(1)

            if (LA12_0 == 43 or LA12_0 == 45) :
                alt12 = 1
            if alt12 == 1:

                pass
                if self.input.LA(1) == 43 or self.input.LA(1) == 45:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse





            cnt13 = 0
            while True:
                alt13 = 2
                LA13_0 = self.input.LA(1)

                if ((48 <= LA13_0 <= 57)) :
                    alt13 = 1


                if alt13 == 1:

                    pass
                    self.mDIGIT()


                else:
                    if cnt13 >= 1:
                        break

                    eee = EarlyExitException(13, self.input)
                    raise eee

                cnt13 += 1






        finally:

            pass






    def mNAME_START(self, ):

        try:


            pass
            if self.input.LA(1) == 36 or (65 <= self.input.LA(1) <= 90) or self.input.LA(1) == 95 or (97 <= self.input.LA(1) <= 122):
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse





        finally:

            pass






    def mASCII_LETTER(self, ):

        try:


            pass
            if (65 <= self.input.LA(1) <= 90) or (97 <= self.input.LA(1) <= 122):
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse





        finally:

            pass






    def mDIGIT(self, ):

        try:


            pass
            self.matchRange(48, 57)




        finally:

            pass






    def mDOLLAR(self, ):

        try:


            pass
            self.match(36)




        finally:

            pass






    def mUNDERSCORE(self, ):

        try:


            pass
            self.match(95)




        finally:

            pass






    def mHEX_DIGIT(self, ):

        try:


            pass
            if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 70) or (97 <= self.input.LA(1) <= 102):
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse





        finally:

            pass






    def mESC_SEQ(self, ):

        try:

            alt14 = 3
            LA14_0 = self.input.LA(1)

            if (LA14_0 == 92) :
                LA14 = self.input.LA(2)
                if LA14 == 34 or LA14 == 39 or LA14 == 92 or LA14 == 98 or LA14 == 102 or LA14 == 110 or LA14 == 114 or LA14 == 116:
                    alt14 = 1
                elif LA14 == 117:
                    alt14 = 2
                elif LA14 == 48 or LA14 == 49 or LA14 == 50 or LA14 == 51 or LA14 == 52 or LA14 == 53 or LA14 == 54 or LA14 == 55:
                    alt14 = 3
                else:
                    nvae = NoViableAltException("", 14, 1, self.input)

                    raise nvae

            else:
                nvae = NoViableAltException("", 14, 0, self.input)

                raise nvae

            if alt14 == 1:

                pass
                self.match(92)
                if self.input.LA(1) == 34 or self.input.LA(1) == 39 or self.input.LA(1) == 92 or self.input.LA(1) == 98 or self.input.LA(1) == 102 or self.input.LA(1) == 110 or self.input.LA(1) == 114 or self.input.LA(1) == 116:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



            elif alt14 == 2:

                pass
                self.mUNICODE_ESC()


            elif alt14 == 3:

                pass
                self.mOCTAL_ESC()



        finally:

            pass






    def mOCTAL_ESC(self, ):

        try:

            alt15 = 3
            LA15_0 = self.input.LA(1)

            if (LA15_0 == 92) :
                LA15_1 = self.input.LA(2)

                if ((48 <= LA15_1 <= 51)) :
                    LA15_2 = self.input.LA(3)

                    if ((48 <= LA15_2 <= 55)) :
                        LA15_4 = self.input.LA(4)

                        if ((48 <= LA15_4 <= 55)) :
                            alt15 = 1
                        else:
                            alt15 = 2
                    else:
                        alt15 = 3
                elif ((52 <= LA15_1 <= 55)) :
                    LA15_3 = self.input.LA(3)

                    if ((48 <= LA15_3 <= 55)) :
                        alt15 = 2
                    else:
                        alt15 = 3
                else:
                    nvae = NoViableAltException("", 15, 1, self.input)

                    raise nvae

            else:
                nvae = NoViableAltException("", 15, 0, self.input)

                raise nvae

            if alt15 == 1:

                pass
                self.match(92)


                pass
                self.matchRange(48, 51)





                pass
                self.matchRange(48, 55)





                pass
                self.matchRange(48, 55)





            elif alt15 == 2:

                pass
                self.match(92)


                pass
                self.matchRange(48, 55)





                pass
                self.matchRange(48, 55)





            elif alt15 == 3:

                pass
                self.match(92)


                pass
                self.matchRange(48, 55)






        finally:

            pass






    def mUNICODE_ESC(self, ):

        try:


            pass
            self.match(92)
            self.match(117)
            self.mHEX_DIGIT()
            self.mHEX_DIGIT()
            self.mHEX_DIGIT()
            self.mHEX_DIGIT()




        finally:

            pass





    def mTokens(self):

        alt16 = 43
        alt16 = self.dfa16.predict(self.input)
        if alt16 == 1:

            pass
            self.mT__58()


        elif alt16 == 2:

            pass
            self.mABS()


        elif alt16 == 3:

            pass
            self.mCOUNT()


        elif alt16 == 4:

            pass
            self.mDISTANCE()


        elif alt16 == 5:

            pass
            self.mGEOPOINT()


        elif alt16 == 6:

            pass
            self.mLOG()


        elif alt16 == 7:

            pass
            self.mMAX()


        elif alt16 == 8:

            pass
            self.mMIN()


        elif alt16 == 9:

            pass
            self.mPOW()


        elif alt16 == 10:

            pass
            self.mAND()


        elif alt16 == 11:

            pass
            self.mOR()


        elif alt16 == 12:

            pass
            self.mXOR()


        elif alt16 == 13:

            pass
            self.mNOT()


        elif alt16 == 14:

            pass
            self.mSNIPPET()


        elif alt16 == 15:

            pass
            self.mSWITCH()


        elif alt16 == 16:

            pass
            self.mTEXT()


        elif alt16 == 17:

            pass
            self.mHTML()


        elif alt16 == 18:

            pass
            self.mATOM()


        elif alt16 == 19:

            pass
            self.mDATE()


        elif alt16 == 20:

            pass
            self.mNUMBER()


        elif alt16 == 21:

            pass
            self.mGEO()


        elif alt16 == 22:

            pass
            self.mINT()


        elif alt16 == 23:

            pass
            self.mPHRASE()


        elif alt16 == 24:

            pass
            self.mFLOAT()


        elif alt16 == 25:

            pass
            self.mNAME()


        elif alt16 == 26:

            pass
            self.mLPAREN()


        elif alt16 == 27:

            pass
            self.mRPAREN()


        elif alt16 == 28:

            pass
            self.mLSQUARE()


        elif alt16 == 29:

            pass
            self.mRSQUARE()


        elif alt16 == 30:

            pass
            self.mPLUS()


        elif alt16 == 31:

            pass
            self.mMINUS()


        elif alt16 == 32:

            pass
            self.mTIMES()


        elif alt16 == 33:

            pass
            self.mDIV()


        elif alt16 == 34:

            pass
            self.mLT()


        elif alt16 == 35:

            pass
            self.mLE()


        elif alt16 == 36:

            pass
            self.mGT()


        elif alt16 == 37:

            pass
            self.mGE()


        elif alt16 == 38:

            pass
            self.mEQ()


        elif alt16 == 39:

            pass
            self.mNE()


        elif alt16 == 40:

            pass
            self.mCOND()


        elif alt16 == 41:

            pass
            self.mQUOTE()


        elif alt16 == 42:

            pass
            self.mCOMMA()


        elif alt16 == 43:

            pass
            self.mWS()









    DFA9_eot = DFA.unpack(
        u"\5\uffff"
        )

    DFA9_eof = DFA.unpack(
        u"\5\uffff"
        )

    DFA9_min = DFA.unpack(
        u"\2\56\3\uffff"
        )

    DFA9_max = DFA.unpack(
        u"\1\71\1\145\3\uffff"
        )

    DFA9_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1\1\3"
        )

    DFA9_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA9_transition = [
        DFA.unpack(u"\1\2\1\uffff\12\1"),
        DFA.unpack(u"\1\3\1\uffff\12\1\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    DFA9 = DFA


    DFA16_eot = DFA.unpack(
        u"\1\uffff\1\44\17\23\1\70\1\71\11\uffff\1\74\1\76\7\uffff\13\23"
        u"\1\112\7\23\7\uffff\1\122\4\23\1\130\1\131\1\132\1\133\1\134\1"
        u"\135\1\uffff\1\136\1\137\5\23\1\uffff\1\145\2\23\1\150\1\23\10"
        u"\uffff\2\23\1\154\1\155\1\23\1\uffff\1\157\1\23\1\uffff\3\23\2"
        u"\uffff\1\23\1\uffff\3\23\1\170\1\171\2\23\1\174\2\uffff\1\175\1"
        u"\176\3\uffff"
        )

    DFA16_eof = DFA.unpack(
        u"\177\uffff"
        )

    DFA16_min = DFA.unpack(
        u"\1\11\1\60\1\142\1\157\1\141\1\145\1\157\1\141\1\157\1\116\1\122"
        u"\2\117\1\156\1\145\1\164\1\165\1\56\1\0\11\uffff\2\75\7\uffff\1"
        u"\163\1\157\1\165\1\163\1\164\1\157\1\147\1\170\1\156\1\167\1\104"
        u"\1\44\1\122\1\124\2\151\1\170\2\155\7\uffff\1\44\1\155\1\156\1"
        u"\164\1\145\6\44\1\uffff\2\44\1\160\2\164\1\154\1\142\1\uffff\1"
        u"\44\1\164\1\141\1\44\1\157\10\uffff\1\160\1\143\2\44\1\145\1\uffff"
        u"\1\44\1\156\1\uffff\1\151\1\145\1\150\2\uffff\1\162\1\uffff\1\143"
        u"\1\156\1\164\2\44\1\145\1\164\1\44\2\uffff\2\44\3\uffff"
        )

    DFA16_max = DFA.unpack(
        u"\1\172\1\71\1\164\1\157\1\151\1\145\1\157\1\151\1\157\1\116\1\122"
        u"\2\117\1\167\1\145\1\164\1\165\1\145\1\uffff\11\uffff\2\75\7\uffff"
        u"\1\163\1\157\1\165\1\163\1\164\1\157\1\147\1\170\1\156\1\167\1"
        u"\104\1\172\1\122\1\124\2\151\1\170\2\155\7\uffff\1\172\1\155\1"
        u"\156\1\164\1\145\6\172\1\uffff\2\172\1\160\2\164\1\154\1\142\1"
        u"\uffff\1\172\1\164\1\141\1\172\1\157\10\uffff\1\160\1\143\2\172"
        u"\1\145\1\uffff\1\172\1\156\1\uffff\1\151\1\145\1\150\2\uffff\1"
        u"\162\1\uffff\1\143\1\156\1\164\2\172\1\145\1\164\1\172\2\uffff"
        u"\2\172\3\uffff"
        )

    DFA16_accept = DFA.unpack(
        u"\23\uffff\1\31\1\32\1\33\1\34\1\35\1\36\1\37\1\40\1\41\2\uffff"
        u"\1\46\1\47\1\50\1\52\1\53\1\30\1\1\23\uffff\1\26\1\51\1\27\1\43"
        u"\1\42\1\45\1\44\13\uffff\1\13\7\uffff\1\2\5\uffff\1\25\1\6\1\7"
        u"\1\10\1\11\1\12\1\14\1\15\5\uffff\1\22\2\uffff\1\23\3\uffff\1\20"
        u"\1\21\1\uffff\1\3\10\uffff\1\17\1\24\2\uffff\1\16\1\4\1\5"
        )

    DFA16_special = DFA.unpack(
        u"\22\uffff\1\0\154\uffff"
        )


    DFA16_transition = [
        DFA.unpack(u"\2\42\2\uffff\1\42\22\uffff\1\42\1\37\1\22\1\uffff\1"
        u"\23\3\uffff\1\24\1\25\1\32\1\30\1\41\1\31\1\1\1\33\12\21\2\uffff"
        u"\1\34\1\36\1\35\1\40\1\uffff\1\11\14\23\1\14\1\12\10\23\1\13\2"
        u"\23\1\26\1\uffff\1\27\1\uffff\1\23\1\uffff\1\2\1\23\1\3\1\4\2\23"
        u"\1\5\1\17\3\23\1\6\1\7\1\20\1\23\1\10\2\23\1\15\1\16\6\23"),
        DFA.unpack(u"\12\43"),
        DFA.unpack(u"\1\45\21\uffff\1\46"),
        DFA.unpack(u"\1\47"),
        DFA.unpack(u"\1\51\7\uffff\1\50"),
        DFA.unpack(u"\1\52"),
        DFA.unpack(u"\1\53"),
        DFA.unpack(u"\1\54\7\uffff\1\55"),
        DFA.unpack(u"\1\56"),
        DFA.unpack(u"\1\57"),
        DFA.unpack(u"\1\60"),
        DFA.unpack(u"\1\61"),
        DFA.unpack(u"\1\62"),
        DFA.unpack(u"\1\63\10\uffff\1\64"),
        DFA.unpack(u"\1\65"),
        DFA.unpack(u"\1\66"),
        DFA.unpack(u"\1\67"),
        DFA.unpack(u"\1\43\1\uffff\12\21\13\uffff\1\43\37\uffff\1\43"),
        DFA.unpack(u"\0\72"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\73"),
        DFA.unpack(u"\1\75"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\77"),
        DFA.unpack(u"\1\100"),
        DFA.unpack(u"\1\101"),
        DFA.unpack(u"\1\102"),
        DFA.unpack(u"\1\103"),
        DFA.unpack(u"\1\104"),
        DFA.unpack(u"\1\105"),
        DFA.unpack(u"\1\106"),
        DFA.unpack(u"\1\107"),
        DFA.unpack(u"\1\110"),
        DFA.unpack(u"\1\111"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\113"),
        DFA.unpack(u"\1\114"),
        DFA.unpack(u"\1\115"),
        DFA.unpack(u"\1\116"),
        DFA.unpack(u"\1\117"),
        DFA.unpack(u"\1\120"),
        DFA.unpack(u"\1\121"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\123"),
        DFA.unpack(u"\1\124"),
        DFA.unpack(u"\1\125"),
        DFA.unpack(u"\1\126"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\17\23\1\127\12\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\140"),
        DFA.unpack(u"\1\141"),
        DFA.unpack(u"\1\142"),
        DFA.unpack(u"\1\143"),
        DFA.unpack(u"\1\144"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\146"),
        DFA.unpack(u"\1\147"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\151"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\152"),
        DFA.unpack(u"\1\153"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\156"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\160"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\161"),
        DFA.unpack(u"\1\162"),
        DFA.unpack(u"\1\163"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\164"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\165"),
        DFA.unpack(u"\1\166"),
        DFA.unpack(u"\1\167"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\172"),
        DFA.unpack(u"\1\173"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u"\1\23\13\uffff\12\23\7\uffff\32\23\4\uffff\1\23\1\uffff"
        u"\32\23"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]



    class DFA16(DFA):
        def specialStateTransition(self_, s, input):





            self = self_.recognizer

            _s = s

            if s == 0:
                LA16_18 = input.LA(1)

                s = -1
                if ((0 <= LA16_18 <= 65535)):
                    s = 58

                else:
                    s = 57

                if s >= 0:
                    return s

            nvae = NoViableAltException(self_.getDescription(), 16, _s, input)
            self_.error(nvae)
            raise nvae




def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from google.appengine._internal.antlr3.main import LexerMain
    main = LexerMain(ExpressionLexer)
    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)


if __name__ == '__main__':
    main(sys.argv)
